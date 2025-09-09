import wx
import logging
import nvda_notify
from datetime import datetime, timedelta
from qrz_lookup import QRZLookup

class QSOManager:
    def __init__(self, parent=None, settings_manager=None):
        self.parent = parent
        if settings_manager is None:
            raise ValueError("SettingsManager не передан в QSOManager")
        self.settings_manager = settings_manager
        self._init_qrz_lookup()
        self.controls = {}
        self.qso_list = []
        self.editing_index = None  # Индекс редактируемой записи

    def set_controls(self, controls):
        self.controls = controls

    def _init_qrz_lookup(self):
        qrz_username = self.settings_manager.settings.get("qrz_username", "")
        qrz_password = self.settings_manager.settings.get("qrz_password", "")
        use_qrz = self.settings_manager.settings.get("use_qrz_lookup", '1') == '1'
        self.qrz_lookup = QRZLookup(qrz_username, qrz_password) if use_qrz else None
        if use_qrz and self.qrz_lookup and not self.qrz_lookup.login():
            wx.MessageBox(
                "Ошибка авторизации на QRZ.ru. Проверьте логин и пароль для XML API.",
                "Ошибка",
                wx.OK | wx.ICON_ERROR
            )

    def reload_settings(self):
        self.settings_manager.load_settings()
        self._init_qrz_lookup()

    def add_qso(self, event):
        call_ctrl = self.controls.get('call')
        name_ctrl = self.controls.get('name')
        required_fields = {
            'Позывной': (call_ctrl, call_ctrl.GetValue().strip().upper() if call_ctrl else ""),
            'Имя': (name_ctrl, name_ctrl.GetValue().strip().title() if name_ctrl else "")
        }
        
        missing = []
        first_missing_ctrl = None
        for field_name, (ctrl, value) in required_fields.items():
            if not value:
                missing.append(field_name)
                if not first_missing_ctrl:
                    first_missing_ctrl = ctrl
        
        if missing:
            msg = "Заполните обязательные поля:\n- " + "\n- ".join(missing)
            print(msg)  # Отладочное сообщение
            self._show_error(msg)
            if first_missing_ctrl:
                first_missing_ctrl.SetFocus()
            return
        
        # Получение и обработка значения частоты
        freq_value = self.controls['freq'].GetValue().strip().replace(",", ".")  # Заменяем запятую на точку

        # Получение даты и времени из полей
        date_value = self.controls['date'].GetValue()
        time_value = self.controls['time'].GetValue()
        datetime_str = f"{date_value.FormatISODate()} {time_value.Format('%H:%M')}"  # Убираем секунды

        qso_data = {
            'call': required_fields['Позывной'][1],
            'name': required_fields['Имя'][1],
            'city': self.controls['city'].GetValue().strip().title(),
            'qth': self.controls['qth'].GetValue().strip().upper(),
            'band': self.controls['band'].GetStringSelection(),
            'mode': self.controls['mode'].GetStringSelection(),
            'freq': freq_value,  # Используем обработанное значение частоты
            'rst_received': self.controls['rst_received'].GetValue().strip(),
            'rst_sent': self.controls['rst_sent'].GetValue().strip(),
            'comment': self.controls['comment'].GetValue().strip().capitalize(),
            'datetime': datetime_str
        }
        
        if self.editing_index is not None:
            self.qso_list[self.editing_index] = qso_data  # Перезапись существующей записи
            self.editing_index = None
        else:
            self.qso_list.append(qso_data)
        
        self._update_journal()
        self._clear_fields()
        self.controls['call'].SetFocus()
        self._show_notification("QSO добавлен в журнал")

    def edit_qso(self, event):
        selected_index = self.journal_list.GetFirstSelected()
        if selected_index == -1:
            self._show_error("Выберите запись для редактирования")
            return
        
        # Переключаемся на вкладку "Добавить QSO" для удобства пользователя
        self.parent.notebook.SetSelection(0)
        
        qso_data = self.qso_list[selected_index]
        self.controls['call'].SetValue(qso_data['call'])
        self.controls['name'].SetValue(qso_data['name'])
        self.controls['city'].SetValue(qso_data['city'])
        self.controls['qth'].SetValue(qso_data['qth'])
        self.controls['band'].SetStringSelection(qso_data['band'])
        self.controls['mode'].SetStringSelection(qso_data['mode'])
        self.controls['freq'].SetValue(qso_data['freq'])
        self.controls['rst_received'].SetValue(qso_data['rst_received'])
        self.controls['rst_sent'].SetValue(qso_data['rst_sent'])
        self.controls['comment'].SetValue(qso_data['comment'])
        
        self.editing_index = selected_index  # Сохранение индекса редактируемой записи
        self.controls['call'].SetFocus()  # Установка фокуса на поле "Позывной"

    def del_qso(self, event):
        selected_index = self.journal_list.GetFirstSelected()
        if selected_index == -1:
            self._show_error("Выберите запись для удаления")
            return
        
        self.qso_list.pop(selected_index)
        self._update_journal()
        self.journal_list.SetFocus()  # Установка фокуса на список записей
        self._show_notification("QSO удален из журнала")

    def _update_journal(self):
        self.journal_list.DeleteAllItems()
        for idx, qso in enumerate(self.qso_list):
            self.journal_list.InsertItem(idx, qso['call'])      # Позывной
            self.journal_list.SetItem(idx, 1, qso['name'])      # Имя
            self.journal_list.SetItem(idx, 2, qso['city'])      # Город
            self.journal_list.SetItem(idx, 3, qso['qth'])       # QTH
            self.journal_list.SetItem(idx, 4, qso['band'])      # Диапазон
            self.journal_list.SetItem(idx, 5, qso['mode'])      # Режим
            self.journal_list.SetItem(idx, 6, qso['rst_received'])     # RST-принято
            self.journal_list.SetItem(idx, 7, qso['rst_sent'])     # RST-передано
            self.journal_list.SetItem(idx, 8, qso['freq'])     # Частота
            self.journal_list.SetItem(idx, 9, qso['comment'])  # Комментарий
            self.journal_list.SetItem(idx, 10, qso['datetime'])  # Дата/Время

    def _clear_fields(self):
        """
        Очищает все поля ввода, кроме RST-принято, RST-передано и Частоты.
        """
        controls_to_clear = [
            'call', 'name', 'city', 'qth', 'comment'
        ]
        for key in controls_to_clear:
            if key in self.controls:
                self.controls[key].SetValue("")

        # Устанавливаем дату и время с учетом часового пояса
        current_time = self._get_current_time_with_timezone()
        self.controls['date'].SetValue(wx.DateTime.FromDMY(current_time.day, current_time.month - 1, current_time.year))
        self.controls['time'].SetValue(wx.DateTime.FromHMS(current_time.hour, current_time.minute, 0))  # Убираем секунды

    def _show_error(self, message):
        dlg = wx.MessageDialog(self.parent, message, "Ошибка ввода", wx.OK|wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    def _show_notification(self, message):
        nvda_notify.nvda_notify(message)

    def _get_timezone_offset(self):
        """
        Получает часовой пояс из настроек и возвращает его в виде смещения в часах.
        """
        timezone = self.settings_manager.settings.get('timezone', 'UTC')
        if timezone == 'UTC':
            return 0  # Если выбран UTC, возвращаем смещение 0
        try:
            # Преобразуем custom_timezone в целое число
            return int(self.settings_manager.settings.get('custom_timezone', '0'))
        except ValueError:
            # Если значение некорректное, показываем ошибку и возвращаем 0
            self._show_error("Некорректное значение часового пояса. Используется UTC.")
            return 0

    def _get_current_time_with_timezone(self):
        """
        Возвращает текущее время с учетом настроек часового пояса.
        """
        timezone_offset = self._get_timezone_offset()
        current_time = datetime.utcnow() + timedelta(hours=timezone_offset)
        return current_time

    def _initialize_rst_fields(self):
        """
        Устанавливает значения по умолчанию для полей RST-принято и RST-передано.
        """
        if 'rst_received' in self.controls:
            self.controls['rst_received'].SetValue("59")
        if 'rst_sent' in self.controls:
            self.controls['rst_sent'].SetValue("59")
            

    def on_callsign_enter(self, event):
        """Обработчик события нажатия Enter в поле позывного."""
        if not self.qrz_lookup:
            nvda_notify.nvda_notify("Поиск по QRZ.ru отключён в настройках.")
            return
        callsign = self.controls['call'].GetValue().strip().upper()
        if not callsign:
            return
        try:
            result = self.qrz_lookup.lookup_call(callsign)
            if result:
                # Вставляем значения из QRZ.ru только если они не пустые
                self.controls['name'].SetValue(result.get("name", ""))
                self.controls['city'].SetValue(result.get("city", ""))
                nvda_notify.nvda_notify(f"Данные для {callsign} успешно загружены")
                print(f"QRZ: Данные для {callsign} успешно загружены: {result}")
                logging.info(f"QRZ: Данные для {callsign} успешно загружены: {result}")
            else:
                nvda_notify.nvda_notify(f"Позывной {callsign} не найден в базе QRZ.ru")
                print(f"QRZ: Позывной {callsign} не найден в базе QRZ.ru")
                logging.warning(f"QRZ: Позывной {callsign} не найден в базе QRZ.ru")
        except Exception as e:
            nvda_notify.nvda_notify(f"Ошибка поиска позывного: {e}")
            print(f"Ошибка поиска позывного: {e}")
            logging.error(f"Ошибка поиска позывного: {e}")
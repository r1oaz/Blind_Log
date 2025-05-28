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
        self.qso_list = []
        self.editing_index = None  # Индекс редактируемой записи

        # Установка значений по умолчанию для RST-принято и RST-передано
        self.text_ctrl_7 = None  # RST-принято
        self.text_ctrl_8 = None  # RST-передано

    def _init_qrz_lookup(self):
        qrz_username = self.settings_manager.settings.get("qrz_username", "")
        qrz_password = self.settings_manager.settings.get("qrz_password", "")
        use_qrz = self.settings_manager.settings.get("use_qrz_lookup", '1') == '1'
        self.qrz_lookup = QRZLookup(qrz_username, qrz_password) if use_qrz else None
        if use_qrz and self.qrz_lookup and not self.qrz_lookup.login():
            nvda_notify.nvda_notify("Ошибка авторизации на QRZ.ru")

    def reload_settings(self):
        self.settings_manager.load_settings()
        self._init_qrz_lookup()

    def add_qso(self, event):
        required_fields = {
            'Позывной': (self.text_ctrl_1, self.text_ctrl_1.GetValue().strip().upper()),  # Преобразование в заглавные буквы
            'Имя': (self.text_ctrl_2, self.text_ctrl_2.GetValue().strip().title())  # Преобразование первых букв в заглавные
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
        freq_value = self.text_ctrl_6.GetValue().strip().replace(",", ".")  # Заменяем запятую на точку

        # Получение даты и времени из полей
        date_value = self.date_ctrl.GetValue()
        time_value = self.time_ctrl.GetValue()
        datetime_str = f"{date_value.FormatISODate()} {time_value.Format('%H:%M')}"  # Убираем секунды

        qso_data = {
            'call': required_fields['Позывной'][1],
            'name': required_fields['Имя'][1],
            'city': self.text_ctrl_3.GetValue().strip().title(),  # Поле "Город" необязательно
            'qth': self.text_ctrl_4.GetValue().strip().upper(),  # Преобразование всех букв в заглавные
            'band': self.band_selector.GetStringSelection(),
            'mode': self.mode_selector.GetStringSelection(),  # Добавление режима
            'freq': freq_value,  # Используем обработанное значение частоты
            'rst_received': self.text_ctrl_7.GetValue().strip(),
            'rst_sent': self.text_ctrl_8.GetValue().strip(),
            'comment': self.comment_ctrl.GetValue().strip().capitalize(),  # Преобразование первой буквы в заглавную
            'datetime': datetime_str
        }
        
        if self.editing_index is not None:
            self.qso_list[self.editing_index] = qso_data  # Перезапись существующей записи
            self.editing_index = None
        else:
            self.qso_list.append(qso_data)
        
        self._update_journal()
        self._clear_fields()
        self.text_ctrl_1.SetFocus()
        self._show_notification("QSO добавлен в журнал")

    def edit_qso(self, event):
        selected_index = self.journal_list.GetFirstSelected()
        if selected_index == -1:
            self._show_error("Выберите запись для редактирования")
            return
        
        qso_data = self.qso_list[selected_index]
        self.text_ctrl_1.SetValue(qso_data['call'])
        self.text_ctrl_2.SetValue(qso_data['name'])
        self.text_ctrl_3.SetValue(qso_data['city'])
        self.text_ctrl_4.SetValue(qso_data['qth'])
        self.band_selector.SetStringSelection(qso_data['band'])
        self.mode_selector.SetStringSelection(qso_data['mode'])
        self.text_ctrl_6.SetValue(qso_data['freq'])
        self.text_ctrl_7.SetValue(qso_data['rst_received'])
        self.text_ctrl_8.SetValue(qso_data['rst_sent'])
        self.comment_ctrl.SetValue(qso_data['comment'])
        
        self.editing_index = selected_index  # Сохранение индекса редактируемой записи
        self.text_ctrl_1.SetFocus()  # Установка фокуса на поле "Позывной"

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
        controls = [
            self.text_ctrl_1, self.text_ctrl_2, self.text_ctrl_3,
            self.text_ctrl_4, self.comment_ctrl
        ]
        for ctrl in controls:
            ctrl.SetValue("")

        # Устанавливаем дату и время с учетом часового пояса
        current_time = self._get_current_time_with_timezone()
        self.date_ctrl.SetValue(wx.DateTime.FromDMY(current_time.day, current_time.month - 1, current_time.year))
        self.time_ctrl.SetValue(wx.DateTime.FromHMS(current_time.hour, current_time.minute, 0))  # Убираем секунды

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
        if self.text_ctrl_7:
            self.text_ctrl_7.SetValue("59")
        if self.text_ctrl_8:
            self.text_ctrl_8.SetValue("59")
            

    def on_callsign_enter(self, event):
        """Обработчик события нажатия Enter в поле позывного."""
        if not self.qrz_lookup:
            nvda_notify.nvda_notify("Поиск по QRZ.ru отключён в настройках.")
            return
        callsign = self.text_ctrl_1.GetValue().strip().upper()
        if not callsign:
            return
        try:
            result = self.qrz_lookup.lookup_call(callsign)
            if result:
                # Вставляем значения из QRZ.ru только если они не пустые
                self.text_ctrl_2.SetValue(result.get("name", ""))
                self.text_ctrl_3.SetValue(result.get("city", ""))
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
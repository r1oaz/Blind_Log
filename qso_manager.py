import wx
import logging
import nvda_notify
from datetime import datetime, timedelta
from qrz_lookup import QRZLookup
from constants import QSO_FIELD_NAMES

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
        use_qrz = self.settings_manager.settings.get("use_qrz_lookup", '0') == '1'
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

    def get_current_qso_from_form(self):
        """Собирает данные QSO из полей формы. Одно место связи с виджетами."""
        date_value = self.controls['date'].GetValue()
        time_value = self.controls['time'].GetValue()
        datetime_str = f"{date_value.FormatISODate()} {time_value.Format('%H:%M')}"
        freq_value = self.controls['freq'].GetValue().strip().replace(",", ".")
        return {
            'call': self.controls['call'].GetValue().strip().upper(),
            'name': self.controls['name'].GetValue().strip().title(),
            'city': self.controls['city'].GetValue().strip().title(),
            'qth': self.controls['qth'].GetValue().strip().upper(),
            'band': self.controls['band'].GetStringSelection(),
            'mode': self.controls['mode'].GetStringSelection(),
            'freq': freq_value,
            'rst_received': self.controls['rst_received'].GetValue().strip(),
            'rst_sent': self.controls['rst_sent'].GetValue().strip(),
            'comment': self.controls['comment'].GetValue().strip().capitalize(),
            'datetime': datetime_str,
        }

    def set_form_from_qso(self, qso):
        """Заполняет поля формы из словаря QSO. Одно место связи с виджетами."""
        self.controls['call'].SetValue(qso.get('call', ''))
        self.controls['name'].SetValue(qso.get('name', ''))
        self.controls['city'].SetValue(qso.get('city', ''))
        self.controls['qth'].SetValue(qso.get('qth', ''))
        self.controls['band'].SetStringSelection(qso.get('band', ''))
        self.controls['mode'].SetStringSelection(qso.get('mode', ''))
        self.controls['freq'].SetValue(qso.get('freq', ''))
        self.controls['rst_received'].SetValue(qso.get('rst_received', ''))
        self.controls['rst_sent'].SetValue(qso.get('rst_sent', ''))
        self.controls['comment'].SetValue(qso.get('comment', ''))

    def add_qso(self, event):
        qso_data = self.get_current_qso_from_form()
        call_val = qso_data['call']
        name_val = qso_data['name']
        if not call_val:
            self._show_error("Заполните обязательные поля:\n- Позывной")
            self.controls['call'].SetFocus()
            return
        if not name_val:
            self._show_error("Заполните обязательные поля:\n- Имя")
            self.controls['name'].SetFocus()
            return

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
        self.parent.notebook.SetSelection(0)
        self.set_form_from_qso(self.qso_list[selected_index])
        self.editing_index = selected_index
        self.controls['call'].SetFocus()

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
            self.journal_list.InsertItem(idx, qso.get(QSO_FIELD_NAMES[0], ""))
            for col_idx in range(1, len(QSO_FIELD_NAMES)):
                self.journal_list.SetItem(idx, col_idx, qso.get(QSO_FIELD_NAMES[col_idx], ""))

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
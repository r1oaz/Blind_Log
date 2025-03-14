import wx
from datetime import datetime
import pytz
from tzlocal import get_localzone

class QSOManager:
    def __init__(self):
        self.qso_list = []
        self.editing_index = None  # Индекс редактируемой записи

    def add_qso(self, event):
        required_fields = {
            'Позывной': (self.text_ctrl_1, self.text_ctrl_1.GetValue().strip().upper()),  # Преобразование в заглавные буквы
            'Имя': (self.text_ctrl_2, self.text_ctrl_2.GetValue().strip().title()),  # Преобразование первых букв в заглавные
            'Город': (self.text_ctrl_3, self.text_ctrl_3.GetValue().strip().title()),  # Преобразование первых букв в заглавные
            'RST-принято': (self.text_ctrl_7, self.text_ctrl_7.GetValue().strip()),
            'RST-передано': (self.text_ctrl_8, self.text_ctrl_8.GetValue().strip()),
            'Диапазон': (self.band_selector, self.band_selector.GetStringSelection()),
            'Режим': (self.mode_selector, self.mode_selector.GetStringSelection())  # Добавление режима
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
            self._show_error(msg)
            if first_missing_ctrl:
                if isinstance(first_missing_ctrl, wx.Choice):
                    first_missing_ctrl.SetFocus()
                else:
                    first_missing_ctrl.SetFocus()
            return
        
        # Получение текущего времени в UTC
        if self.editing_index is None:
            local_tz = get_localzone()  # Автоматическое определение часового пояса
            local_time = datetime.now(local_tz)
            utc_time = local_time.astimezone(pytz.utc)
            datetime_str = utc_time.strftime("%Y-%m-%d %H:%M")
        else:
            datetime_str = self.qso_list[self.editing_index]['datetime']
        
        qso_data = {
            'call': required_fields['Позывной'][1],
            'name': required_fields['Имя'][1],
            'city': required_fields['Город'][1],
            'qth': self.text_ctrl_4.GetValue().strip().upper(),  # Преобразование всех букв в заглавные
            'band': required_fields['Диапазон'][1],
            'mode': required_fields['Режим'][1],  # Добавление режима
            'freq': self.text_ctrl_6.GetValue().strip(),
            'rst_received': required_fields['RST-принято'][1],
            'rst_sent': required_fields['RST-передано'][1],
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
        controls = [
            self.text_ctrl_1, self.text_ctrl_2, self.text_ctrl_3,
            self.text_ctrl_4, self.text_ctrl_6, self.text_ctrl_7,
            self.text_ctrl_8, self.comment_ctrl
        ]
        for ctrl in controls:
            ctrl.SetValue("")

    def _show_error(self, message):
        dlg = wx.MessageDialog(self, message, "Ошибка ввода", wx.OK|wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    def _show_notification(self, message):
        wx.adv.NotificationMessage("Blind_Log", message).Show()
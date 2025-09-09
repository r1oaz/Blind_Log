import wx
import configparser
import os
import logging

class SettingsManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = 'settings.ini'
        self.default_settings = {
            'call': 'R1OAZ',
            'operator_name': 'Иван',
            'my_qth': 'KP50DB',
            'my_city': 'Архангельск',
            'my_rig': 'baofeng',
            'my_lat': '',
            'my_lon': '',
            'timezone': 'UTC',
            'custom_timezone': '+0',
            'qrz_username': '',
            'qrz_password': '',
            'use_qrz_lookup': '0',  # По умолчанию все флажки сняты
            'check_updates_on_start': '0',
            'log_enabled': '0',
        }
        self.settings = {}
        self.load_settings()
        self.apply_logging()

    def load_settings(self):
        if not os.path.exists(self.config_file):
            self.create_default_settings()
            self.show_info_message(
                "Файл настроек был создан со значениями по умолчанию.\n"
                "Если вы хотите использовать поиск позывных на QRZ.ru, отметьте соответствующий флажок и заполните логин и пароль."
            )
        try:
            with open(self.config_file, 'r', encoding='utf-8') as configfile:
                self.config.read_file(configfile)
        except UnicodeDecodeError:
            with open(self.config_file, 'r', encoding='cp1251') as configfile:
                self.config.read_file(configfile)
        if 'Settings' not in self.config:
            self.create_default_settings()
        self.settings = {key: self.config.get('Settings', key, fallback=value)
                         for key, value in self.default_settings.items()}
        self.apply_logging()

    def create_default_settings(self):
        self.config['Settings'] = self.default_settings
        with open(self.config_file, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def save_settings(self, settings):
        if not self.config.has_section('Settings'):
            self.config.add_section('Settings')
        for key, value in settings.items():
            self.config.set('Settings', key, value)
        with open(self.config_file, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)
        self.settings = settings.copy()
        self.apply_logging()

    def apply_logging(self):
        # Используем force=True (для Python 3.8+), чтобы перенастроить logging.
        # Это позволяет централизованно управлять логированием из этого класса.
        if self.settings.get('log_enabled', '0') == '1':
            logging.basicConfig(filename='blind_log.log', level=logging.INFO,
                                format='%(asctime)s - %(levelname)s - %(message)s',
                                force=True, encoding='utf-8')
        else:
            # Отключаем логирование, удаляя все обработчики из корневого логгера
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

    def show_info_message(self, message):
        dlg = wx.MessageDialog(None, message, "Информация", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def show_settings(self, parent=None):
        dialog = SettingsDialog(parent=parent, title="Настройки", settings_manager=self)
        if dialog.ShowModal() == wx.ID_OK:
            self.load_settings()
        dialog.Destroy()

class SettingsDialog(wx.Dialog):
    def __init__(self, *args, settings_manager=None, **kwds):
        super(SettingsDialog, self).__init__(*args, **kwds)
        self.settings_manager = settings_manager or SettingsManager()
        self.settings = self.settings_manager.settings
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.call_label = wx.StaticText(self, label="Позывной оператора:")
        self.call_text = wx.TextCtrl(self)
        self.operator_name_label = wx.StaticText(self, label="Имя оператора:")
        self.operator_name_text = wx.TextCtrl(self)
        self.my_qth_label = wx.StaticText(self, label="Мой QTH:")
        self.my_qth_text = wx.TextCtrl(self)
        self.my_city_label = wx.StaticText(self, label="Мой город:")
        self.my_city_text = wx.TextCtrl(self)
        self.my_rig_label = wx.StaticText(self, label="Моё оборудование:")
        self.my_rig_text = wx.TextCtrl(self)
        self.my_lat_label = wx.StaticText(self, label="Широта:")
        self.my_lat_text = wx.TextCtrl(self)
        self.my_lon_label = wx.StaticText(self, label="Долгота:")
        self.my_lon_text = wx.TextCtrl(self)
        self.use_qrz_checkbox = wx.CheckBox(self, label="Использовать QRZ.ru для подстановки имени и города")
        self.use_qrz_checkbox.Bind(wx.EVT_CHECKBOX, self.on_use_qrz_toggle)
        main_sizer.Add(self.use_qrz_checkbox, 0, wx.ALL, 5)
        self.qrz_username_label = wx.StaticText(self, label="Логин QRZ.ru:")
        self.qrz_username_text = wx.TextCtrl(self)
        self.qrz_password_label = wx.StaticText(self, label="Пароль QRZ.ru:")
        self.qrz_password_text = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        # Группа для логина/пароля QRZ.ru
        self.qrz_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.qrz_sizer.Add(self.qrz_username_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.qrz_sizer.Add(self.qrz_username_text, 1, wx.EXPAND | wx.RIGHT, 10)
        self.qrz_sizer.Add(self.qrz_password_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.qrz_sizer.Add(self.qrz_password_text, 1, wx.EXPAND)
        main_sizer.Add(self.qrz_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.timezone_label = wx.StaticText(self, label="Часовой пояс:")
        self.timezone_choice = wx.RadioBox(
            self, label="", choices=["UTC", "Задать свой часовой пояс"], majorDimension=1, style=wx.RA_SPECIFY_ROWS
        )
        self.custom_timezone_label = wx.StaticText(self, label="Свой часовой пояс:")
        self.custom_timezone_text = wx.TextCtrl(self)
        self.log_enabled_checkbox = wx.CheckBox(self, label="Вести лог (blind_log.log)")
        main_sizer.Add(self.log_enabled_checkbox, 0, wx.ALL, 5)
        self.check_updates_checkbox = wx.CheckBox(self, label="Проверять обновления при запуске программы")
        main_sizer.Add(self.check_updates_checkbox, 0, wx.ALL, 5)
        fields = [
            (self.call_label, self.call_text),
            (self.operator_name_label, self.operator_name_text),
            (self.my_qth_label, self.my_qth_text),
            (self.my_city_label, self.my_city_text),
            (self.my_rig_label, self.my_rig_text),
            (self.my_lat_label, self.my_lat_text),
            (self.my_lon_label, self.my_lon_text),
            (self.timezone_label, self.timezone_choice),
            (self.custom_timezone_label, self.custom_timezone_text)
        ]
        for label, ctrl in fields:
            row_sizer = wx.BoxSizer(wx.HORIZONTAL)
            row_sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
            row_sizer.Add(ctrl, 1, wx.EXPAND)
            main_sizer.Add(row_sizer, 0, wx.EXPAND | wx.ALL, 5)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.save_btn = wx.Button(self, label="Сохранить")
        self.cancel_btn = wx.Button(self, label="Отмена")
        btn_sizer.Add(self.save_btn, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.cancel_btn, 0)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        self.SetSizer(main_sizer)
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.timezone_choice.Bind(wx.EVT_RADIOBOX, self.on_timezone_change)

    def on_use_qrz_toggle(self, event):
        enabled = self.use_qrz_checkbox.GetValue()
        self.qrz_username_label.Enable(enabled)
        self.qrz_username_text.Enable(enabled)
        self.qrz_password_label.Enable(enabled)
        self.qrz_password_text.Enable(enabled)

    def load_settings(self):
        self.call_text.SetValue(self.settings['call'])
        self.operator_name_text.SetValue(self.settings['operator_name'])
        self.my_qth_text.SetValue(self.settings['my_qth'])
        self.my_city_text.SetValue(self.settings['my_city'])
        self.my_rig_text.SetValue(self.settings['my_rig'])
        self.my_lat_text.SetValue(self.settings['my_lat'])
        self.my_lon_text.SetValue(self.settings['my_lon'])
        self.qrz_username_text.SetValue(self.settings['qrz_username'])
        self.qrz_password_text.SetValue(self.settings['qrz_password'])
        self.timezone_choice.SetStringSelection(self.settings['timezone'])
        self.custom_timezone_text.SetValue(self.settings['custom_timezone'])
        self.custom_timezone_text.Enable(self.settings['timezone'] == "Задать свой часовой пояс")
        self.use_qrz_checkbox.SetValue(self.settings.get('use_qrz_lookup', '0') == '1')
        self.log_enabled_checkbox.SetValue(self.settings.get('log_enabled', '0') == '1')
        self.check_updates_checkbox.SetValue(self.settings.get('check_updates_on_start', '0') == '1')
        self.on_use_qrz_toggle(None)

    def on_save(self, event):
        settings = {
            'call': self.call_text.GetValue(),
            'operator_name': self.operator_name_text.GetValue(),
            'my_qth': self.my_qth_text.GetValue(),
            'my_city': self.my_city_text.GetValue(),
            'my_rig': self.my_rig_text.GetValue(),
            'my_lat': self.my_lat_text.GetValue(),
            'my_lon': self.my_lon_text.GetValue(),
            'qrz_username': self.qrz_username_text.GetValue(),
            'qrz_password': self.qrz_password_text.GetValue(),
            'timezone': self.timezone_choice.GetStringSelection(),
            'custom_timezone': self.custom_timezone_text.GetValue(),
            'use_qrz_lookup': '1' if self.use_qrz_checkbox.GetValue() else '0',
            'log_enabled': '1' if self.log_enabled_checkbox.GetValue() else '0',
            'check_updates_on_start': '1' if self.check_updates_checkbox.GetValue() else '0',
        }
        self.settings_manager.save_settings(settings)
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_timezone_change(self, event):
        self.custom_timezone_text.Enable(self.timezone_choice.GetSelection() == 1)
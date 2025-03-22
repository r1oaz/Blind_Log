import wx
import configparser
import os

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
            'custom_timezone': '+0'
        }
        self.settings = {}  # Инициализация пустого словаря настроек
        self.load_settings()

    def load_settings(self):
        """
        Загружает настройки из файла или создает файл с настройками по умолчанию.
        """
        if not os.path.exists(self.config_file):
            self.create_default_settings()
            self.show_info_message("Файл настроек был создан. На данный момент поля заполнены значениями по умолчанию.")
        try:
            with open(self.config_file, 'r', encoding='utf-8') as configfile:
                self.config.read_file(configfile)
        except UnicodeDecodeError:
            with open(self.config_file, 'r', encoding='cp1251') as configfile:
                self.config.read_file(configfile)

        # Загружаем настройки из секции [Settings]
        if 'Settings' not in self.config:
            self.create_default_settings()
        self.settings = {key: self.config.get('Settings', key, fallback=value)
                         for key, value in self.default_settings.items()}

    def create_default_settings(self):
        """
        Создает файл настроек с настройками по умолчанию.
        """
        self.config['Settings'] = self.default_settings
        with open(self.config_file, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def save_settings(self, settings):
        """
        Сохраняет настройки в файл.
        """
        if not self.config.has_section('Settings'):
            self.config.add_section('Settings')
        for key, value in settings.items():
            self.config.set('Settings', key, value)
        with open(self.config_file, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def show_info_message(self, message):
        """
        Показывает информационное сообщение.
        """
        dlg = wx.MessageDialog(None, message, "Информация", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def show_settings(self, parent=None):
        """
        Открывает диалог настроек.
        """
        dialog = SettingsDialog(parent=parent, title="Настройки")
        dialog.ShowModal()
        dialog.Destroy()


class SettingsDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        super(SettingsDialog, self).__init__(*args, **kwds)
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.settings

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Поля ввода
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

        # Радиокнопки для часового пояса
        self.timezone_label = wx.StaticText(self, label="Часовой пояс:")
        self.timezone_choice = wx.RadioBox(
            self, label="", choices=["UTC", "Задать свой часовой пояс"], majorDimension=1, style=wx.RA_SPECIFY_ROWS
        )
        self.custom_timezone_label = wx.StaticText(self, label="Свой часовой пояс:")
        self.custom_timezone_text = wx.TextCtrl(self)

        # Добавление полей в интерфейс
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

        # Кнопки
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.save_btn = wx.Button(self, label="Сохранить")
        self.cancel_btn = wx.Button(self, label="Отмена")
        btn_sizer.Add(self.save_btn, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.cancel_btn, 0)

        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(main_sizer)

        # Привязка событий
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.timezone_choice.Bind(wx.EVT_RADIOBOX, self.on_timezone_change)

    def load_settings(self):
        self.call_text.SetValue(self.settings['call'])
        self.operator_name_text.SetValue(self.settings['operator_name'])
        self.my_qth_text.SetValue(self.settings['my_qth'])
        self.my_city_text.SetValue(self.settings['my_city'])
        self.my_rig_text.SetValue(self.settings['my_rig'])
        self.my_lat_text.SetValue(self.settings['my_lat'])
        self.my_lon_text.SetValue(self.settings['my_lon'])
        self.timezone_choice.SetStringSelection(self.settings['timezone'])
        self.custom_timezone_text.SetValue(self.settings['custom_timezone'])
        self.custom_timezone_text.Enable(self.settings['timezone'] == "Задать свой часовой пояс")

    def on_save(self, event):
        settings = {
            'call': self.call_text.GetValue(),
            'operator_name': self.operator_name_text.GetValue(),
            'my_qth': self.my_qth_text.GetValue(),
            'my_city': self.my_city_text.GetValue(),
            'my_rig': self.my_rig_text.GetValue(),
            'my_lat': self.my_lat_text.GetValue(),
            'my_lon': self.my_lon_text.GetValue(),
            'timezone': self.timezone_choice.GetStringSelection(),
            'custom_timezone': self.custom_timezone_text.GetValue()
        }
        self.settings_manager.save_settings(settings)
        self.Close()

    def on_cancel(self, event):
        self.Close()

    def on_timezone_change(self, event):
        self.custom_timezone_text.Enable(self.timezone_choice.GetSelection() == 1)
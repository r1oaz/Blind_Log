import wx
import configparser
import os

class SettingsManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = 'settings.ini'
        self.default_settings = {
            'call': 'R1OAZ'
        }
        self.load_settings()

    def show_settings(self):
        self.settings_dialog = SettingsDialog(None, title="Настройки")
        self.settings_dialog.ShowModal()
        self.settings_dialog.Destroy()

    def load_settings(self):
        if not os.path.exists(self.config_file):
            self.create_default_settings()
            self.show_info_message("Файл настроек был создан. На данный момент поля заполнены, вы должны изменить значения на свои.")
        try:
            with open(self.config_file, 'r', encoding='utf-8') as configfile:
                self.config.read_file(configfile)
        except UnicodeDecodeError:
            with open(self.config_file, 'r', encoding='cp1251') as configfile:
                self.config.read_file(configfile)
        self.settings = {
            'call': self.config.get('Operator', 'call', fallback=self.default_settings['call'])
        }

    def create_default_settings(self):
        self.config['Operator'] = self.default_settings
        with open(self.config_file, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def save_settings(self, settings):
        if not self.config.has_section('Operator'):
            self.config.add_section('Operator')
        self.config.set('Operator', 'Call', settings['call'])
        with open(self.config_file, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def show_info_message(self, message):
        dlg = wx.MessageDialog(None, message, "Информация", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

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

        # Добавление полей в интерфейс
        row_sizer = wx.BoxSizer(wx.HORIZONTAL)
        row_sizer.Add(self.call_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        row_sizer.Add(self.call_text, 1, wx.EXPAND)
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

    def load_settings(self):
        self.call_text.SetValue(self.settings['call'])
        self.call_text.SetFocus()

    def on_save(self, event):
        settings = {
            'call': self.call_text.GetValue()
        }
        self.settings_manager.save_settings(settings)
        self.Close()

    def on_cancel(self, event):
        self.Close()
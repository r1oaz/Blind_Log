"""
Main module for the Blind_log application.
"""

import wx
from gui import Blind_log
from settings import SettingsManager

class MyApp(wx.App):
    """
    Application class for Blind_log.
    """
    def OnInit(self):
        """
        Initialize the application.
        """
        try:
            self.settings_manager = SettingsManager()
            self.frame = Blind_log(None, settings_manager=self.settings_manager)  # Передаем settings_manager
            self.frame.Show()
            return True
        except Exception as e:
            wx.MessageBox(f"Ошибка при запуске приложения: {e}", "Ошибка", wx.OK | wx.ICON_ERROR)
            return False

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
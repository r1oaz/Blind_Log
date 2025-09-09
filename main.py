"""
Основной модуль для приложения Blind_log.
"""

import wx
import logging
from gui import Blind_log
from settings import SettingsManager
from updater import check_update

class MyApp(wx.App):
    """
    Класс приложения для Blind_log.
    """
    def OnInit(self):
        """
        Инициализация приложения.
        """
        try:
            self.settings_manager = SettingsManager()
            # Настройка логирования теперь полностью управляется SettingsManager
            # Проверка обновлений при запуске, если включено в настройках
            if self.settings_manager.settings.get('check_updates_on_start', '1') == '1':
                check_update(None, silent_if_latest=True)  # Не показывать сообщение при автозапуске
            self.frame = Blind_log(None, settings_manager=self.settings_manager)  # Передаем settings_manager
            self.frame.Show()
            return True
        except Exception as e:
            import nvda_notify
            nvda_notify.nvda_notify(f"Ошибка при запуске приложения: {e}")
            print(f"Ошибка при запуске приложения: {e}")
            logging.error(f"Ошибка при запуске приложения: {e}")
            wx.MessageBox(f"Ошибка при запуске приложения: {e}", "Ошибка", wx.OK | wx.ICON_ERROR)
            return False

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()

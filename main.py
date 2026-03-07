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
            if self.settings_manager.get_option('check_updates_on_start') == '1':
                check_update(None, silent_if_latest=True)  # Не показывать сообщение при автозапуске
            self.frame = Blind_log(None, settings_manager=self.settings_manager)  # Передаем settings_manager
            # автосохранение: предлагаем восстановить данные, если настройка включена
            if self.settings_manager.get_option('auto_temp', '0') == '1':
                temp_data = self.frame.qso_manager.load_temp()
                if temp_data and len(temp_data) > 0:
                    dlg = wx.MessageDialog(
                        self.frame,
                        f"Найдены несохранённые данные ({len(temp_data)} QSO). Восстановить?",
                        "Восстановление сессии",
                        wx.YES_NO | wx.ICON_QUESTION
                    )
                    if dlg.ShowModal() == wx.ID_YES:
                        self.frame.qso_manager.qso_list = temp_data
                        self.frame.qso_manager._update_journal()
                        # после восстановления больше не предлагать
                        try:
                            self.frame.qso_manager.clear_temp()
                        except Exception:
                            pass
                    dlg.Destroy()
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
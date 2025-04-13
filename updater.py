import os
import shutil
import tempfile
import zipfile
import requests
import wx
import threading
import re
import sys
import subprocess

EXE_NAME = "Blind_log.exe"
ZIP_URL = "https://github.com/r1oaz/Blind_Log/releases/latest/download/Blind_log.zip"
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/r1oaz/Blind_Log/main/version.txt"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

VERSION_FILE = resource_path("version.txt")

class UpdaterFrame(wx.Frame):
    def __init__(self, parent=None):
        super().__init__(parent, title="Обновление", size=(400, 150))
        self.panel = wx.Panel(self)

        self.info = wx.StaticText(self.panel, label="Проверка обновлений...")
        self.progress = wx.Gauge(self.panel, range=100)
        self.progress.Hide()
        self.status_text = wx.StaticText(self.panel, label="")

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.info, 0, wx.ALL | wx.EXPAND, 10)
        self.sizer.Add(self.progress, 0, wx.ALL | wx.EXPAND, 10)
        self.sizer.Add(self.status_text, 0, wx.ALL | wx.EXPAND, 10)

        self.panel.SetSizerAndFit(self.sizer)
        self.Center()
        self.Show()

        threading.Thread(target=self.check_versions, daemon=True).start()

    def get_local_version(self):
        if not os.path.exists(VERSION_FILE):
            return None
        try:
            with open(VERSION_FILE, "r") as f:
                content = f.read()
                match = re.search(r"StringStruct\('ProductVersion', '([\d\.]+)'\)", content)
                return match.group(1) if match else None
        except:
            return None

    def get_remote_version(self):
        try:
            response = requests.get(REMOTE_VERSION_URL, timeout=10)
            response.raise_for_status()
            match = re.search(r"StringStruct\('ProductVersion', '([\d\.]+)'\)", response.text)
            return match.group(1) if match else None
        except:
            return None

    def check_versions(self):
        local = self.get_local_version()
        remote = self.get_remote_version()

        wx.CallAfter(self.info.SetLabel, f"Текущая версия: {local or 'неизвестно'}\nДоступна версия: {remote or 'неизвестно'}")

        if not local or not remote:
            wx.CallAfter(self.finish_dialog, "Не удалось получить версии. Проверьте подключение к интернету.")
        elif local == remote:
            wx.CallAfter(self.finish_dialog, "У вас актуальная версия.")
        else:
            wx.CallAfter(self.ask_update, remote)

    def ask_update(self, remote):
        dlg = wx.MessageDialog(
            self,
            f"Доступна новая версия {remote}.\n\nЕсли у вас есть незавершённый журнал, нажмите 'Нет', сохраните его и затем повторите обновление.\n\nОбновить сейчас?",
            "Обновление",
            wx.YES_NO | wx.ICON_QUESTION
        )
        if dlg.ShowModal() == wx.ID_YES:
            self.progress.Show()
            self.status_text.SetLabel("Загрузка...")
            self.Layout()
            threading.Thread(target=self.download_archive, daemon=True).start()
        else:
            self.finish_dialog("Обновление отменено.")
        dlg.Destroy()

    def download_archive(self):
        zip_path = os.path.join(tempfile.gettempdir(), "Blind_log.zip")
        try:
            response = requests.get(ZIP_URL, stream=True)
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            percent = int(downloaded * 100 / total)
                            wx.CallAfter(self.progress.SetValue, percent)
                            wx.CallAfter(self.status_text.SetLabel, f"Загружено: {percent}%")

            wx.CallAfter(self.confirm_close_and_update, zip_path)
        except Exception as e:
            wx.CallAfter(self.finish_dialog, f"Ошибка загрузки: {e}")

    def confirm_close_and_update(self, zip_path):
        dlg = wx.MessageDialog(
            self,
            "Архив обновления загружен.\n\nСейчас будет закрыта основная программа для установки новой версии.\nПродолжить?",
            "Установка обновления",
            wx.YES_NO | wx.ICON_WARNING
        )
        if dlg.ShowModal() == wx.ID_YES:
            self.CloseMainApp()
            threading.Thread(target=self.replace_files_and_restart, args=(zip_path,), daemon=True).start()
        else:
            self.finish_dialog("Установка отменена.")
        dlg.Destroy()

    def CloseMainApp(self):
        for window in wx.GetTopLevelWindows():
            if window is not self:
                window.Close()

    def replace_files_and_restart(self, zip_path):
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(tmpdir)

                for item in os.listdir(tmpdir):
                    s = os.path.join(tmpdir, item)
                    d = os.path.join(os.getcwd(), item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)

            os.remove(zip_path)
            wx.CallAfter(self.ask_restart)
        except Exception as e:
            wx.CallAfter(self.finish_dialog, f"Ошибка при замене файлов:\n{e}")

    def ask_restart(self):
        dlg = wx.MessageDialog(self, "Обновление успешно установлено. Запустить программу снова?", "Готово", wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            subprocess.Popen([EXE_NAME], cwd=os.getcwd(), shell=True)
        dlg.Destroy()
        self.Destroy()

    def finish_dialog(self, msg):
        dlg = wx.MessageDialog(self, msg, "Обновление", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        self.Destroy()

if __name__ == "__main__":
    app = wx.App(False)
    UpdaterFrame()
    app.MainLoop()

import os
import shutil
import tempfile
import zipfile
import requests
import wx
import threading
import re
import sys  # Для работы с sys._MEIPASS

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
    def __init__(self, callback_on_done):
        super().__init__(None, title="Проверка обновлений", size=(400, 200))
        self.panel = wx.Panel(self)
        self.callback_on_done = callback_on_done
        self.update_cancelled = False
        self.update_successful = False

        self.info = wx.StaticText(self.panel, label="Проверка обновлений...")
        self.progress = wx.Gauge(self.panel, range=100, style=wx.GA_HORIZONTAL)
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
            wx.CallAfter(self.info.SetLabel, "Файл version.txt не найден.")
            return None
        try:
            with open(VERSION_FILE, "r") as f:
                content = f.read()
                match = re.search(r"StringStruct\('ProductVersion', '([\d\.]+)'\)", content)
                if match:
                    return match.group(1)
        except Exception as e:
            wx.CallAfter(self.info.SetLabel, f"Ошибка при чтении локальной версии: {e}")
        return None

    def get_remote_version(self):
        try:
            response = requests.get(REMOTE_VERSION_URL, timeout=10)
            response.raise_for_status()
            match = re.search(r"StringStruct\('ProductVersion', '([\d\.]+)'\)", response.text)
            if match:
                return match.group(1)
        except Exception as e:
            wx.CallAfter(self.info.SetLabel, f"Ошибка получения версии с GitHub: {e}")
        return None

    def check_versions(self):
        local = self.get_local_version()
        remote = self.get_remote_version()

        if not local and not remote:
            wx.CallAfter(self.finish, "Не удалось получить информацию о версиях.")
            return

        wx.CallAfter(self.info.SetLabel, f"Текущая версия: {local or 'неизвестно'}\nДоступна версия: {remote or 'неизвестно'}")

        if not local or not remote:
            wx.CallAfter(self.finish, "Ошибка при проверке версий.")
        elif local == remote:
            wx.CallAfter(self.finish, "У вас актуальная версия.")
        else:
            wx.CallAfter(self.ask_update, remote)

    def ask_update(self, remote):
        dlg = wx.MessageDialog(self, f"Найдена новая версия {remote}.\nОбновить сейчас?", "Обновление", wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_YES:
            self.progress.Show()
            self.status_text.SetLabel("Идёт обновление, пожалуйста подождите...")
            self.Layout()
            threading.Thread(target=self.download_and_install, daemon=True).start()
        else:
            self.update_cancelled = True
            self.Destroy()

    def download_and_install(self):
        zip_path = os.path.join(tempfile.gettempdir(), "Blind_log.zip")
        try:
            success = self.download_zip(ZIP_URL, zip_path)
            if success and self.extract_and_replace(zip_path):
                os.remove(zip_path)
                wx.CallAfter(self.finish, "Обновление завершено. Перезапустите программу вручную.\nНе забудьте сохранить лог в ADIF файл.")
            else:
                raise Exception("Ошибка при загрузке или установке.")
        except Exception as e:
            wx.CallAfter(self.finish, f"Ошибка при установке: {e}")
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)

    def download_zip(self, url, dest_path):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            percent = int(downloaded * 100 / total)
                            wx.CallAfter(self.progress.SetValue, percent)
                            wx.CallAfter(self.status_text.SetLabel,
                                         f"Загружено: {percent}% ({downloaded // 1024} KB из {total // 1024} KB)")
            return True
        except Exception as e:
            wx.CallAfter(self.info.SetLabel, f"Ошибка загрузки: {e}")
            return False

    def extract_and_replace(self, zip_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(tmpdir)
                for item in os.listdir(tmpdir):
                    s = os.path.join(tmpdir, item)
                    d = os.path.join(os.getcwd(), item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
                return True
            except Exception as e:
                wx.CallAfter(self.info.SetLabel, f"Ошибка при замене файлов: {e}")
                return False

    def finish(self, msg):
        if self.update_cancelled:
            self.Destroy()
            return

        self.info.SetLabel(msg)
        self.progress.Hide()
        self.status_text.SetLabel("")
        self.Layout()

        if "Обновление завершено" in msg:
            self.update_successful = True
            # Добавляем кнопку "Закрыть"
            close_btn = wx.Button(self.panel, label="Закрыть")
            close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Destroy())
            self.sizer.Add(close_btn, 0, wx.ALL | wx.ALIGN_CENTER, 10)
            self.panel.Layout()
        else:
            wx.CallLater(3000, self.close_and_continue)

    def close_and_continue(self):
        if self.callback_on_done and not self.update_cancelled and not self.update_successful:
            self.callback_on_done()
        self.Destroy()

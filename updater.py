import os
import sys
import zipfile
import requests
import subprocess
import shutil
import logging
import wx
import re

# Логгирование
log_path = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "updater.log")
logging.basicConfig(filename=log_path, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу, учитывая запуск из PyInstaller onefile."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_app_path():
    """Возвращает путь к текущему приложению."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def parse_version_txt(path):
    """Читает текущую версию из файла version.txt."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r"StringStruct\('FileVersion', '(.+?)'\)", content)
            if match:
                return match.group(1)
    except FileNotFoundError:
        logging.error("Файл version.txt не найден.")
    except Exception as e:
        logging.error(f"Ошибка при чтении version.txt: {e}")
    return None

def version_tuple(v):
    """Преобразует строку версии в кортеж чисел."""
    return tuple(int(x) for x in v.strip().replace("v", "").split("."))

def check_update(parent_frame, silent_if_latest=False):
    """Проверяет наличие обновлений и запускает процесс обновления."""
    version_path = resource_path("version.txt")
    current_version = parse_version_txt(version_path)

    if not current_version:
        wx.CallAfter(wx.MessageBox, "Не удалось определить текущую версию.", "Ошибка", wx.ICON_ERROR)
        return

    try:
        response = requests.get("https://api.github.com/repos/r1oaz/blind_log/releases/latest", timeout=15)
        response.raise_for_status()
        data = response.json()
        latest_version = data["tag_name"]
        download_url = None
        changelog = data.get("body", "")

        for asset in data["assets"]:
            if asset["name"].endswith(".zip"):
                download_url = asset["browser_download_url"]
                break

        if not download_url:
            wx.CallAfter(wx.MessageBox, "Не удалось найти архив обновления.", "Ошибка", wx.ICON_ERROR)
            return

    except requests.RequestException as e:
        wx.CallAfter(wx.MessageBox, f"Ошибка при получении обновления:\n{e}", "Ошибка", wx.ICON_ERROR)
        return

    if version_tuple(latest_version) <= version_tuple(current_version):
        if not silent_if_latest:
            wx.CallAfter(wx.MessageBox, f"У вас уже установлена последняя версия: {current_version}", "Обновление", wx.ICON_INFORMATION)
        return

    # Показываем changelog пользователю
    dlg = wx.Dialog(parent_frame, title=f"Доступна новая версия {latest_version}", size=(600, 500))
    vbox = wx.BoxSizer(wx.VERTICAL)
    info = wx.StaticText(dlg, label="Что нового в этой версии:")
    vbox.Add(info, 0, wx.ALL, 10)
    text_ctrl = wx.TextCtrl(dlg, value=changelog, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
    vbox.Add(text_ctrl, 1, wx.EXPAND|wx.ALL, 10)
    btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
    btn_update = wx.Button(dlg, label="Обновить")
    btn_cancel = wx.Button(dlg, label="Отмена")
    btn_sizer.Add(btn_update, 0, wx.RIGHT, 10)
    btn_sizer.Add(btn_cancel, 0)
    vbox.Add(btn_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 10)
    dlg.SetSizer(vbox)

    result = [None]
    def on_update(evt):
        result[0] = True
        dlg.Close()
    def on_cancel(evt):
        result[0] = False
        dlg.Close()
    btn_update.Bind(wx.EVT_BUTTON, on_update)
    btn_cancel.Bind(wx.EVT_BUTTON, on_cancel)
    dlg.ShowModal()
    dlg.Destroy()
    if not result[0]:
        return

    # Загружаем и обновляем
    download_and_update(download_url, parent_frame)

def download_and_update(download_url, parent_frame):
    """Загружает архив обновления и выполняет обновление."""
    temp_dir = os.path.join(get_app_path(), "temp")
    zip_path = os.path.join(temp_dir, "update.zip")

    try:
        # Создаём временную папку
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Создаём диалог прогресса
        progress_dialog = wx.ProgressDialog(
            "Загрузка обновления",
            "Подготовка к загрузке...",
            maximum=100,
            parent=parent_frame,
            style=wx.PD_AUTO_HIDE | wx.PD_APP_MODAL | wx.PD_CAN_ABORT
        )

        # Загружаем архив
        logging.info(f"Скачиваем обновление из {download_url}")
        response = requests.get(download_url, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    percent = int(downloaded_size * 100 / total_size)
                    keep_going = progress_dialog.Update(percent, f"Загружено {percent}%")
                    if not keep_going:
                        progress_dialog.Destroy()
                        logging.info("Загрузка отменена пользователем.")
                        return

        progress_dialog.Destroy()
        logging.info(f"Архив загружен: {zip_path}")

        # Распаковываем архив
        if not extract_zip(zip_path, temp_dir):
            wx.CallAfter(wx.MessageBox, "Ошибка распаковки архива.", "Ошибка", wx.ICON_ERROR)
            return

        # Создаём bat-файл для обновления
        create_update_bat(zip_path)

        # Запускаем bat-файл и закрываем программу
        bat_path = os.path.join(get_app_path(), "update_later.bat")
        subprocess.Popen([bat_path], shell=True)
        parent_frame.Close()

    except Exception as e:
        logging.error(f"Ошибка обновления: {e}")
        wx.CallAfter(wx.MessageBox, f"Ошибка обновления:\n{e}", "Ошибка", wx.ICON_ERROR)

def extract_zip(zip_path, extract_to):
    """Распаковывает архив в указанную директорию."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        logging.info(f"Архив распакован в {extract_to}")
        return True
    except Exception as e:
        logging.error(f"Ошибка распаковки: {e}")
        return False

def create_update_bat(zip_filename):
    """Создаёт bat-файл для завершения программы, обновления файлов и автозапуска Blind_log.exe."""
    bat_code = f"""@echo off
cd /d %~dp0
ping 127.0.0.1 -n 4 > nul
powershell -command "Expand-Archive -Path '{zip_filename}' -DestinationPath 'temp'"
move /Y "temp\\Blind_log.exe" "Blind_log.exe"
rd /s /q temp
del "{zip_filename}"
start "" "Blind_log.exe"
del "%~f0"
"""
    bat_path = os.path.join(get_app_path(), "update_later.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_code)
    logging.info(f"Создан bat-файл: {bat_path}")
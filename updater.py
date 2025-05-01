import os
import sys
import zipfile
import requests
import subprocess
import shutil
import logging
import wx

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
            for line in f:
                if "FileVersion" in line:
                    parts = line.split("'")
                    if len(parts) >= 4:
                        return parts[3]
    except FileNotFoundError:
        logging.error("Файл version.txt не найден.")
    except Exception as e:
        logging.error(f"Ошибка при чтении version.txt: {e}")
    return None

def version_tuple(v):
    """Преобразует строку версии в кортеж чисел."""
    return tuple(int(x) for x in v.strip().replace("v", "").split("."))

def check_update(parent_frame):
    """Проверяет наличие обновлений и запускает процесс обновления."""
    version_path = resource_path("version.txt")
    current_version = parse_version_txt(version_path)

    if not current_version:
        wx.CallAfter(wx.MessageBox, "Не удалось определить текущую версию.", "Ошибка", wx.ICON_ERROR)
        return

    try:
        response = requests.get("https://api.github.com/repos/r1oaz/blind_log/releases/latest")
        response.raise_for_status()
        data = response.json()
        latest_version = data["tag_name"]
        download_url = None

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
        wx.CallAfter(wx.MessageBox, f"У вас уже установлена последняя версия: {current_version}", "Обновление", wx.ICON_INFORMATION)
        return

    dlg = wx.MessageDialog(
        parent_frame,
        f"Доступна новая версия {latest_version}.\n\n"
        "Для обновления необходимо завершить программу.\n"
        "Если у вас есть несохранённый журнал, нажмите «Нет», сохраните его и снова запустите проверку обновлений.\n\n"
        "Обновить сейчас?",
        "Обновление",
        wx.YES_NO | wx.ICON_QUESTION
    )

    if dlg.ShowModal() == wx.ID_NO:
        dlg.Destroy()
        return

    dlg.Destroy()

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
        response = requests.get(download_url, stream=True)
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
        create_update_bat(temp_dir, zip_path)

        # Запускаем bat-файл и закрываем программу
        bat_path = os.path.join(temp_dir, "update.bat")
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

def create_update_bat(temp_dir, zip_path):
    """Создаёт bat-файл для завершения программы и обновления файлов."""
    bat_path = os.path.join(temp_dir, "update.bat")
    app_dir = get_app_path()

    with open(bat_path, "w", encoding="cp1251") as bat_file:
        bat_file.write(f"""
        @echo off
        timeout /t 2 /nobreak >nul
        taskkill /f /im Blind_log.exe >nul 2>&1
        timeout /t 1 /nobreak >nul
        xcopy "{temp_dir}\\Blind_log.exe" "{app_dir}" /e /y >nul
        del "{zip_path}" >nul
        rmdir /s /q "{temp_dir}" >nul
        start Blind_log.exe
        del "%~f0" >nul
                """)

    logging.info(f"Создан bat-файл: {bat_path}")
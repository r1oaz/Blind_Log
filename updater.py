import os
import sys
import zipfile
import shutil
import argparse
import requests
import wx
import threading
import time
import psutil
import logging

# Логгирование
log_path = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "updater.log")
logging.basicConfig(filename=log_path, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="URL архива обновления")
    parser.add_argument("--pid", type=int, required=False, help="PID основной программы (необязательно)")
    return parser.parse_args()


def terminate_process(pid):
    try:
        p = psutil.Process(pid)
        if p.is_running():
            logging.info(f"Завершаем процесс PID={pid}")
            p.terminate()
            p.wait(timeout=5)
    except Exception as e:
        logging.warning(f"Не удалось завершить процесс {pid}: {e}")


def extract_zip(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        logging.info(f"Архив распакован в {extract_to}")
        return True
    except Exception as e:
        logging.error(f"Ошибка распаковки: {e}")
        return False


def launch_program(path):
    try:
        logging.info(f"Запускаем программу: {path}")
        os.startfile(path)
    except Exception as e:
        logging.error(f"Не удалось запустить {path}: {e}")


class UpdaterFrame(wx.Frame):
    def __init__(self, url, pid=None):
        super().__init__(None, title="Обновление", size=(400, 150))
        self.url = url
        self.pid = pid
        self.zip_path = None

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.status = wx.StaticText(panel, label="Подготовка к обновлению...")
        self.gauge = wx.Gauge(panel, range=100, style=wx.GA_HORIZONTAL)

        vbox.Add(self.status, flag=wx.ALL | wx.EXPAND, border=10)
        vbox.Add(self.gauge, flag=wx.ALL | wx.EXPAND, border=10)

        panel.SetSizer(vbox)
        self.Centre()
        self.Show()

        threading.Thread(target=self.run_update, daemon=True).start()

    def run_update(self):
        try:
            logging.info("Updater запущен")
            if self.pid:
                terminate_process(self.pid)
            else:
                logging.info("PID не передан, пропускаем завершение процесса")

            filename = os.path.basename(self.url.split("?")[0])
            self.zip_path = os.path.join(os.getcwd(), filename)

            if not self.download_zip():
                return

            self.status.SetLabel("Распаковка файлов...")
            success = extract_zip(self.zip_path, os.getcwd())

            if success:
                self.status.SetLabel("Запуск новой версии...")
                time.sleep(1)
                exe_path = os.path.join(os.getcwd(), "Blind_log.exe")
                launch_program(exe_path)
            else:
                self.status.SetLabel("Ошибка распаковки")
                wx.CallAfter(wx.MessageBox, "Не удалось распаковать архив обновления.", "Ошибка", wx.ICON_ERROR)

        except Exception as e:
            logging.exception("Ошибка в процессе обновления")
            wx.CallAfter(wx.MessageBox, f"Обновление завершилось с ошибкой:\n{e}", "Ошибка", wx.ICON_ERROR)
        finally:
            time.sleep(1)
            self.Close()

    def download_zip(self):
        logging.info(f"Скачиваем: {self.url}")
        self.status.SetLabel("Загрузка обновления...")
        try:
            response = requests.get(self.url, stream=True, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Ошибка при загрузке архива: {e}")
            wx.CallAfter(wx.MessageBox, f"Ошибка при загрузке архива:\n{e}", "Ошибка", wx.ICON_ERROR)
            return False

        total = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(self.zip_path, 'wb') as f:
            for data in response.iter_content(chunk_size=1024):
                if data:
                    f.write(data)
                    downloaded += len(data)
                    percent = int((downloaded / total) * 100) if total else 0
                    wx.CallAfter(self.gauge.SetValue, percent)
                    wx.CallAfter(self.status.SetLabel, f"Загрузка обновления... {percent}%")
        logging.info(f"Файл загружен: {self.zip_path}")
        return True


if __name__ == "__main__":
    args = parse_args()
    app = wx.App(False)
    UpdaterFrame(args.url, args.pid)
    app.MainLoop()

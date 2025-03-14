<<<<<<< HEAD
import wx
from datetime import datetime

class Exporter:
    def __init__(self, qso_manager, settings_manager):
        self.qso_manager = qso_manager
        self.settings_manager = settings_manager

    def on_export(self, event):
        with wx.FileDialog(None, "Сохранить файл ADIF", wildcard="ADIF files (*.adi)|*.adi",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # Пользователь отменил сохранение

            # Получение пути для сохранения файла
            pathname = fileDialog.GetPath()
            self.export_to_adif(pathname)

    def export_to_adif(self, filepath):
        operator = self.settings_manager.settings['call']
        with open(filepath, 'w', encoding='cp1251') as file:
            # Запись заголовка ADIF
            file.write(f"#   Created:  {datetime.now().strftime('%d-%m-%Y  %H:%M:%S')}\n")
            file.write("<ADIF_VER:3>2.0\n<EOH>\n")

            # Запись данных QSO
            for qso in self.qso_manager.qso_list:
                adif_record = (
                    f"<OPERATOR:{len(operator)}>{operator}"
                    f"<CALL:{len(qso['call'])}>{qso['call']}"
                    f"<QSO_DATE:8>{qso['datetime'].replace('-', '').replace(':', '').replace(' ', '')[:8]}"
                    f"<TIME_ON:4>{qso['datetime'].replace('-', '').replace(':', '').replace(' ', '')[8:]}"
                    f"<FREQ:{len(qso['freq'])}>{qso['freq']}"
                    f"<MODE:{len(qso['mode'])}>{qso['mode']}"
                    f"<RST_SENT:{len(qso['rst_received'])}>{qso['rst_received']}"
                    f"<RST_RCVD:{len(qso['rst_sent'])}>{qso['rst_sent']}"
                    f"<GRIDSQUARE:{len(qso['qth'])}>{qso['qth']}"
                    f"<BAND:{len(qso['band'])}>{qso['band']}"
                    f"<NAME:{len(qso['name'])}>{qso['name']}"
                    f"<QTH:{len(qso['city'])}>{qso['city']}"
                    f"<COMMENT:{len(qso['comment'])}>{qso['comment']}"
                    f"<EOR>\n"
                )
=======
import wx
from datetime import datetime

class Exporter:
    def __init__(self, qso_manager, settings_manager):
        self.qso_manager = qso_manager
        self.settings_manager = settings_manager

    def on_export(self, event):
        with wx.FileDialog(None, "Сохранить файл ADIF", wildcard="ADIF files (*.adi)|*.adi",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # Пользователь отменил сохранение

            # Получение пути для сохранения файла
            pathname = fileDialog.GetPath()
            self.export_to_adif(pathname)

    def export_to_adif(self, filepath):
        operator = self.settings_manager.settings['call']
        with open(filepath, 'w', encoding='cp1251') as file:
            # Запись заголовка ADIF
            file.write(f"#   Created:  {datetime.now().strftime('%d-%m-%Y  %H:%M:%S')}\n")
            file.write("<ADIF_VER:3>2.0\n<EOH>\n")

            # Запись данных QSO
            for qso in self.qso_manager.qso_list:
                adif_record = (
                    f"<OPERATOR:{len(operator)}>{operator}"
                    f"<CALL:{len(qso['call'])}>{qso['call']}"
                    f"<QSO_DATE:8>{qso['datetime'].replace('-', '').replace(':', '').replace(' ', '')[:8]}"
                    f"<TIME_ON:4>{qso['datetime'].replace('-', '').replace(':', '').replace(' ', '')[8:]}"
                    f"<FREQ:{len(qso['freq'])}>{qso['freq']}"
                    f"<MODE:{len(qso['mode'])}>{qso['mode']}"
                    f"<RST_SENT:{len(qso['rst_received'])}>{qso['rst_received']}"
                    f"<RST_RCVD:{len(qso['rst_sent'])}>{qso['rst_sent']}"
                    f"<GRIDSQUARE:{len(qso['qth'])}>{qso['qth']}"
                    f"<BAND:{len(qso['band'])}>{qso['band']}"
                    f"<NAME:{len(qso['name'])}>{qso['name']}"
                    f"<QTH:{len(qso['city'])}>{qso['city']}"
                    f"<COMMENT:{len(qso['comment'])}>{qso['comment']}"
                    f"<EOR>\n"
                )
>>>>>>> 4d6728a1fd900293dcc7956277376e04f4acbc85
                file.write(adif_record)
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
                return False  # Пользователь отменил сохранение

            # Получение пути для сохранения файла
            pathname = fileDialog.GetPath()
            return self.export_to_adif(pathname)

    def export_to_adif(self, filepath):
        # Убедиться, что настройки загружены
        if not hasattr(self.settings_manager, 'settings'):
            raise ValueError("Настройки не загружены в SettingsManager")

        # Получение данных из настроек
        operator = self.settings_manager.settings.get('call', '')
        my_name = self.settings_manager.settings.get('operator_name', '')
        my_qth = self.settings_manager.settings.get('my_qth', '')
        my_city = self.settings_manager.settings.get('my_city', '')
        my_rig = self.settings_manager.settings.get('my_rig', '')
        my_lat = self.settings_manager.settings.get('my_lat', '')
        my_lon = self.settings_manager.settings.get('my_lon', '')

        try:
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
                        f"<RST_SENT:{len(qso.get('rst_sent', ''))}>{qso.get('rst_sent', '')}"
                        f"<RST_RCVD:{len(qso.get('rst_received', ''))}>{qso.get('rst_received', '')}"
                        f"<GRIDSQUARE:{len(qso.get('qth', ''))}>{qso.get('qth', '')}"
                        f"<BAND:{len(qso.get('band', ''))}>{qso.get('band', '')}"
                        f"<NAME:{len(qso.get('name', ''))}>{qso.get('name', '')}"
                        f"<QTH:{len(qso.get('city', ''))}>{qso.get('city', '')}"
                        f"<COMMENT:{len(qso.get('comment', ''))}>{qso.get('comment', '')}"
                        f"<MY_NAME:{len(my_name)}>{my_name}"
                        f"<MY_QTH:{len(my_qth)}>{my_qth}"
                        f"<MY_CITY:{len(my_city)}>{my_city}"
                        f"<MY_RIG:{len(my_rig)}>{my_rig}"
                        f"<MY_LAT:{len(my_lat)}>{my_lat}"
                        f"<MY_LON:{len(my_lon)}>{my_lon}"
                        f"<EOR>\n"
                    )
                    file.write(adif_record)

            wx.MessageBox("Экспорт в ADIF завершен успешно!", "Экспорт", wx.OK | wx.ICON_INFORMATION)
            return True
        except Exception as e:
            wx.MessageBox(f"Ошибка экспорта ADIF: {e}", "Ошибка", wx.OK | wx.ICON_ERROR)
            return False
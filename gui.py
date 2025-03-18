import wx
import wx.adv
import webbrowser
from datetime import datetime
from qso_manager import QSOManager
from exporter import Exporter
from settings import SettingsManager

class Blind_log(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        
        self.SetTitle("Blind_Log")
        self.qso_manager = QSOManager(parent=self)  # Передаем self как родителя
        self.settings_manager = SettingsManager()
        self.exporter = Exporter(self.qso_manager, self.settings_manager)
        
        self._init_ui()
        self._init_journal_columns()
        self._init_accelerator()
        self.Layout()
        self.Centre()

    def _init_ui(self):
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_PREFERENCES, "Настройки\tCtrl+P")
        file_menu.Append(wx.ID_EXIT, "Выход\tCtrl+Q")
        menubar.Append(file_menu, "Файл")
        
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "О программе\tShift+F1")
        help_menu.Append(wx.ID_HELP, "Справка\tF1")
        menubar.Append(help_menu, "Помощь")
        
        self.SetMenuBar(menubar)
        
        self.notebook = wx.Notebook(self, style=wx.NB_LEFT)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)
        
        add_panel = wx.Panel(self.notebook)
        self._init_add_qso_ui(add_panel)
        self.notebook.AddPage(add_panel, "Добавить QSO")
        
        journal_panel = wx.Panel(self.notebook)
        self._init_journal_ui(journal_panel)
        self.notebook.AddPage(journal_panel, "Журнал")
        
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_settings, id=wx.ID_PREFERENCES)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_help, id=wx.ID_HELP)

    def _init_add_qso_ui(self, panel):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Создание всех элементов с метками
        label_1 = wx.StaticText(panel, label="Позывной:")
        self.text_ctrl_1 = wx.TextCtrl(panel)
        label_2 = wx.StaticText(panel, label="Имя:")
        self.text_ctrl_2 = wx.TextCtrl(panel)
        label_3 = wx.StaticText(panel, label="Город:")
        self.text_ctrl_3 = wx.TextCtrl(panel)
        label_4 = wx.StaticText(panel, label="QTH:")
        self.text_ctrl_4 = wx.TextCtrl(panel)
        label_6 = wx.StaticText(panel, label="Частота:")
        self.text_ctrl_6 = wx.TextCtrl(panel)
        label_7 = wx.StaticText(panel, label="RST-принято:")
        self.text_ctrl_7 = wx.TextCtrl(panel)
        label_8 = wx.StaticText(panel, label="RST-передано:")
        self.text_ctrl_8 = wx.TextCtrl(panel)

        # Группировка полей
        fields = [
            (label_1, self.text_ctrl_1),
            (label_2, self.text_ctrl_2),
            (label_3, self.text_ctrl_3),
            (label_4, self.text_ctrl_4),
            (label_6, self.text_ctrl_6),
            (label_7, self.text_ctrl_7),
            (label_8, self.text_ctrl_8),
        ]

        # Добавление элементов в интерфейс
        for label, ctrl in fields:
            row_sizer = wx.BoxSizer(wx.HORIZONTAL)
            row_sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
            row_sizer.Add(ctrl, 1, wx.EXPAND)
            main_sizer.Add(row_sizer, 0, wx.EXPAND|wx.ALL, 5)

        # Выбор режима
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mode_label = wx.StaticText(panel, label="Режим:")
        self.mode_selector = wx.Choice(panel, choices=["AM", "FM", "SSB", "CW"])
        self.mode_selector.SetSelection(0)
        mode_sizer.Add(mode_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        mode_sizer.Add(self.mode_selector, 1, wx.EXPAND)
        main_sizer.Add(mode_sizer, 0, wx.EXPAND|wx.ALL, 5)

        # Выбор диапазона
        band_sizer = wx.BoxSizer(wx.HORIZONTAL)
        band_label = wx.StaticText(panel, label="Диапазон:")
        self.band_selector = wx.Choice(panel, choices=[
            "160m", "80m", "40m", 
            "20m", "10m", "6m",
            "2m", "70sm"
        ])
        self.band_selector.SetSelection(0)
        band_sizer.Add(band_label, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        band_sizer.Add(self.band_selector, 1, wx.EXPAND)
        main_sizer.Add(band_sizer, 0, wx.EXPAND|wx.ALL, 5)

        # Комментарий
        comment_label = wx.StaticText(panel, label="Комментарий:")
        self.comment_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        main_sizer.Add(comment_label, 0, wx.TOP|wx.LEFT, 5)
        main_sizer.Add(self.comment_ctrl, 1, wx.EXPAND|wx.ALL, 5)

        # Кнопка добавления
        self.add_btn = wx.Button(panel, label="Добавить QSO")
        main_sizer.Add(self.add_btn, 0, wx.ALIGN_RIGHT|wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        self.add_btn.Bind(wx.EVT_BUTTON, self.qso_manager.add_qso)
        self.text_ctrl_1.SetFocus()

        # Привязка полей к менеджеру QSO
        self.qso_manager.text_ctrl_1 = self.text_ctrl_1
        self.qso_manager.text_ctrl_2 = self.text_ctrl_2
        self.qso_manager.text_ctrl_3 = self.text_ctrl_3
        self.qso_manager.text_ctrl_4 = self.text_ctrl_4
        self.qso_manager.text_ctrl_6 = self.text_ctrl_6
        self.qso_manager.text_ctrl_7 = self.text_ctrl_7
        self.qso_manager.text_ctrl_8 = self.text_ctrl_8
        self.qso_manager.comment_ctrl = self.comment_ctrl
        self.qso_manager.band_selector = self.band_selector
        self.qso_manager.mode_selector = self.mode_selector

    def _init_journal_ui(self, panel):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.journal_list = wx.ListCtrl(
            panel, 
            style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES,
            size=(-1, 600)
        )
        
        # Кнопки управления журналом
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.edit_btn = wx.Button(panel, label="Редактировать")
        self.del_btn = wx.Button(panel, label="Удалить")
        self.export_btn = wx.Button(panel, label="Экспорт в ADIF")
        
        btn_sizer.Add(self.edit_btn, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.del_btn, 0, wx.RIGHT, 10)
        btn_sizer.Add(self.export_btn, 0)
        
        sizer.Add(self.journal_list, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT|wx.ALL, 10)
        panel.SetSizer(sizer)
        
        self.qso_manager.journal_list = self.journal_list
        self.edit_btn.Bind(wx.EVT_BUTTON, self.qso_manager.edit_qso)
        self.del_btn.Bind(wx.EVT_BUTTON, self.qso_manager.del_qso)
        self.export_btn.Bind(wx.EVT_BUTTON, self.exporter.on_export)

    def _init_journal_columns(self):
        columns = [
            ("Позывной", 120),
            ("Имя", 100),
            ("Город", 120),
            ("QTH", 120),
            ("Диапазон", 80),
            ("Режим", 80),  # Добавление столбца "Mode"
            ("RST-принято", 80),
            ("RST-передано", 80),
            ("Частота", 80),
            ("Комментарий", 250),
            ("Дата/Время", 150)  # Перемещение столбца "Дата/Время" в конец
        ]
        for idx, (title, width) in enumerate(columns):
            self.journal_list.InsertColumn(idx, title, width=width)

    def _init_accelerator(self):
        accel_entries = [
            (wx.ACCEL_CTRL, wx.WXK_RETURN, self.add_btn.GetId()),  # Ctrl+Enter для добавления QSO
            (wx.ACCEL_CTRL, ord('E'), self.edit_btn.GetId()),      # Ctrl+E для редактирования
            (wx.ACCEL_CTRL, ord('S'), self.export_btn.GetId()),    # Ctrl+S для экспорта
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, self.del_btn.GetId()), # Delete для удаления
            (wx.ACCEL_SHIFT, wx.WXK_F1, wx.ID_ABOUT),              # Shift+F1 для "О программе"
            (wx.ACCEL_NORMAL, wx.WXK_F1, wx.ID_HELP)               # F1 для "Справка"
        ]
        accel_tbl = wx.AcceleratorTable([wx.AcceleratorEntry(*entry) for entry in accel_entries])
        self.SetAcceleratorTable(accel_tbl)

    def on_page_changed(self, event):
        selected_page = self.notebook.GetSelection()
        if selected_page == 0:  # Вкладка "Добавить QSO"
            self.text_ctrl_1.SetFocus()
        elif selected_page == 1:  # Вкладка "Журнал"
            self.journal_list.SetFocus()
        event.Skip()

    def on_settings(self, event):
        self.settings_manager.show_settings()

    def on_exit(self, event):
        self.Close()

    def on_about(self, event):
        # Заглушка для "О программе"
        wx.MessageBox("О программе: Blind_Log", "О программе", wx.OK | wx.ICON_INFORMATION)

    def on_help(self, event):
        # Открытие файла help.html в браузере по умолчанию
        webbrowser.open("help.htm")
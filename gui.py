import subprocess
import wx
import wx.adv
import webbrowser
import os
from datetime import datetime
from updater import check_update

from qso_manager import QSOManager
from exporter import Exporter
from settings import SettingsManager
from utils import resource_path, get_version_info
from constants import MODES, BANDS, DEFAULT_MODE_INDEX, DEFAULT_BAND_INDEX, JOURNAL_COLUMNS

# Создаем кастомные ID для пунктов меню
ID_UPDATE = wx.NewIdRef()
ID_CHANGELOG = wx.NewIdRef()
ID_ADD_QSO = wx.NewIdRef()
ID_EDIT_QSO = wx.NewIdRef()
ID_DEL_QSO = wx.NewIdRef()
ID_EXPORT_QSO = wx.NewIdRef()


class Blind_log(wx.Frame):
    def __init__(self, *args, settings_manager=None, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        
        self.controls = {}
        self.SetTitle("Blind_Log")
        self.settings_manager = settings_manager  # Сохраняем экземпляр SettingsManager
        self.qso_manager = QSOManager(parent=self, settings_manager=self.settings_manager)  # Передаем settings_manager
        self.exporter = Exporter(self.qso_manager, self.settings_manager)
        
        self._init_ui()
        self._init_journal_columns()
        # Применяем видимость полей при старте (rebuild add panel and columns)
        self.apply_visible_fields()
        # Устанавливаем ускорители после финальной сборки контролов (add_btn может быть пересоздан)
        self._init_accelerator()
        self.Layout()
        self.Centre()
        # Добавляем обработчик закрытия окна
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def _init_ui(self):
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_PREFERENCES, "Настройки\tCtrl+P")
        file_menu.Append(wx.ID_EXIT, "Выход\tCtrl+Q")
        menubar.Append(file_menu, "Файл")

        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "О программе\tShift+F1")
        help_menu.Append(wx.ID_HELP, "Справка\tF1")
        help_menu.Append(ID_UPDATE, "Проверить обновления\tCtrl+U")
        help_menu.Append(ID_CHANGELOG, "Что нового\tCtrl+F1")
        menubar.Append(help_menu, "Помощь")
        self.SetMenuBar(menubar)

        self.notebook = wx.Notebook(self, style=wx.NB_LEFT)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)

        self.add_panel = wx.Panel(self.notebook)
        self._init_add_qso_ui(self.add_panel)
        self.notebook.AddPage(self.add_panel, "Добавить QSO")

        self.journal_panel = wx.Panel(self.notebook)
        self._init_journal_ui(self.journal_panel)
        self.notebook.AddPage(self.journal_panel, "Журнал")

        # Привязываем обработчики к правильным идентификаторам
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_settings, id=wx.ID_PREFERENCES)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_help, id=wx.ID_HELP)
        self.Bind(wx.EVT_MENU, self.on_check_updates, id=ID_UPDATE)
        self.Bind(wx.EVT_MENU, self.on_show_changelog, id=ID_CHANGELOG)
        # Привязка обработчиков для ускорителей QSO (работают независимо от ID кнопок)
        self.Bind(wx.EVT_MENU, lambda e: self.qso_manager.add_qso(e), id=ID_ADD_QSO)
        self.Bind(wx.EVT_MENU, lambda e: self.qso_manager.edit_qso(e), id=ID_EDIT_QSO)
        self.Bind(wx.EVT_MENU, lambda e: self.qso_manager.del_qso(e), id=ID_DEL_QSO)
        self.Bind(wx.EVT_MENU, lambda e: self.exporter.on_export(e), id=ID_EXPORT_QSO)

    def _init_add_qso_ui(self, panel):
        # Построение формы добавления QSO: создаём только видимые контролы
        self.controls = getattr(self, 'controls', {})
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        visible = self.settings_manager.get_visible_fields()

        field_definitions = [
            ('call', "Позывной:", wx.TextCtrl, {'style': wx.TE_PROCESS_ENTER}),
            ('name', "Имя:", wx.TextCtrl, {}),
            ('city', "Город:", wx.TextCtrl, {}),
            ('qth', "QTH:", wx.TextCtrl, {}),
            ('freq', "Частота:", wx.TextCtrl, {}),
            ('rst_received', "RST-принято:", wx.TextCtrl, {}),
            ('rst_sent', "RST-передано:", wx.TextCtrl, {}),
        ]

        for key, label_text, ctrl_class, styles in field_definitions:
            if not visible.get(key, True):
                # remove any existing control reference
                if key in self.controls:
                    del self.controls[key]
                continue
            row_sizer = wx.BoxSizer(wx.HORIZONTAL)
            label = wx.StaticText(panel, label=label_text)
            ctrl = ctrl_class(panel, **styles)
            self.controls[key] = ctrl
            row_sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
            row_sizer.Add(ctrl, 1, wx.EXPAND)
            main_sizer.Add(row_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Привязка Enter для позывного
        if 'call' in self.controls:
            self.controls['call'].Bind(wx.EVT_TEXT_ENTER, self.qso_manager.on_callsign_enter)

        # Режим
        if visible.get('mode', True):
            mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
            mode_label = wx.StaticText(panel, label="Режим:")
            self.controls['mode'] = wx.Choice(panel, choices=MODES)
            self.controls['mode'].SetSelection(DEFAULT_MODE_INDEX)
            mode_sizer.Add(mode_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
            mode_sizer.Add(self.controls['mode'], 1, wx.EXPAND)
            main_sizer.Add(mode_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Диапазон
        if visible.get('band', True):
            band_sizer = wx.BoxSizer(wx.HORIZONTAL)
            band_label = wx.StaticText(panel, label="Диапазон:")
            self.controls['band'] = wx.Choice(panel, choices=BANDS)
            self.controls['band'].SetSelection(DEFAULT_BAND_INDEX)
            band_sizer.Add(band_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
            band_sizer.Add(self.controls['band'], 1, wx.EXPAND)
            main_sizer.Add(band_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Комментарий
        if visible.get('comment', True):
            comment_label = wx.StaticText(panel, label="Комментарий:")
            self.controls['comment'] = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
            main_sizer.Add(comment_label, 0, wx.TOP | wx.LEFT, 5)
            main_sizer.Add(self.controls['comment'], 1, wx.EXPAND | wx.ALL, 5)

        # Дата и время
        if visible.get('date', True) or visible.get('time', True):
            date_time_sizer = wx.BoxSizer(wx.HORIZONTAL)
            date_label = wx.StaticText(panel, label="Дата:")
            self.controls['date'] = wx.adv.DatePickerCtrl(panel, style=wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY)
            time_label = wx.StaticText(panel, label="Время:")
            self.controls['time'] = wx.adv.TimePickerCtrl(panel)
            date_time_sizer.Add(date_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
            date_time_sizer.Add(self.controls['date'], 1, wx.EXPAND | wx.RIGHT, 10)
            date_time_sizer.Add(time_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
            date_time_sizer.Add(self.controls['time'], 1, wx.EXPAND)
            main_sizer.Add(date_time_sizer, 0, wx.EXPAND | wx.ALL, 5)
            current_time = self.qso_manager._get_current_time_with_timezone()
            try:
                self.controls['date'].SetValue(wx.DateTime.FromDMY(current_time.day, current_time.month - 1, current_time.year))
                self.controls['time'].SetValue(wx.DateTime.FromHMS(current_time.hour, current_time.minute, 0))
            except Exception:
                pass

        # Кнопка добавления
        self.add_btn = wx.Button(panel, label="Добавить QSO")
        main_sizer.Add(self.add_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        panel.SetSizer(main_sizer)
        self.add_btn.Bind(wx.EVT_BUTTON, self.qso_manager.add_qso)
        if 'call' in self.controls:
            self.controls['call'].SetFocus()

        # Передаем элементы управления менеджеру QSO
        self.qso_manager.set_controls(self.controls)
        self.qso_manager._initialize_rst_fields()

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
        # self.export_btn больше не добавляется в интерфейс, но кнопка и обработчик остаются для Ctrl+S
        # btn_sizer.Add(self.export_btn, 0)
        sizer.Add(self.journal_list, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT|wx.ALL, 10)
        panel.SetSizer(sizer)
        
        self.qso_manager.journal_list = self.journal_list
        self.edit_btn.Bind(wx.EVT_BUTTON, self.qso_manager.edit_qso)
        self.del_btn.Bind(wx.EVT_BUTTON, self.qso_manager.del_qso)
        self.export_btn.Bind(wx.EVT_BUTTON, self.exporter.on_export)

    def _init_journal_columns(self):
        # Перестроить колонки согласно видимости полей
        try:
            while self.journal_list.GetColumnCount() > 0:
                self.journal_list.DeleteColumn(0)
        except Exception:
            pass
        visible = self.settings_manager.get_visible_fields()
        journal_columns = []
        idx = 0
        # Используем QSO_FIELD_NAMES и JOURNAL_COLUMNS для порядка и заголовков
        from constants import QSO_FIELD_NAMES
        for (field_name, (title, width)) in zip(QSO_FIELD_NAMES, JOURNAL_COLUMNS):
            if field_name == 'datetime':
                continue
            if visible.get(field_name, True):
                self.journal_list.InsertColumn(idx, title, width=width)
                journal_columns.append(field_name)
                idx += 1
        # Добавляем комбинированную дата/время если хотя бы одно видно
        if visible.get('date', True) or visible.get('time', True):
            dt_title, dt_width = JOURNAL_COLUMNS[-1]
            self.journal_list.InsertColumn(idx, dt_title, width=dt_width)
            journal_columns.append('datetime')
        # Сохраняем порядок колонок в QSOManager
        self.qso_manager.journal_columns = journal_columns

    def apply_visible_fields(self):
        # Перестроить add_panel и колонки журнала
        try:
            self.add_panel.DestroyChildren()
        except Exception:
            pass
        self._init_add_qso_ui(self.add_panel)
        try:
            self.journal_list.DeleteAllItems()
        except Exception:
            pass
        self._init_journal_columns()
        try:
            self.qso_manager._update_journal()
        except Exception:
            pass

    def _init_accelerator(self):
        # Используем кастомные IDs для ускорителей, чтобы они работали даже после перестроения UI
        accel_entries = [
            (wx.ACCEL_CTRL, wx.WXK_RETURN, ID_ADD_QSO),
            (wx.ACCEL_CTRL, ord('E'), ID_EDIT_QSO),
            (wx.ACCEL_CTRL, ord('S'), ID_EXPORT_QSO),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_DEL_QSO),
            (wx.ACCEL_SHIFT, wx.WXK_F1, wx.ID_ABOUT),
            (wx.ACCEL_NORMAL, wx.WXK_F1, wx.ID_HELP),
            (wx.ACCEL_CTRL, wx.WXK_F1, ID_CHANGELOG),
            (wx.ACCEL_CTRL, ord('U'), ID_UPDATE),
        ]
        accel_tbl = wx.AcceleratorTable([wx.AcceleratorEntry(*entry) for entry in accel_entries])
        self.SetAcceleratorTable(accel_tbl)
    def on_show_changelog(self, event):
        changelog_path = resource_path("changeLog.txt")
        try:
            with open(changelog_path, "r", encoding="utf-8") as f:
                changelog_text = f.read()
        except Exception as e:
            wx.MessageBox(f"Не удалось открыть changeLog.txt: {e}", "Ошибка", wx.OK | wx.ICON_ERROR)
            return

        dlg = wx.Dialog(self, title="История изменений (changelog)", size=(600, 500))
        vbox = wx.BoxSizer(wx.VERTICAL)
        text_ctrl = wx.TextCtrl(dlg, value=changelog_text, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        vbox.Add(text_ctrl, 1, wx.EXPAND|wx.ALL, 10)
        btn = wx.Button(dlg, label="Закрыть")
        btn.Bind(wx.EVT_BUTTON, lambda evt: dlg.Close())
        vbox.Add(btn, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        dlg.SetSizer(vbox)
        dlg.ShowModal()
        dlg.Destroy()

    def on_page_changed(self, event):
        selected_page = self.notebook.GetSelection()
        if (selected_page == 0):
            self.controls['call'].SetFocus()
        elif (selected_page == 1):
            self.journal_list.SetFocus()
        event.Skip()

    def on_settings(self, event):
        # Открыть диалог настроек; после закрытия применяем настройки и перестраиваем UI
        self.settings_manager.show_settings(parent=self)
        # Обновить настройки в менеджере QSO (перечитать значения, инициализировать QRZ при необходимости)
        self.qso_manager.reload_settings()
        # Применить видимость полей немедленно (перестроит форму и колонки)
        try:
            self.apply_visible_fields()
        except Exception:
            pass

    def on_exit(self, event):
        """
        Обработчик для пункта меню "Выход".
        Завершает приложение без вызова проверки обновлений.
        """
        self.Close()  # Закрываем главное окно, завершая приложение

    def on_close(self, event):
        """
        Обработчик закрытия окна (крестик или Alt+F4).
        Если в журнале есть хотя бы одна запись, спрашивает о сохранении.
        """
        if len(self.qso_manager.qso_list) > 0:
            dlg = wx.MessageDialog(
                self,
                "В журнале есть несохранённые записи. Сохранить журнал перед выходом?",
                "Сохранить журнал?",
                wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION
            )
            dlg.SetYesNoCancelLabels("Сохранить", "Не сохранять", "Отмена")
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_YES:
                # Открыть диалог экспорта ADIF
                export_result = self.exporter.on_export(None)
                if export_result:
                    self.Destroy()
                else:
                    # Если экспорт не удался или отменён, не закрывать окно
                    event.Veto()
                    return
            elif result == wx.ID_NO:
                self.Destroy()
            else:
                # Отмена — не закрывать окно
                event.Veto()
                return
        else:
            self.Destroy()

    def on_about(self, event):
        """
        Обработчик для пункта меню "О программе".
        """
        version_info = get_version_info()

        # Создание диалога "О программе"
        about_dialog = wx.Dialog(self, title="О программе", size=(400, 300))
        about_sizer = wx.BoxSizer(wx.VERTICAL)

        # Текст с информацией о программе
        about_text = wx.StaticText(
            about_dialog,
            label=f"{version_info['description']}\n\n"
                  f"Автор: {version_info['author']}\n"
                  f"Версия: {version_info['version']}"
        )
        about_text.Wrap(380)
        about_sizer.Add(about_text, 1, wx.ALL | wx.EXPAND, 10)

        # Кнопка для перехода на сайт программы
        site_button = wx.Button(about_dialog, label="Перейти на сайт программы")
        site_button.Bind(wx.EVT_BUTTON, lambda evt: webbrowser.open("https://github.com/r1oaz/Blind_Log"))
        about_sizer.Add(site_button, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        # Кнопка "Закрыть"
        close_button = wx.Button(about_dialog, label="Закрыть")
        close_button.Bind(wx.EVT_BUTTON, lambda evt: about_dialog.Close())
        about_sizer.Add(close_button, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        about_dialog.SetSizer(about_sizer)
        about_dialog.ShowModal()
        about_dialog.Destroy()

    def on_help(self, event):
        # Открытие файла help.htm из ресурсов, упакованных в exe
        help_path = resource_path("help.htm")
        webbrowser.open(help_path)

    def on_check_updates(self, event):
        check_update(self)  # вызываем функцию и передаём главное окно
import wx
from gui import My_Log

class MyApp(wx.App):
    def OnInit(self):
        self.frame = My_Log(None)
        self.frame.Show()
        return True

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
import wx
from gui import Blind_log

class MyApp(wx.App):
    def OnInit(self):
        self.frame = Blind_log(None)
        self.frame.Show()
        return True

if __name__ == "__main__":
    app = MyApp()
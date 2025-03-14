<<<<<<< HEAD
import wx
from gui import Blind_log

class MyApp(wx.App):
    def OnInit(self):
        self.frame = Blind_log(None)
        self.frame.Show()
        return True

if __name__ == "__main__":
    app = MyApp()
=======
import wx
from gui import My_Log

class MyApp(wx.App):
    def OnInit(self):
        self.frame = My_Log(None)
        self.frame.Show()
        return True

if __name__ == "__main__":
    app = MyApp()
>>>>>>> 4d6728a1fd900293dcc7956277376e04f4acbc85
    app.MainLoop()
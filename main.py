"""
Main module for the Blind_log application.
"""

import wx
from gui import Blind_log

class MyApp(wx.App):
    """
    Application class for Blind_log.
    """
    def OnInit(self):
        """
        Initialize the application.
        """
        try:
            self.frame = Blind_log(None)
            self.frame.Show()
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
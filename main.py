import tkinter as tk
from app.gui.login_app import TelegramLoginApp

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramLoginApp(root)
    root.mainloop()
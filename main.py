import customtkinter as ctk
import sv_ttk

from scripts.soundboard import Soundboard

if __name__ == "__main__":
    root = ctk.CTk()
    app = Soundboard(root)
    sv_ttk.set_theme("dark")

    root.mainloop()

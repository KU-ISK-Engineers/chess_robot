import tkinter as tk
from PIL import Image, ImageTk



def gui_main():
    global root
    root = tk.Tk()
    root.configure(bg="#FFFFFF")

    #root.attributes('-fullscreen', True)
    #root.attributes('-type', 'splash')

    root.mainloop()

gui_main()

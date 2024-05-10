import tkinter as tk
from PIL import Image, ImageTk

def clear_widget(widget):
    # Destroy the widget
    widget.destroy()

def start_game():
    global button  # Access the global button variable
    print("Game starting")

    # What's needed to start the game
    #
    #
    #

    # Clear the button after the game starts
    clear_widget(button)

def add_logos(root):
    image1 = Image.open("images/ku.png")
    image1 = ImageTk.PhotoImage(image1)

    image2 = Image.open("images/conexus.png")
    image2 = ImageTk.PhotoImage(image2)

    image3 = Image.open("images/fondas.png")
    image3 = ImageTk.PhotoImage(image3)

    screen_width = root.winfo_screenwidth()

    # Calculate the x-coordinate for each image to place them in a row
    image_width = max(image1.width(), image2.width(), image3.width())
    x1 = (screen_width - 3 * image_width) // 4
    x2 = x1 + image_width + (screen_width - 3 * image_width) // 2
    x3 = x2 + image_width + (screen_width - 3 * image_width) // 2

    # Place each image at the calculated coordinates
    label1 = tk.Label(root, image=image1)
    label1.image = image1  # Keep a reference to prevent garbage collection
    label1.place(x=x1, y=0)

    label2 = tk.Label(root, image=image2)
    label2.image = image2  # Keep a reference to prevent garbage collection
    label2.place(x=x2, y=0)

    label3 = tk.Label(root, image=image3)
    label3.image = image3  # Keep a reference to prevent garbage collection
    label3.place(x=x3, y=0)
    
    


def create_empty_frame(root):
    frame = tk.Frame(root, bg="#FFFFFF")
    frame.pack(fill=tk.BOTH, expand=True)
    

def start_button(root):   
    global button  # Declare button as global variable

    # Load the PNG image for the start button
    image = Image.open("images/start.png")
    image = ImageTk.PhotoImage(image)

    # Create a button with the image
    button = tk.Button(root, image=image, command=start_game, borderwidth=0, highlightthickness=0)
    button.image = image  # Keep a reference to the image to prevent garbage collection

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate the coordinates to place the button in the center
    x = (screen_width - image.width()) // 2
    y = (screen_height - image.height()) // 2

    # Place the button at the calculated coordinates
    button.place(x=x, y=y)


root = tk.Tk()
create_empty_frame(root)
add_logos(root)
start_button(root)
root.mainloop()    

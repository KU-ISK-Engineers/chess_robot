import tkinter as tk
from PIL import Image, ImageTk

def clear_widget(widget):
    # Destroy the widget
    widget.destroy()

def levels_screen(root):
    global level  # level=depth

    def select_level(level_value):
        global level
        level = level_value
        for widget in root.winfo_children():
            if widget not in logo_widgets:  # Preserve logos
                clear_widget(widget)
        start_button(root)
        print(level)

    # Load level images
    level1_img = Image.open("gui/images/beginner.png")
    level2_img = Image.open("gui/images/intermediate.png")
    level3_img = Image.open("gui/images/advanced.png")
    level4_img = Image.open("gui/images/unbeatable.png")

    level1_img = ImageTk.PhotoImage(level1_img)
    level2_img = ImageTk.PhotoImage(level2_img)
    level3_img = ImageTk.PhotoImage(level3_img)
    level4_img = ImageTk.PhotoImage(level4_img)

    # Create buttons for each level
    level1_button = tk.Button(root, image=level1_img, command=lambda: select_level(2), borderwidth=0, bg="#FFFFFF")
    level1_button.image = level1_img
    level1_button.place(x=400, y=200)

    level2_button = tk.Button(root, image=level2_img, command=lambda: select_level(4), borderwidth=0, bg="#FFFFFF")
    level2_button.image = level2_img
    level2_button.place(x=400, y=325)

    level3_button = tk.Button(root, image=level3_img, command=lambda: select_level(6), borderwidth=0, bg="#FFFFFF")
    level3_button.image = level3_img
    level3_button.place(x=400, y=450)

    level4_button = tk.Button(root, image=level4_img, command=lambda: select_level(20), borderwidth=0, bg="#FFFFFF")
    level4_button.image = level4_img
    level4_button.place(x=400, y=575)

def game_screen(root):
    # Load the images
    
    turns = Image.open("gui/images/turns.png")
    robot_turn_active = Image.open("gui/images/robot_turn_active.png")
    robot_turn_inactive = Image.open("gui/images/robot_turn_inactive.png")
    your_turn_active = Image.open("gui/images/your_turn_active.png")
    your_turn_inactive = Image.open("gui/images/your_turn_inactive.png")

    turns = ImageTk.PhotoImage(turns)
    robot_turn_active = ImageTk.PhotoImage(robot_turn_active)
    robot_turn_inactive = ImageTk.PhotoImage(robot_turn_inactive)
    your_turn_active = ImageTk.PhotoImage(your_turn_active)
    your_turn_inactive = ImageTk.PhotoImage(your_turn_inactive)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Place the turns image in the center
    turns_label = tk.Label(root, image=turns, bg="#FFFFFF")
    turns_label.image = turns
    x_turns =500
    y_turns = (screen_height) // 4
    turns_label.place(x=x_turns, y=y_turns)

    # Place the inactive robot and user turn labels below the turns image
    robot_label = tk.Label(root, image=robot_turn_inactive, bg="#FFFFFF")
    robot_label.image = robot_turn_inactive
    robot_label.place(x=x_turns, y=y_turns + 2*turns.height() + 10)

    user_label = tk.Label(root, image=your_turn_inactive, bg="#FFFFFF")
    user_label.image = your_turn_inactive
    user_label.place(x=x_turns, y=y_turns + 3*turns.height() + 10)

    # Function to update the turn indicators
    def update_turn(active):
        if active == "robot":
            robot_label.config(image=robot_turn_active)
            robot_label.image = robot_turn_active
            user_label.config(image=your_turn_inactive)
            user_label.image = your_turn_inactive
        elif active == "user":
            robot_label.config(image=robot_turn_inactive)
            robot_label.image = robot_turn_inactive
            user_label.config(image=your_turn_active)
            user_label.image = your_turn_active

    # Simulate some event after 3 seconds
    root.after(3000, lambda: update_turn("robot"))
    root.after(6000, lambda: update_turn("user"))

def start_game():
    for widget in root.winfo_children():
        if widget not in logo_widgets:  # Preserve logos
            clear_widget(widget)
    game_screen(root)

def add_logos(root):
    global logo_widgets
    logo_widgets = []

    # Load the images
    image1 = Image.open("gui/images/ku.png")
    image2 = Image.open("gui/images/conexus.png")
    image3 = Image.open("gui/images/fondas.png")

    # Define the target height
    target_height = 100

    # Calculate the aspect ratio and resize each image to the same height
    def resize_image(image, target_height):
        aspect_ratio = image.width / image.height
        new_width = int(target_height * aspect_ratio)
        return image.resize((new_width, target_height), Image.Resampling.LANCZOS)

    image1 = resize_image(image1, target_height)
    image2 = resize_image(image2, target_height)
    image3 = resize_image(image3, target_height)

    # Convert the images to ImageTk.PhotoImage
    image1 = ImageTk.PhotoImage(image1)
    image2 = ImageTk.PhotoImage(image2)
    image3 = ImageTk.PhotoImage(image3)

    screen_width = root.winfo_screenwidth()

    # Calculate the total width of all images and spacing
    total_width = image1.width() + image2.width() + image3.width()
    spacing = (screen_width - total_width) // 4

    # Calculate the x-coordinate for each image to place them in a row
    x1 = spacing
    x2 = x1 + image1.width() + spacing
    x3 = x2 + image2.width() + spacing

    # Place each image at the calculated coordinates
    label1 = tk.Label(root, image=image1, bg="#FFFFFF")
    label1.image = image1  # Keep a reference to prevent garbage collection
    label1.place(x=x1, y=0)
    logo_widgets.append(label1)

    label2 = tk.Label(root, image=image2, bg="#FFFFFF")
    label2.image = image2  # Keep a reference to prevent garbage collection
    label2.place(x=x2, y=0)
    logo_widgets.append(label2)

    label3 = tk.Label(root, image=image3, bg="#FFFFFF")
    label3.image = image3  # Keep a reference to prevent garbage collection
    label3.place(x=x3, y=0)
    logo_widgets.append(label3)

def create_empty_frame(root):
    frame = tk.Frame(root, bg="#FFFFFF")
    frame.pack(fill=tk.BOTH, expand=True)

def start_button(root):   
    global button  # Declare button as global variable

    # Load the PNG image for the start button
    image = Image.open("gui/images/start.png")
    image = ImageTk.PhotoImage(image)

    # Create a button with the image
    button = tk.Button(root, image=image, command=start_game, borderwidth=0, highlightthickness=0, bg="#FFFFFF")
    button.image = image  # Keep a reference to the image to prevent garbage collection

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate the coordinates to place the button in the center
    x = (screen_width - image.width()) // 2
    y = (screen_height - image.height()) // 2

    # Place the button at the calculated coordinates
    button.place(x=x, y=y)

root = tk.Tk()
root.configure(bg="#FFFFFF")  # Set the background color of the main window to white
create_empty_frame(root)
add_logos(root)
levels_screen(root)
root.mainloop()

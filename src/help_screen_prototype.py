import tkinter as tk
from PIL import Image, ImageTk
from tkvideo import tkvideo


def clear_screen():
    for widget in root.winfo_children():
        if widget not in logo_widgets:
            widget.destroy()


def background():
    global logo_widgets, count_label
    logo_widgets = []

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    image1 = Image.open("images/fondas.png")
    image2 = Image.open("images/ku.png")
    image3 = Image.open("images/conexus.png")
    killcount = Image.open("images/killcount.png")

    target_height = 100

    def resize_image(image, target_height):
        aspect_ratio = image.width / image.height
        new_width = int(target_height * aspect_ratio)
        return image.resize((new_width, target_height), Image.Resampling.LANCZOS)

    image1 = resize_image(image1, target_height)
    image2 = resize_image(image2, target_height)
    image3 = resize_image(image3, target_height)
    killcount = resize_image(killcount, 150)

    image1 = ImageTk.PhotoImage(image1)
    image2 = ImageTk.PhotoImage(image2)
    image3 = ImageTk.PhotoImage(image3)
    killcount = ImageTk.PhotoImage(killcount)

    total_width = image1.width() + image2.width() + image3.width()
    spacing = (screen_width - total_width) // 5

    x1 = spacing
    x2 = x1 + image1.width() + spacing
    x3 = x2 + image2.width() + spacing
    x4 = 30

    label1 = tk.Label(root, image=image1, borderwidth=0, bg="#FFFFFF")
    label1.image = image1
    label1.place(x=x1, y=0)
    logo_widgets.append(label1)

    label2 = tk.Label(root, image=image2, borderwidth=0, bg="#FFFFFF")
    label2.image = image2
    label2.place(x=x2, y=0)
    logo_widgets.append(label2)

    label3 = tk.Label(root, image=image3, borderwidth=0, bg="#FFFFFF")
    label3.image = image3
    label3.place(x=x3, y=0)
    logo_widgets.append(label3)

    killcount_label = tk.Label(root, image=killcount, borderwidth=0, bg="#FFFFFF")
    killcount_label.image = killcount
    killcount_label.place(x=x4, y=150)
    logo_widgets.append(killcount_label)

    count_label = tk.Label(root, text=str('5'), bg="#FFFFFF", font=("Arial", 30), fg="black")
    count_label.place(x=x4 + killcount.width() // 2 - 20, y=230)
    logo_widgets.append(count_label)

    help=help_button()
    help.place(relx=0.1, rely=0.45, anchor='center')
    logo_widgets.append(help)
    
def help_screen():
    global main_frame, left_frame
    clear_screen()
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    left_frame = tk.Frame(root, width=screen_width/3, background='white')
    left_frame.pack(side="left", fill="y")
    main_frame = tk.Frame(root,  background='white')
    main_frame.pack(side="right", fill="both", expand=True)

    # List of images for buttons and corresponding videos
    button_images = ["images/pawn_button.png", "images/rook_button.png", "images/knight_button.png", "images/bishop_button.png", "images/queen_button.png", "images/king_button.png"]
    video_files = ["images/pawn_moves.mp4", "images/rook_moves.mp4", "images/knight_moves.mp4", "images/bishop_moves.mp4", "images/queen_moves.mp4", "images/king_moves.mp4"]

    # Create buttons with images in the left frame
    for i, button_image_path in enumerate(button_images):
        button_image = Image.open(button_image_path)
        button_image = button_image.resize((200, 100), Image.Resampling.LANCZOS)
        button_image = ImageTk.PhotoImage(button_image)
        
        button = tk.Button(left_frame, image=button_image, command=lambda i=i: show_video(video_files[i]),borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
        button.image = button_image
        button.pack(pady=10, anchor="center")


def help_button():
    help_button_image = Image.open("images/help.png")
    help_button_image = help_button_image.resize((100, 75), Image.Resampling.LANCZOS)
    help_button_image = ImageTk.PhotoImage(help_button_image)

    help_button = tk.Button(root, image=help_button_image, command=help_screen, borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    help_button.image = help_button_image
    
    return help_button
# Function to switch to the video view screen
def show_video(video_path):
    global current_player

    for widget in main_frame.winfo_children():
        widget.destroy()

    main_frame.update_idletasks()  # Ensure the frame has been fully updated
    frame_width = main_frame.winfo_width()
    video_size = int(frame_width * 0.5) 

    video_label = tk.Label(main_frame, width=video_size, height=video_size)
    video_label.place(relx=0.5, rely=0.5, anchor='center')
    
    current_player = tkvideo(video_path, video_label, loop=1, size=(video_size, video_size))
    current_player.play()

    back_button_image = Image.open("images/back.png")
    back_button_image = back_button_image.resize((50, 50), Image.Resampling.LANCZOS)
    back_button_image = ImageTk.PhotoImage(back_button_image)

    # Back button
    back_button_image = Image.open("images/back.png")
    back_button_image = back_button_image.resize((100, 70), Image.Resampling.LANCZOS)
    back_button_image = ImageTk.PhotoImage(back_button_image)
    back_button = tk.Button(root, image=back_button_image, command=clear_screen, borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    back_button.image = back_button_image
    back_button.place(relx=0.9, rely=0.9, anchor='center')


root = tk.Tk()
root.configure(bg="#FFFFFF")
background()
root.mainloop()

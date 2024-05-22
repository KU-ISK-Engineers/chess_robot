import tkinter as tk
from PIL import Image, ImageTk
import chess.engine

robot_count = 0
root = None
game = None

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

def update_robot_win_count():
    global robot_count
    read_robot_count_from_file()
    robot_count += 1
    def write_robot_count_to_file():
        with open("gui/robot_win_count.txt", "w") as file:
            file.write(str(robot_count))
    write_robot_count_to_file()
    def update_count_label():
        count_label.config(text=str(robot_count))
    update_count_label()

def read_robot_count_from_file():
    global robot_count
    try:
        with open("gui/robot_win_count.txt", "r") as file:
            content = file.read()
            if content:
                robot_count = int(content)
    except FileNotFoundError:
        robot_count = 0
def place_image(path):
    image = Image.open(path)
    image = ImageTk.PhotoImage(image)
    label = tk.Label(root, image=image, borderwidth=0)
    x=(screen_width - image.width()) // 2
    y=(screen_height - image.height()) // 2 - 200
    label.image = image
    label.place(x, y)

def win_lose_msg():
    clear_widgets()


    back = Image.open("images/back.png")
    back = ImageTk.PhotoImage(back)
    back_button = tk.Button(root, image=back, command=lambda: levels_screen(), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    back_button.image = back
    back_button.place(x=1200, y=800)


    place_image("gui/images/game_over.png")

    def display_win_lose_messages():
        image_path = None
        if game.board.perspective==chess.WHITE:
            if game.check_game_over() == "1-0":
                image_path = "images/you_won.png"
            elif game.check_game_over() == "0-1":
                image_path = "images/you_lose.png"
                update_robot_win_count()
            elif game.check_game_over() == "1/2-1/2":
                image_path = "images/draw.png"
        elif game.board.perspective==chess.BLACK:
            if game.check_game_over() == "1-0":
                image_path = "images/you_lose.png"
                update_robot_win_count()
            elif game.check_game_over() == "0-1":
                image_path = "images/you_won.png"
            elif game.check_game_over() == "1/2-1/2":
                image_path = "images/draw.png"

        if image_path:
            place_image(image_path)
    

    root.after(2000, display_win_lose_messages)

def play_chess(level, player_color, root):
    result = "1-0"
    win_lose_msg(player_color, result, root)

def clear_widgets():
    for widget in root.winfo_children():
        if widget not in logo_widgets:
            widget.destroy()

def levels_screen():
    clear_widgets()

    def select_level(level_value):
        game.depth = level_value
        clear_widgets()
        color_screen()

    place_image("images/choose_level.png")

    level1_img = Image.open("images/beginner.png")
    level2_img = Image.open("images/intermediate.png")
    level3_img = Image.open("images/advanced.png")
    level4_img = Image.open("images/unbeatable.png")

    level1_img = ImageTk.PhotoImage(level1_img)
    level2_img = ImageTk.PhotoImage(level2_img)
    level3_img = ImageTk.PhotoImage(level3_img)
    level4_img = ImageTk.PhotoImage(level4_img)

    level1_button = tk.Button(root, image=level1_img, command=lambda: select_level(2), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    level1_button.image = level1_img
    level1_button.place(x=(screen_width - level1_img.width()) // 2, y=(screen_height - 110) // 2 - 50)

    level2_button = tk.Button(root, image=level2_img, command=lambda: select_level(4), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    level2_button.image = level2_img
    level2_button.place(x=(screen_width - level2_img.width()) // 2, y=(screen_height - 110) // 2 + 75)

    level3_button = tk.Button(root, image=level3_img, command=lambda: select_level(6), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    level3_button.image = level3_img
    level3_button.place(x=(screen_width - level3_img.width()) // 2, y=(screen_height - 110) // 2 + 200)

    level4_button = tk.Button(root, image=level4_img, command=lambda: select_level(20), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    level4_button.image = level4_img
    level4_button.place(x=(screen_width - level4_img.width()) // 2, y=(screen_height - 110) // 2 + 325)

def receive_move():
    
    update_turn("user")

def send_move(w, update_turn_func):
    w.destroy()
    update_turn_func("robot")

def update_turn(active, robot_label, user_label, robot_turn_active, robot_turn_inactive, your_turn_active, your_turn_inactive, finished_button):
    if active == "robot":
        robot_label.config(image=robot_turn_active)
        robot_label.image = robot_turn_active
        user_label.config(image=your_turn_inactive)
        user_label.image = your_turn_inactive
        game.player=ROBOT

    elif active == "user":
        robot_label.config(image=robot_turn_inactive)
        robot_label.image = robot_turn_inactive
        user_label.config(image=your_turn_active)
        user_label.image = your_turn_active
        screen_width = root.winfo_screenwidth()
        game.player=HUMAN
        finished_button.place(x=(screen_width - finished_button.winfo_width()) // 2, y=650)

def game_screen():
    clear_widgets()

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    turns = Image.open("images/turns.png")
    robot_turn_active = Image.open("images/robot_turn_active.png")
    robot_turn_inactive = Image.open("images/robot_turn_inactive.png")
    your_turn_active = Image.open("images/your_turn_active.png")
    your_turn_inactive = Image.open("images/your_turn_inactive.png")

    turns = ImageTk.PhotoImage(turns)
    robot_turn_active = ImageTk.PhotoImage(robot_turn_active)
    robot_turn_inactive = ImageTk.PhotoImage(robot_turn_inactive)
    your_turn_active = ImageTk.PhotoImage(your_turn_active)
    your_turn_inactive = ImageTk.PhotoImage(your_turn_inactive)

    turns_label = tk.Label(root, image=turns, borderwidth=0, bg="#FFFFFF")
    turns_label.image = turns
    x_turns = (screen_width - turns.width()) // 2
    y_turns = (screen_height) // 4
    turns_label.place(x=x_turns, y=y_turns)

    robot_label = tk.Label(root, image=robot_turn_inactive, borderwidth=0, bg="#FFFFFF")
    robot_label.image = robot_turn_inactive
    robot_label.place(x=x_turns, y=y_turns + 2 * turns.height() + 10)

    user_label = tk.Label(root, image=your_turn_inactive, borderwidth=0, bg="#FFFFFF")
    user_label.image = your_turn_inactive
    user_label.place(x=x_turns, y=y_turns + 3 * turns.height() + 10)

    def resign_button_commands(root):
        levels_screen(root)
        update_robot_win_count()

    resign = Image.open("images/resign.png")
    resign = resign.resize((200, 100), Image.Resampling.LANCZOS)
    resign = ImageTk.PhotoImage(resign)
    resign_button = tk.Button(root, image=resign, command=lambda: resign_button_commands(root), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    resign_button.image = resign
    resign_button.place(x=1200, y=800)

    finished_move = Image.open("images/move_finished.png")
    finished_move = finished_move.resize((300, 150), Image.Resampling.LANCZOS)
    finished_move = ImageTk.PhotoImage(finished_move)
    finished_button = tk.Button(root, image=finished_move, command=lambda: send_move(finished_button, lambda active: update_turn(active, robot_label, user_label, robot_turn_active, robot_turn_inactive, your_turn_active, your_turn_inactive, finished_button)), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    finished_button.image = finished_move

    root.after(3000, lambda: update_turn("robot", robot_label, user_label, robot_turn_active, robot_turn_inactive, your_turn_active, your_turn_inactive, finished_button))
    root.after(6000, lambda: update_turn("user", robot_label, user_label, robot_turn_active, robot_turn_inactive, your_turn_active, your_turn_inactive, finished_button))

def assign_color(selected_color):
    #global player_color
    #player_color = selected_color
    if selected_color=="white":
        game.board.perspective=chess.WHITE
    elif selected_color=="black":
        game.board.perspective=chess.BLACK

    new_board = BoardWithOffsets(perspective=game.)
    game.reset_board(new_board, move_pieces)
    start_button()

def color_screen():
    
    clear_widgets()

    place_image("images/choose_color.png")

    color1 = Image.open("images/white.png")
    color1 = ImageTk.PhotoImage(color1)
    button1 = tk.Button(root, image=color1, command=lambda: assign_color("white"), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    button1.image = color1
    button1.place(x=(screen_width - color1.width()) // 2, y=(screen_height - color1.height()) // 2)

    color2 = Image.open("images/black.png")
    color2 = ImageTk.PhotoImage(color2)
    button2 = tk.Button(root, image=color2, command=lambda: assign_color("black"), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    button2.image = color2
    button2.place(x=(screen_width - color2.width()) // 2, y=(screen_height - color2.height()) // 2 + 200)

def start_game():
    clear_widgets()
    game_screen()
    #play_chess(level, player_color, root=root)

def add_logos():
    global logo_widgets, count_label
    logo_widgets = []

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

    def labels(img, x, y):
        label1 = tk.Label(root, image=img, borderwidth=0, bg="#FFFFFF")
        label1.image = image1
        label1.place(x, y)
        logo_widgets.append(label1)
    
    labels(image1, x1, 0)
    labels(image2, x2, 0)
    labels(image3, x3, 0)
    labels(killcount, x4, 150)

    count_label = tk.Label(root, text=str(robot_count), bg="#FFFFFF", font=("Arial", 30), fg="black")
    count_label.place(x=x4 + killcount.width() // 2 - 20, y=230)
    logo_widgets.append(count_label)

def create_empty_frame():
    frame = tk.Frame(root, bg="#FFFFFF")
    frame.pack(fill=tk.BOTH, expand=True)

def start_button():
    global button

    clear_widgets()

    image = Image.open("images/start.png")
    image = ImageTk.PhotoImage(image)

    button = tk.Button(root, image=image, command=start_game, borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    button.image = image

    x = (screen_width - image.width()) // 2
    y = (screen_height - image.height()) // 2

    button.place(x=x, y=y)

def gui_main(game_obj):
    global root, game

    game = game_obj
    root = tk.Tk()
    root.configure(bg="#FFFFFF")

    root.attributes('-fullscreen', True)
    root.attributes('-type', 'splash')

    create_empty_frame(root)
    add_logos(root)
    levels_screen(root)
    read_robot_count_from_file()
    
    root.mainloop()

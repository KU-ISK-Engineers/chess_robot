import logging
import threading
from io import BytesIO

import tkinter as tk
from PIL import Image, ImageTk
import chess
import chess.svg
import cairosvg

from src.core.game import Player

logger = logging.getLogger(__name__)

game_thread = None

#class Gui():
   # frame
   #root
   #thread
   #screens


def update_robot_win_count() -> None:
    win_count=read_robot_count_from_file()
    win_count += 1
    with open("robot_win_count.txt", "w") as file:
        file.write(str(win_count))
    
def read_robot_count_from_file() -> int:
    try:
        with open("robot_win_count.txt", "r") as file:
            content = file.read()
            if content:
                win_count = int(content)
                logger.info(f"Robot wins: {win_count}")
    except FileNotFoundError:
        win_count = 0
    return win_count

def place_img(path: str, x: float, y: float, show_for: int = None, resize_height: float = None, frame: tk.Frame = None) -> None:
    image = Image.open(path)
    if resize_height is not None:
        aspect_ratio = image.width / image.height
        new_width = int(resize_height * aspect_ratio)
        image = image.resize((new_width, resize_height), Image.Resampling.LANCZOS)
    image = ImageTk.PhotoImage(image)
    placement = frame if frame is not None else root
    label = tk.Label(placement, image=image, borderwidth=0, bg="#FFFFFF")
    label.image = image
    label.place(x=x, y=y)
    if show_for is not None:
        label.after(show_for, label.destroy)

#not used rn
def show_check_msg() -> None:
    frame = tk.Frame(root, bd=0, background="#FFFFFF")
    frame.place(x=450, y=200, width=700, height=720)
    place_img(path="images/check_msg.png", x=0, y=0, show_for=3000, frame=frame)
    clear_screen(frame)

def show_wrong_move_msg() -> None:
    frame = tk.Frame(root, bd=0, background="#FFFFFF")
    frame.place(x=450, y=200, width=500, height=500)
    place_img(path="images/wrong_move.png", x=100, y=0, show_for=2000, frame=frame)
    clear_screen(frame)
    
def clear_screen(frame:tk.Frame = None) -> None:
    for widget in frame.winfo_children():
        widget.destroy()
    if frame is not None:
        frame.destroy()

def background():
    target_height = 100

    place_img(path="images/fondas.png", x=100, y=0, resize_height=target_height)
    place_img(path="images/ku.png", x=300, y=0, resize_height=target_height)
    place_img(path="images/conexus.png", x=500, y=0, resize_height=target_height)

    place_img(path="images/killcount.png", x=50, y=150, resize_height=150)

    count_label = tk.Label(root, text=str(read_robot_count_from_file()), bg="#FFFFFF", font=("Arial", 30), fg="black")
    count_label.place(x=30, y=230)

def svg_board():
    board = game.get_chess_board()
    orientation = chess.WHITE if game.human_color == chess.WHITE else chess.BLACK

    boardsvg = chess.svg.board(board, size=640, orientation=orientation)
    png_image = cairosvg.svg2png(bytestring=boardsvg)

    place_img(path=BytesIO(png_image), x=600, y=200)

def chess_engine_thread():
    svg_board()
    while True:
        state = game.result()
        root.after(0, update_turn)

        if state != "*" or state == "resigned":
            print('Stopping game')
            return show_game_result()
        
        valid_move = None
        if game.current_player == Player.ROBOT:
            valid_move = game.robot_makes_move()
            if valid_move:
                svg_board()
        elif game.current_player == Player.HUMAN:
            move, valid = game.human_made_move()
            print(move, valid)
            if move and valid:
                svg_board()
            elif move and not valid:
                show_wrong_move_msg()


def select_level(level):
    if level == 'beginner':
        game.set_depth(2)
        game.set_skill_level(0)
    elif level == 'intermediate':
        game.set_depth(3)
        game.set_skill_level(2)
    elif level == 'advanced':
        game.set_depth(4)
        game.set_skill_level(4)
    elif level == 'hard':
        game.set_depth(6)
        game.set_skill_level(20)

    color_screen()


def place_button(path: str, x: float, y: float, frame: tk.Frame = None, resize_height: float = None, func: callable = None,  func_arg: str = None) -> None:
    image = Image.open(path)
    image = ImageTk.PhotoImage(image)
    if resize_height is not None:
        aspect_ratio = image.width / image.height
        new_width = int(resize_height * aspect_ratio)
        image = image.resize((new_width, resize_height), Image.Resampling.LANCZOS)
    placement = frame if frame is not None else root
    button = tk.Button(placement, image=image, command=lambda: func(func_arg), borderwidth=0, highlightthickness=0, relief='flat', bg="#FFFFFF")
    button.image = image
    button.place(x=x, y=y)


def level_screen():
    
    frame = tk.Frame(root, bd=0, background="#FFFFFF")
    frame.place(x=450, y=200, width=700, height=720)
    
    place_img(path="images/choose_level.png", x=0, y=0)

    place_button(path="images/beginner.png", x=0, y=150, frame=frame, func=select_level, func_arg="beginner")
    place_button(path="images/intermediate.png", x=0, y=280, frame=frame, func=select_level, func_arg="intermediate")
    place_button(path="images/advanced.png", x=0, y=400, frame=frame, func=select_level, func_arg="advanced")
    place_button(path="images/unbeatable.png", x=0, y=520, frame=frame, func=select_level, func_arg="hard")

    clear_screen(frame)

def color_screen() -> None:
    frame = tk.Frame(root, bd=0, background="#FFFFFF")
    frame.place(x=450, y=200, width=700, height=720)

    place_img(path="images/choose_color.png", x=0, y=0, frame=frame)

    place_button(path="images/white.png", x=0, y=300, func=assign_color, func_arg="white")
    place_button(path="images/black.png", x=0, y=500, func=assign_color, func_arg="black")

    clear_screen(frame)

def assign_color(selected_color: str) -> None:
    if selected_color=='white':
        game.reset_state(human_color=chess.WHITE)
    elif selected_color=='black':
        game.reset_state(human_color=chess.BLACK)                    
    game_screen()

def show_game_result():

    frame = tk.Frame(root, bd=0, background="#FFFFFF")
    frame.place(x=450, y=200, width=700, height=720)

    place_img(path="images/game_over.png", x=0, y=0, show_for=2000)

    def win_lose_message_path() -> str:
        image_path = None
        state = game.result()

        # TODO: Move human/robot win logic in game

        if state == "resigned":
            image_path = "images/you_lose.png"
            update_robot_win_count()
        elif state == "1-0":
            image_path = "images/you_won.png"
        elif state == "0-1":
            image_path = "images/you_lose.png"
            update_robot_win_count()
        elif state == "1/2-1/2":
            image_path = "images/draw.png"
        return image_path

    if win_lose_message_path():
        place_img(path=win_lose_message_path(), x=0, y=0, frame=frame)
    place_button(path="images/back.png", frame=frame, x=frame.winfo_width()//2, y=frame.winfo_height()-50, resize_height=100, func=level_screen)
    clear_screen(frame)

def update_turn():
    if game.current_player == Player.ROBOT:
        robot_label.config(image=robot_turn_active)
        robot_label.image = robot_turn_active
        user_label.config(image=your_turn_inactive)
        user_label.image = your_turn_inactive
    elif game.current_player == Player.HUMAN:
        robot_label.config(image=robot_turn_inactive)
        robot_label.image = robot_turn_inactive
        user_label.config(image=your_turn_active)
        user_label.image = your_turn_active

def game_screen():
    frame = tk.Frame(root, bd=0, background="#FFFFFF")
    frame.place(x=20, y=200, width=300, height=500)

    place_img(path="images/turns.png", frame=frame, x=0, y=300)


    global robot_label, user_label, robot_turn_active,your_turn_inactive, robot_turn_inactive,your_turn_active
    
    robot_turn_active = Image.open("images/robot_turn_active.png")
    robot_turn_inactive = Image.open("images/robot_turn_inactive.png")
    your_turn_active = Image.open("images/your_turn_active.png")
    your_turn_inactive = Image.open("images/your_turn_inactive.png")

    robot_turn_active = ImageTk.PhotoImage(robot_turn_active)
    robot_turn_inactive = ImageTk.PhotoImage(robot_turn_inactive)
    your_turn_active = ImageTk.PhotoImage(your_turn_active)
    your_turn_inactive = ImageTk.PhotoImage(your_turn_inactive)


    robot_label = tk.Label(root, image=robot_turn_inactive, borderwidth=0, bg="#FFFFFF")
    robot_label.image = robot_turn_inactive
    robot_label.place(x=x_turns, y=y_turns + 2 * turns.height() + 10)

    user_label = tk.Label(root, image=your_turn_inactive, borderwidth=0, bg="#FFFFFF")
    user_label.image = your_turn_inactive
    user_label.place(x=x_turns, y=y_turns + 3 * turns.height() + 10)

    place_button(path="images/resign.png", frame=frame, x=20, y=frame.winfo_width()-50, func=game.resign_human)



    global game_thread
    game_thread = threading.Thread(target=chess_engine_thread)
    game_thread.start()

def gui_main(game_obj, fullscreen = True, splash = True):
    global root, game
    game=game_obj

    read_robot_count_from_file()

    root = tk.Tk()
    root.configure(bg="#FFFFFF")

    root.attributes('-fullscreen', fullscreen)
    if splash:
        root.attributes('-type', 'splash')

    background()
    level_screen()

    root.mainloop()

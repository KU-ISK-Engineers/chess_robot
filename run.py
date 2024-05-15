import chess.engine
from cvlib.object_detection import YOLO
from pypylon import pylon
import argparse
import chess
import time

from src.camera import CameraDetection
from src.game import Game
from src import communication

def setup_camera():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    camera.AcquisitionFrameRateEnable.SetValue(True)
    camera.AcquisitionFrameRate.SetValue(5)
    camera.ExposureAuto.SetValue('Continuous')
    camera.AcquisitionMode.SetValue("Continuous")
    camera.PixelFormat.SetValue("RGB8")
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    return camera

def setup_yolo(weights_file, config_file, labels_file):
    return YOLO(weights_file, config_file, labels_file)

def setup_points(file_path):
    with open(file_path, 'r') as file:
        points = list(map(int, file.readline().strip().split()))
    if len(points) != 4:
        raise ValueError("Expected four integers in the file.")
    return points

def main(weights_file, config_file, labels_file, points_file, engine_path, pgn_path):
    try:
        camera = setup_camera()
        yolo = setup_yolo(weights_file, config_file, labels_file)
        points = setup_points(points_file)
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)

        detection = CameraDetection(camera, points, yolo)

        global game
        game = Game(detection, engine)

        communication.setup_communication()
        while not communication.is_available():
            print("Waiting for robot signal...")
            time.sleep(1000)

        # ----------- PGN TESTING ---    
        global root, canvas
        # Create a tkinter window
        root = tk.Tk()
        root.title("Chess Board")

        # Create a canvas to display the chess board
        canvas = tk.Canvas(root, width=BOARD_SIZE, height=BOARD_SIZE)
        canvas.pack()

        play_from_directory(pgn_path)

        root.mainloop()

    finally:
        communication.close_communication()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run chess robot.")
    parser.add_argument('--weights', type=str, default='yolov4-tiny-custom_best.weights', help='Path to YOLO weights file')
    parser.add_argument('--config', type=str, default='yolov4-tiny-custom.cfg', help='Path to YOLO config file')
    parser.add_argument('--labels', type=str, default='obj.names', help='Path to YOLO labels file')
    parser.add_argument('--points', type=str, default='points.txt', help='Path to file with points')
    parser.add_argument('--engine', type=str, default='stockfish\stockfish-windows-x86-64-avx2.exe', help='Path to stockfish engine')

    # For PGN testing
    parser.add_argument('--pgn', type=str, help='PGN directory path')

    args = parser.parse_args()

    main(args.weights, args.config, args.labels, args.points, args.engine, args.pgn)

# ------------------------------------ TESTING PGN ------------------------------------

import chess.pgn
import chess.svg
import os
import tkinter as tk
from PIL import Image, ImageTk
import io
import cairosvg
import sys
import threading

current_board = chess.Board()

# Set the dimensions of the chess board
BOARD_SIZE = 400

def display_board(board):
    # Load the SVG image of the chess board
    svg_board = chess.svg.board(board=board)
    
    # Convert SVG to PNG bytes
    png_output = io.BytesIO()
    cairosvg.svg2png(bytestring=svg_board.encode('utf-8'), write_to=png_output)
    
    # Convert PNG bytes to Image
    image = Image.open(io.BytesIO(png_output.getvalue()))

    # Resize image to fit the board
    image = image.resize((BOARD_SIZE, BOARD_SIZE), Image.BILINEAR)

    # Convert Image to Tkinter PhotoImage
    photo = ImageTk.PhotoImage(image)

    # Update the canvas with the new image
    canvas.delete("all")
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.update()


def play_from_pgn(pgn_file):
    global current_board

    game = chess.pgn.read_game(open(pgn_file))
    if not game:
        return False

    pgn_board = game.board()

    if movement.reset_board(current_board, pgn_board) == communication.RESPONSE_TIMEOUT:
       return communication.RESPONSE_TIMEOUT
    current_board = pgn_board

    nodes = iter(game.mainline())

    # Loop through the moves in the game
    def next_move(prev_response, prev_move):
        if prev_response == communication.RESPONSE_TIMEOUT:
            print('Move timeout!')
            print(current_board)
            print(prev_move)
            return communication.RESPONSE_TIMEOUT

        display_board(current_board)

        node = next(nodes)
        while node.move is None:
            node = next(nodes)

        if node.move is None:
            return communication.RESPONSE_SUCCESS

        if not current_board.is_legal(node.move):
            print('Invalid move!')
            print(current_board)
            print(node.move)
            return

        _background_move(current_board, node.move, next_move)

    next_move(communication.RESPONSE_SUCCESS, None)


def _background_move(board, move, callback):
    def thread_func():
        callback(movement.make_move(board, move), move)

    thread = threading.Thread(target=thread_func)
    thread.start()

def play_from_directory(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".pgn"):
            filepath = os.path.join(directory, filename)
            print(f"Playing game: {filename}")
            if play_from_pgn(filepath) == communication.RESPONSE_TIMEOUT:
                return communication.RESPONSE_TIMEOUT
            print("\n")  # Add a newline between games

    return communication.RESPONSE_SUCCESS

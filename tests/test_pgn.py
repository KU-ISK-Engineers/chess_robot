import chess.pgn
import chess.svg
import os
import argparse
import tkinter as tk
from PIL import Image, ImageTk
import io
import cairosvg
import sys

sys.path.append('../')

from src import communication
from src import movement

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

    # Loop through the moves in the game
    for node in game.mainline():
        if node.move is None:
            continue

        if not current_board.is_legal(node.move):
            continue

        # Visualize current position
        display_board(current_board)
        if movement.make_move(current_board, node.move) == communication.RESPONSE_TIMEOUT:
            print('Move timeout!')
            print(current_board)
            print(node.move)
            return communication.RESPONSE_TIMEOUT


        # Print the board after each move
        current_board.push(node.move)

    # Print the final board and result
    display_board(current_board)
    return communication.RESPONSE_SUCCESS


def play_from_directory(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".pgn"):
            filepath = os.path.join(directory, filename)
            print(f"Playing game: {filename}")
            if play_from_pgn(filepath) == communication.RESPONSE_TIMEOUT:
                return communication.RESPONSE_TIMEOUT
            print("\n")  # Add a newline between games

    return communication.RESPONSE_SUCCESS


def main(args):
    play_from_directory(args.path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Play out PGN files on the robot')
    parser.add_argument('path', type=str, help='PGN directory path')
    args = parser.parse_args()

    try:
        communication.setup_communication()

        # Create a tkinter window
        root = tk.Tk()
        root.title("Chess Board")

        # Create a canvas to display the chess board
        canvas = tk.Canvas(root, width=BOARD_SIZE, height=BOARD_SIZE)
        canvas.pack()

        main(args)

        # Run the tkinter event loop
        root.mainloop()
    finally:
        communication.close_communication()



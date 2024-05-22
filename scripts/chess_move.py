import chess.engine
from src.gui import update_turn


def play_chess(level, player_color):
    # Start the Stockfish engine
    engine = chess.engine.SimpleEngine.popen_uci("stockfish\stockfish-windows-x86-64-avx2.exe")

       # Start the Stockfish engine
    engine = chess.engine.SimpleEngine.popen_uci("stockfish\stockfish-windows-x86-64-avx2.exe")

    # Start a new game
    board = chess.Board()

    player_turn = chess.WHITE if player_color == "white" else chess.BLACK     #player colour input from button

    while not board.is_game_over():
        #print(board)

        if board.turn == player_turn:
            # Person's move
            while True:
                try:
                    #update_turn('user')
                    person_move = input("Enter your move (e.g., e2e4): ") #change to input from camera
                    move = chess.Move.from_uci(person_move)
                    if move in board.legal_moves:
                        board.push(move)
                        break
                    else:
                        print("Invalid move, try again.")     
                except ValueError:
                    print("Invalid move format, try again.")

        else:
            # Stockfish's move
            #update_turn('robot')
            result1 = engine.play(board, chess.engine.Limit(depth=level))
            best_move = result1.move
            board.push(best_move)

    global result
    result=board.result()     
    #print("Game Over")
    #print("Result:", board.result())
    engine.quit()
    return result

if __name__ == "__main__":
    level = input("Choose the level (beginner, intermediate, advanced, unbeatable): ").lower()
    play_chess(level)

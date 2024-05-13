import chess.engine

def get_depth(level):
    if level == "beginner":
        return 2
    elif level == "intermediate":
        return 4
    elif level == "advanced":
        return 6
    elif level == "unbeatable":
        return 20  # Or any high depth you desire
    else:
        return 4  # Default to intermediate

def play_chess(level):
    # Start the Stockfish engine
    engine = chess.engine.SimpleEngine.popen_uci("stockfish\stockfish-windows-x86-64-avx2.exe")

    # Start a new game
    board = chess.Board()

    while not board.is_game_over():
        print(board)

        if board.turn == chess.WHITE:
            # Person's move
            while True:
                try:
                    person_move = input("Enter your move (e.g., e2e4): ")
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
            result = engine.play(board, chess.engine.Limit(depth=get_depth(level)))
            best_move = result.move
            board.push(best_move)

    print("Game Over")
    print("Result:", board.result())
    engine.quit()

if __name__ == "__main__":
    level = input("Choose the level (beginner, intermediate, advanced, unbeatable): ").lower()
    play_chess(level)
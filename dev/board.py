from src.board import RealBoard, BoardDetection
from src.game import Game, ROBOT
import chess
import chess.pgn
import chess.engine
from typing import Optional, TextIO

class PGNBoardDetection(BoardDetection):
    def __init__(self, pgn: TextIO):
        pgn_game = chess.pgn.read_game(pgn)
        if not pgn_game:
            raise ValueError('Invalid pgn')

        self.board = pgn_game.board()
        self.moves = pgn_game.mainline_moves()
        self.move = iter(self.moves)
        self.game = None

    def attach_game(self, game: Game):
        self.game = game

    def capture_board(self, perspective: chess.Color = chess.WHITE) -> Optional[RealBoard]:
        if not self.game:
            raise ValueError("Cannot capture board without attaching a game.")

        game_board = self.game.chess_board()

        if self.board.fen() != game_board.fen():
            raise RuntimeError("Game board does not match pgn board")

        move = self.next_move()
        if not move:
            raise RuntimeError("No more moves remaining")

        return RealBoard(board=chess.Board(fen=self.board.fen()), perspective=perspective)

    def next_move(self) -> chess.Move:
        move = next(self.move)
        self.board.push(move)
        return move

class EngineBoardDetection(BoardDetection):
    def __init__(self, engine: chess.engine.SimpleEngine, game: Optional[Game] = None, depth: int = 4):
        self.engine = engine
        self.game = game
        self.depth = depth

    def attach_game(self, game: Game):
        self.game = game

    def capture_board(self, perspective: chess.Color = chess.WHITE) -> Optional[RealBoard]:
        if not self.game:
            raise ValueError("Cannot capture board without attaching a game.")

        board = chess.Board(fen=self.game.chess_board().fen())

        if self.game.player == ROBOT:
            return RealBoard(board=board, perspective=perspective)

        result = self.engine.play(board, chess.engine.Limit(depth=self.depth))
        move = result.move

        if not move or move not in board.legal_moves:
            move_uci = move.uci() if move else ''
            raise RuntimeError(f"Engine did not make a valid move ({move_uci}).")

        board.push(move)
        return RealBoard(board=board, perspective=perspective)


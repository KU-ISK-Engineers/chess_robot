from src.board import RealBoard, BoardDetection
from src.game import Game, ROBOT
import chess
import chess.pgn
import chess.engine
from typing import Optional

class PGNBoardDetection(BoardDetection):
    def __init__(self, pgn_file: str):
        moves = read_pgn_moves(pgn_file)
        if not moves:
            raise ValueError(f"No moves found in file {pgn_file}")

        self.moves = moves
        self.board_shown = 0
        self.current_move = 0
        self.board = chess.Board()

    def capture_board(self, perspective: chess.Color = chess.WHITE) -> RealBoard:
        self.board_shown += 1
        if self.board_shown >= 10:
            self.board_shown = 0
            self.current_move += 1

            if self.current_move >= len(self.moves):
                self.current_move = 0
                self.board = RealBoard()
            else:
                self.board.push(self.moves[self.current_move])

        return RealBoard(board=chess.Board(fen=self.board.fen()), perspective=perspective)

def read_pgn_moves(pgn_file: str) -> list[chess.Move]:
    with open(pgn_file) as pgn:
        game = chess.pgn.read_game(pgn)

    if game is None:
        return []
    
    return list(game.mainline_moves())

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


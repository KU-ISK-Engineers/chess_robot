import unittest
from dev.board import MockPGNBoardDetection
from dev.robot import patch_communication


class TestPGN(unittest.TestCase):
    def setUp(self):
        patch_communication()
        detection = MockPGNBoardDetection()
        self.game

    def test_pgn(self):
        path


if __name__ == "__main__":
    unittest.main()

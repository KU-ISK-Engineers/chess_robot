# Chess Robot

This project aims to create a robotic hand that can automatically play chess with a person on a physical chessboard, without any virtual interaction—just hands, no mouse or keyboard needed.

## Project Overview

Project uses a camera system and an object detection model to recognize and validate chess moves.

When a valid move is detected, the system calculates the optimal move using a chess engine and sends the appropriate command to the robotic hand, which physically performs the move on the chessboard.

This repository contains code for detecting and validating chess moves using object detection models, a user interface that displays the current game state, and command communication with the robotic hand to execute moves.

### Logic

1. **Move Detection and Validation**: At regular intervals, a camera system captures images of the board. Yolov8 object detection model identifies the locations of pieces and creates a virtual board representation. This current state is compared to the previous game state stored in memory to determine the player’s move. Each move is validated against chess rules to ensure only legal moves receive a response.

2. **Command Issuing**: Once a valid move is detected, the system calculates the sequence of physical actions (where to pick up and place pieces) and issues commands to the robotic hand. Certain moves, like captures or promotions, require multiple commands to be expressed.

3. **Physical Piece Movement**: The robotic hand moves pieces on the chessboard by executing commands that specify coordinates for each move. It can transfer pieces from one square to another and handle actions such as removing captured pieces from the board or placing them back on if needed.

4. **Game Controls and Visualization**: The user interface allows the player to resign, see the virtual board of the game, and receive feedback such as “Invalid Move” notifications. All gameplay takes place on the physical chessboard, with the interface serving as a visual and control tool.

## Prerequisites

- **Basler Camera** with the Basler Pylon SDK installed.
- **Python 3.x** and dependencies listed in `requirements.txt`.

## Installation and Running

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/np425/chess_robot_opencv
   cd chess_robot_opencv
   ```

2. **Install Dependencies**:
   Ensure the Basler Pylon SDK is installed, then install the remaining dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   Start the application:
   ```bash
   python run.py
   ```

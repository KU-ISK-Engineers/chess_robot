import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

import random
import logging
global player_win_count, robot_win_count

def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def game_over(frame, outcome):   #outcome-winning or losing
    clear_frame(frame)
    #game_over.png, buton 'home'
    if(outcome==win):
        #you_won.png#
        player_win_count+=1
    elif (outcome==lose):
        #you_lose.png
        robot_win_count+=1

def resign():
    clear_frame(frame)
    #message 'you resigned'
    #return to home page
    robot_win_count+=1

def level_choice():
    ...


    

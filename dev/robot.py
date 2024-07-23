from src import robot
import logging
import time

delay = 0


def issue_command(command: str, timeout_max=robot.DELAY_TIMEOUT) -> int:
    time.sleep(delay)
    return robot.COMMAND_SUCCESS


def patch_communication(new_delay: float = 0):
    global delay
    delay = new_delay

    logging.info(f"Replaced robot communication function with mock function, delay {delay} s")
    robot.issue_command = issue_command


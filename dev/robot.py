from src.communication import tcp_robot
import logging
import time

delay = 0


def issue_command(command: str, timeout_max=tcp_robot.DELAY_TIMEOUT) -> int:
    time.sleep(delay)
    return tcp_robot.COMMAND_SUCCESS


def patch_communication(new_delay: float = 0):
    global delay
    delay = new_delay

    logging.info(f"Replaced robot communication function with mock function, delay {delay} s")
    tcp_robot.issue_command = issue_command


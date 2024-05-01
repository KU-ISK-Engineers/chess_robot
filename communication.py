import RPi.GPIO as GPIO
import logging
import time

# Pin configuration
_PIN_OUT_DAT = 11
_PIN_OUT_CLK = 13
_PIN_IN_RESP = 15

# Delay configuration
_DELAY_TIMEOUT_S = 10
_DELAY_WAIT_S = 0.5

# Signal waiting return values
RESPONSE_TIMEOUT = 0
RESPONSE_SUCCESS = 1

def setup_communication():
    logging.info("Setting up GPIO pins...")

    GPIO.setmode(GPIO.BOARD)

    # Pin directions
    GPIO.setup(_PIN_OUT_CLK, GPIO.OUT)
    GPIO.setup(_PIN_OUT_DAT, GPIO.OUT)
    GPIO.setup(_PIN_IN_RESP, GPIO.IN)

    # Initial values
    GPIO.output(_PIN_OUT_CLK, GPIO.LOW)
    GPIO.output(_PIN_OUT_DAT, GPIO.LOW)

def close_communication():
    logging.info("Cleaning up GPIO pins...")

    GPIO.cleanup()

def _send_command(command):
    # 16 bits command
    for bit in range(16):
        bit_value = (command >> (15 - bit)) & 1

        GPIO.output(_PIN_OUT_DAT, GPIO.HIGH if bit_value else GPIO.LOW)
        
        # Toggle the clock to signal data is ready
        GPIO.output(_PIN_OUT_CLK, GPIO.HIGH)
        time.sleep(0.0001)    
        GPIO.output(_PIN_OUT_CLK, GPIO.LOW)
        time.sleep(0.0001)    

    # Wait for signal
    time_started = time.time()

    while time.time() - time_started < _DELAY_TIMEOUT_S:
        signal = GPIO.input(_PIN_IN_RESP)
        # Wait for low signal
        if signal == GPIO.LOW:
            return RESPONSE_SUCCESS
        time.sleep(_DELAY_WAIT_S)

    return RESPONSE_TIMEOUT



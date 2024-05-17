import RPi.GPIO as GPIO
import logging
import time

# Pin configuration
PIN_IN_RESP = 15

def setup_gpio():
    logging.info("Setting up GPIO pins...")
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(PIN_IN_RESP, GPIO.IN)

def cleanup_gpio():
    logging.info("Cleaning up GPIO pins...")
    GPIO.cleanup()

def detect_pin_state():
    logging.info(f"Monitoring pin {PIN_IN_RESP} for state changes...")
    try:
        while True:
            pin_state = GPIO.input(PIN_IN_RESP)
            if pin_state == GPIO.HIGH:
                logging.info("Pin 15 is HIGH")
            else:
                logging.info("Pin 15 is LOW")
            time.sleep(1)  # Adjust the sleep time as needed for your application
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")

def main():
    logging.basicConfig(level=logging.INFO)
    setup_gpio()
    try:
        detect_pin_state()
    finally:
        cleanup_gpio()

if __name__ == "__main__":
    main()

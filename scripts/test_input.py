import RPi.GPIO as GPIO
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def setup_gpio():
    logging.info("Setting up GPIO pins...")
    GPIO.setmode(GPIO.BOARD)  # Use BCM GPIO numbering
    GPIO.setwarnings(False)

def cleanup_gpio():
    logging.info("Cleaning up GPIO pins...")
    GPIO.cleanup()

def detect_pin_states(pins):
    logging.info("Monitoring all GPIO pins for state changes...")
    try:
        while True:
            for pin in pins:
                try:
                    pin_state = GPIO.input(pin)
                    state_str = "HIGH" if pin_state == GPIO.HIGH else "LOW"
                    logging.info(f"Pin {pin} is {state_str}")
                except Exception as e:
                    logging.warning(f"Failed to read pin {pin}: {e}")
            time.sleep(1)  # Adjust the sleep time as needed for your application
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")

def main():
    setup_gpio()
    # Define a list of pins to monitor. Update the list based on your specific Raspberry Pi model.
    pins = list(range(2, 28))  # GPIO2 to GPIO27

    try:
        # Set all pins as inputs
        for pin in pins:
            try:
                GPIO.setup(pin, GPIO.IN)
                logging.info(f"Successfully set pin {pin} as input")
            except Exception as e:
                logging.error(f"Failed to set pin {pin} as input: {e}")

        detect_pin_states(pins)
    finally:
        cleanup_gpio()

if __name__ == "__main__":
    main()

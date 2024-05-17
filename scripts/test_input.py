import gpiod
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

def setup_gpio(chip_name='gpiochip0'):
    logging.info("Setting up GPIO pins...")
    chip = gpiod.Chip(chip_name)
    return chip

def cleanup_gpio(chip):
    logging.info("Cleaning up GPIO pins...")
    chip.close()

def detect_pin_states(chip, lines):
    logging.info("Monitoring all GPIO pins for state changes...")
    try:
        while True:
            for line in lines:
                try:
                    pin_state = line.get_value()
                    state_str = "HIGH" if pin_state == 1 else "LOW"
                    logging.info(f"Pin {line.offset} is {state_str}")
                except Exception as e:
                    logging.warning(f"Failed to read pin {line.offset}: {e}")
            time.sleep(1)  # Adjust the sleep time as needed for your application
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")

def main():
    chip = setup_gpio()
    # Define a list of pins to monitor. Update the list based on your specific Raspberry Pi model.
    pins = list(range(2, 28))  # GPIO2 to GPIO27
    try:
        # Claim all pins as inputs
        lines = [chip.get_line(pin) for pin in pins]
        for line in lines:
            line.request(consumer='gpio_monitor', type=gpiod.LINE_REQ_DIR_IN)
        detect_pin_states(chip, lines)
    finally:
        cleanup_gpio(chip)

if __name__ == "__main__":
    main()

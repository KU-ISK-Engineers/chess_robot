import lgpio
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

def setup_gpio():
    logging.info("Setting up GPIO pins...")
    h = lgpio.gpiochip_open(0)
    return h

def cleanup_gpio(h):
    logging.info("Cleaning up GPIO pins...")
    lgpio.gpiochip_close(h)

def detect_pin_states(h, pins):
    logging.info("Monitoring all GPIO pins for state changes...")
    try:
        while True:
            for pin in pins:
                try:
                    pin_state = lgpio.gpio_read(h, pin)
                    state_str = "HIGH" if pin_state == 1 else "LOW"
                    logging.info(f"Pin {pin} is {state_str}")
                except Exception as e:
                    logging.warning(f"Failed to read pin {pin}: {e}")
            time.sleep(1)  # Adjust the sleep time as needed for your application
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")

def main():
    h = setup_gpio()
    # Define a list of pins to monitor. Update the list based on your specific Raspberry Pi model.
    pins = list(range(2, 28))  # GPIO2 to GPIO27
    try:
        # Claim all pins as inputs
        for pin in pins:
            lgpio.gpio_claim_input(h, pin)
        detect_pin_states(h, pins)
    finally:
        cleanup_gpio(h)

if __name__ == "__main__":
    main()

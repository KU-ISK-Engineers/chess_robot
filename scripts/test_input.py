import lgpio
import logging
import time

# Pin configuration
PIN_IN_RESP = 15

def setup_gpio():
    logging.info("Setting up GPIO pins...")
    h = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_input(h, PIN_IN_RESP)
    return h

def cleanup_gpio(h):
    logging.info("Cleaning up GPIO pins...")
    lgpio.gpiochip_close(h)

def detect_pin_state(h):
    logging.info(f"Monitoring pin {PIN_IN_RESP} for state changes...")
    try:
        while True:
            pin_state = lgpio.gpio_read(h, PIN_IN_RESP)
            if pin_state == 1:
                logging.info("Pin 15 is HIGH")
            else:
                logging.info("Pin 15 is LOW")
            time.sleep(1)  # Adjust the sleep time as needed for your application
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")

def main():
    logging.basicConfig(level=logging.INFO)
    h = setup_gpio()
    try:
        detect_pin_state(h)
    finally:
        cleanup_gpio(h)

if __name__ == "__main__":
    main()

import pigpio
import time
import argparse

DAT = 23
CLK = 27
RESP = 17

def main():
    parser = argparse.ArgumentParser(description="Control GPIO pins on a remote Raspberry Pi.")
    parser.add_argument('ip_address', type=str, help='IP address of the remote Raspberry Pi')
    parser.add_argument('gpio_pin', type=int, help='GPIO pin number to control')

    args = parser.parse_args()

    # Connect to the remote Raspberry Pi
    pi = pigpio.pi(args.ip_address)

    if not pi.connected:
        print("Failed to connect to remote Raspberry Pi")
    else:
        print(f"Connected to remote Raspberry Pi at {args.ip_address}")

        # Set the specified GPIO pin as an output and toggle it
        # gpio_pin = args.gpio_pin
        # pi.set_mode(gpio_pin, pigpio.OUTPUT)

        # # Turn on the pin
        # pi.write(gpio_pin, 1)
        # print(f"GPIO {gpio_pin} is on")
        
        # # Wait for a few seconds
        # time.sleep(5)
        
        # # Turn off the pin
        # pi.write(gpio_pin, 0)
        # print(f"GPIO {gpio_pin} is off")

        # # Stop the connection
        # pi.stop()

if __name__ == '__main__':
    main()

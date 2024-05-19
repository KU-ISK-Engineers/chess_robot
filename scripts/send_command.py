import sys
import time
import subprocess

def to_8bit_binary(num):
    """Convert a signed integer to an 8-bit binary representation."""
    if num < 0:
        num = (1 << 8) + num
    return format(num, '08b')

def pinctrl_set(pin, value):
    """Set the pin value using pinctrl."""
    subprocess.run(['pinctrl', 'set', str(pin), value])

def main():
    if len(sys.argv) != 3:
        print("Usage: send_command.py <square_from> <square_to>")
        sys.exit(1)

    square_from = int(sys.argv[1])
    square_to = int(sys.argv[2])

    bin_square_from = to_8bit_binary(square_from)
    bin_square_to = to_8bit_binary(square_to)

    combined_command = bin_square_from + bin_square_to

    for bit in combined_command:
        bit_value = 'dh' if bit == '1' else 'dl'
        pinctrl_set(17, bit_value)
        pinctrl_set(27, 'dh')
        time.sleep(0.05)
        pinctrl_set(27, 'dl')
        time.sleep(0.05)

if __name__ == '__main__':
    main()

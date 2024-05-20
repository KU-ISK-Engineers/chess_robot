import paramiko
import argparse
import time
import os

def create_remote_script_content(gpio_chip, gpio_pin):
    script_content = f"""
import gpiod
import time

def control_gpio(gpio_chip, gpio_pin):
    chip = gpiod.Chip(gpio_chip)
    line = chip.get_line(gpio_pin)
    line.request(consumer='gpiod', type=gpiod.LINE_REQ_DIR_OUT)
    line.set_value(1)
    print(f"GPIO {{gpio_pin}} is on")
    time.sleep(5)
    line.set_value(0)
    print(f"GPIO {{gpio_pin}} is off")
    line.release()

if __name__ == "__main__":
    control_gpio('{gpio_chip}', {gpio_pin})
"""
    return script_content

def upload_script_if_not_exists_or_differs(ssh, username, gpio_chip, gpio_pin):
    remote_script_path = f"/home/{username}/control_gpio.py"
    script_content = create_remote_script_content(gpio_chip, gpio_pin)

    try:
        sftp = ssh.open_sftp()
        try:
            with sftp.open(remote_script_path, 'r') as remote_file:
                remote_content = remote_file.read().decode()
            if remote_content == script_content:
                print("Remote script is up-to-date.")
                return
            else:
                print("Remote script differs. Updating...")
        except FileNotFoundError:
            print("Remote script does not exist. Uploading...")
        
        with sftp.open(remote_script_path, 'w') as remote_file:
            remote_file.write(script_content)
        sftp.chmod(remote_script_path, 0o755)
        print("Remote script updated.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        sftp.close()

def execute_remote_command(ip_address, username, password, gpio_chip, gpio_pin):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip_address, username=username, password=password)

    upload_script_if_not_exists_or_differs(ssh, username, gpio_chip, gpio_pin)

    remote_script_path = f"/home/{username}/control_gpio.py"
    command = f'python3 {remote_script_path}'
    stdin, stdout, stderr = ssh.exec_command(command)
    print(stdout.read().decode())
    print(stderr.read().decode())

    ssh.close()

def main():
    parser = argparse.ArgumentParser(description="Control GPIO pins on a remote Raspberry Pi via SSH.")
    parser.add_argument('ip_address', type=str, help='IP address of the remote Raspberry Pi')
    parser.add_argument('gpio_chip', type=str, help='GPIO chip, usually "/dev/gpiochip0"')
    parser.add_argument('gpio_pin', type=int, help='GPIO pin number to control')
    parser.add_argument('username', type=str, help='Username for SSH')
    parser.add_argument('password', type=str, help='Password for SSH')
    args = parser.parse_args()

    execute_remote_command(args.ip_address, args.username, args.password, args.gpio_chip, args.gpio_pin)

if __name__ == '__main__':
    main()

from machine import Pin, I2C
import time

# I2C Configuration
I2C_ADDR = 0x0C  # Default I2C address of MLX90393
i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=50000)  # Lowered I2C frequency to 50 kHz

# Interrupt Pin Configuration
int_pin = Pin(1, Pin.IN, Pin.PULL_UP)  # GPIO1 as interrupt pin

# MLX90393 Commands
CMD_RESET = 0x60
CMD_START_MEASUREMENT = 0x3E
CMD_READ_MEASUREMENT = 0x4E
CMD_EXIT = 0x80

def scan_i2c_bus():
    """Scan the I2C bus for connected devices."""
    devices = i2c.scan()
    if devices:
        print("I2C devices found:", [hex(device) for device in devices])
    else:
        print("No I2C devices detected. Check wiring!")

def send_command(command, retries=5):
    """Send a command to the MLX90393 sensor with retry on timeout."""
    for attempt in range(retries):
        try:
            i2c.writeto(I2C_ADDR, bytes([command]))
            return
        except OSError as e:
            print(f"Attempt {attempt + 1}: Failed to send command {hex(command)}: {e}")
            time.sleep(0.5)  # Delay before retry
    raise OSError("Failed to communicate with MLX90393 after retries.")

def read_data(length, retries=5):
    """Read data from the MLX90393 sensor with retry on timeout."""
    for attempt in range(retries):
        try:
            return i2c.readfrom(I2C_ADDR, length)
        except OSError as e:
            print(f"Attempt {attempt + 1}: Failed to read data: {e}")
            time.sleep(0.5)
    raise OSError("Failed to read data from MLX90393 after retries.")

def reset_sensor():
    """Reset the MLX90393 sensor."""
    print("Resetting sensor...")
    send_command(CMD_RESET)
    time.sleep(0.5)  # Wait for reset to complete

def start_measurement():
    """Start a single measurement."""
    send_command(CMD_START_MEASUREMENT)
    time.sleep(0.1)  # Allow sensor to process before the next command

def read_measurement():
    """Read the measurement data."""
    send_command(CMD_READ_MEASUREMENT)
    return read_data(7)  # MLX90393 returns 7 bytes

def process_data(data):
    """Process raw measurement data into magnetic field values."""
    raw_x = (data[1] << 8) | data[2]
    raw_y = (data[3] << 8) | data[4]
    raw_z = (data[5] << 8) | data[6]
    # Convert raw values to magnetic field strength (adjust scale factor if needed)
    x = raw_x * 0.1
    y = raw_y * 0.1
    z = raw_z * 0.1
    return x, y, z

def interrupt_handler(pin):
    """Interrupt handler for data ready signal."""
    print("Interrupt triggered: Data ready!")
    try:
        data = read_measurement()
        x, y, z = process_data(data)
        print(f"X: {x:.2f} uT")  # Print X on a separate line
        print(f"Y: {y:.2f} uT")  # Print Y on a separate line
        print(f"Z: {z:.2f} uT")  # Print Z on a separate line
    except Exception as e:
        print(f"Error in interrupt handler: {e}")

# Attach the interrupt handler to the INT/DRDY pin
int_pin.irq(trigger=Pin.IRQ_FALLING, handler=interrupt_handler)

# Main Function
def main():
    print("Scanning I2C bus...")
    scan_i2c_bus()

    print("Initializing MLX90393...")
    try:
        reset_sensor()
        print("Sensor initialized. Waiting for data...")
    except Exception as e:
        print(f"Initialization failed: {e}")
        return

    # Main loop
    try:
        while True:
            try:
                start_measurement()
                time.sleep(0.5)  # Delay to avoid overwhelming the sensor
            except OSError as e:
                print(f"Error starting measurement: {e}")
    except KeyboardInterrupt:
        print("Exiting...")
        send_command(CMD_EXIT)

# Run the main function
main()


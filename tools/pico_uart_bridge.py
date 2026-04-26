from machine import UART, Pin
import sys
import time

uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# Buffer for line-based parsing
line_buffer = bytearray()
boot_complete = False
thermal_reported = False


def safe_write(data):
    for b in data:
        if b in (9, 10, 13) or 32 <= b < 127:
            sys.stdout.write(chr(b))
        else:
            sys.stdout.write("\\x{:02x}".format(b))


def send_command(cmd):
    uart.write(cmd + "\n")
    time.sleep_ms(100)


def check_boot_complete(data_str):
    global boot_complete
    indicators = [
        "login:",
        "root@",
        "# ",
        "~#",
        "debian@",
        "ubuntu@",
        "orangepi@",
    ]
    for indicator in indicators:
        if indicator in data_str:
            boot_complete = True
            return True
    return False


def report_thermal():
    global thermal_reported
    if thermal_reported:
        return
    thermal_reported = True

    print("\n" + "=" * 60)
    print("THERMAL REPORT - Auto-generated")
    print("=" * 60)

    # Send thermal zone listing
    send_command("cat /sys/class/thermal/thermal_zone*/type 2>/dev/null")
    time.sleep_ms(200)

    # Send temperature readings
    send_command("cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null")
    time.sleep_ms(200)

    # Send CPU frequency info
    send_command(
        "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq 2>/dev/null"
    )
    time.sleep_ms(200)

    # Send uptime
    send_command("cat /proc/uptime")
    time.sleep_ms(200)

    print("=" * 60)
    print("End of thermal report")
    print("=" * 60 + "\n")


print("\nOrange Pi 4 Pro - Smart UART Bridge")
print("Baudrate: 115200")
print("Features: Boot detection, Auto-thermal report")
print("-" * 60 + "\n")

# Small delay to let USB serial stabilize
time.sleep_ms(500)

while True:
    if uart.any():
        data = uart.read(256)
        if data:
            # Parse for boot completion
            for b in data:
                line_buffer.append(b)
                if b == 10:  # newline
                    try:
                        line_str = line_buffer.decode("utf-8", errors="replace")
                        check_boot_complete(line_str)
                    except:
                        pass
                    line_buffer = bytearray()

            safe_write(data)

    # If boot just completed, trigger thermal report
    if boot_complete and not thermal_reported:
        time.sleep_ms(500)  # Give shell time to settle
        report_thermal()

    time.sleep_ms(2)

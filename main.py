# Updated main.py (MicroPython)
# Based on your uploaded file. Only communication layer changed (added TCP).
# Keep all your functions and pin definitions unchanged.

import machine
import network
import time

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# ---------------------------
# --- PINS / PWM / LOGIC ---
# ---------------------------
# (I kept your exact pin setup and functions — not changed)
M1_FW = machine.Pin(13, machine.Pin.OUT)
M1_BW = machine.Pin(12, machine.Pin.OUT)
M2_FW = machine.Pin(27, machine.Pin.OUT)
M2_BW = machine.Pin(14, machine.Pin.OUT)
M3_FW = machine.Pin(16, machine.Pin.OUT)
M3_BW = machine.Pin(17, machine.Pin.OUT)
M4_FW = machine.Pin(18, machine.Pin.OUT)
M4_BW = machine.Pin(19, machine.Pin.OUT)

PWM_FREQ = 1000
pwm_speed = 512

M5_FW_PWM = machine.PWM(machine.Pin(21), freq=PWM_FREQ, duty=0)
M5_BW_PWM = machine.PWM(machine.Pin(22), freq=PWM_FREQ, duty=0)
M6_FW_PWM = machine.PWM(machine.Pin(23), freq=PWM_FREQ, duty=0)
M6_BW_PWM = machine.PWM(machine.Pin(25), freq=PWM_FREQ, duty=0)

LED_PIN = machine.Pin(2, machine.Pin.OUT)

CHASSIS_PINS = [
    M1_FW, M1_BW, M2_FW, M2_BW, M3_FW, M3_BW, M4_FW, M4_BW
]
PWM_MOTOR_PINS = [M5_FW_PWM, M5_BW_PWM, M6_FW_PWM, M6_BW_PWM]

def stop_all_chassis():
    for pin in CHASSIS_PINS:
        pin.off()

def stop_all_pwm():
    for pwm_pin in PWM_MOTOR_PINS:
        pwm_pin.duty(0)

def stop_all():
    stop_all_chassis()
    stop_all_pwm()
    LED_PIN.off()
    print("Acción: DETENER TODO")

def move_forward():
    stop_all_chassis()
    M1_FW.on(); M2_FW.on(); M3_FW.on(); M4_FW.on()
    print("Acción: Mover Adelante")

def move_backward():
    stop_all_chassis()
    M1_BW.on(); M2_BW.on(); M3_BW.on(); M4_BW.on()
    print("Acción: Mover Atrás")

def turn_left():
    stop_all_chassis()
    M1_BW.on(); M3_BW.on()
    M2_FW.on(); M4_FW.on()
    print("Acción: Girar Izquierda")

def turn_right():
    stop_all_chassis()
    M1_FW.on(); M3_FW.on()
    M2_BW.on(); M4_BW.on()
    print("Acción: Girar Derecha")

async def forklift_up(duration_s=3):
    stop_all_pwm()
    await asyncio.sleep_ms(50)
    print(f"Acción: Subiendo montacargas (Velocidad: {pwm_speed})...")
    M5_FW_PWM.duty(pwm_speed)
    await asyncio.sleep(duration_s)
    M5_FW_PWM.duty(0)
    print("Acción: Montacargas detenido.")

async def forklift_down(duration_s=3):
    stop_all_pwm()
    await asyncio.sleep_ms(50)
    print(f"Acción: Bajando montacargas (Velocidad: {pwm_speed})...")
    M5_BW_PWM.duty(pwm_speed)
    await asyncio.sleep(duration_s)
    M5_BW_PWM.duty(0)
    print("Acción: Montacargas detenido.")

async def camera_rotate_a(duration_s=1):
    stop_all_pwm()
    await asyncio.sleep_ms(50)
    print(f"Acción: Rotando cámara A (Velocidad: {pwm_speed})...")
    M6_FW_PWM.duty(pwm_speed)
    await asyncio.sleep(duration_s)
    M6_FW_PWM.duty(0)
    print("Acción: Cámara detenida.")

async def camera_rotate_b(duration_s=1):
    stop_all_pwm()
    await asyncio.sleep_ms(50)
    print(f"Acción: Rotando cámara B (Velocidad: {pwm_speed})...")
    M6_BW_PWM.duty(pwm_speed)
    await asyncio.sleep(duration_s)
    M6_BW_PWM.duty(0)
    print("Acción: Cámara detenida.")

def led_on():
    LED_PIN.on()
    print("Acción: LED ON")

def led_off():
    LED_PIN.off()
    print("Acción: LED OFF")

# ---------------------------
# --- WiFi connect (unchanged) ---
# ---------------------------
def connect_to_wifi(ssid, password, timeout_s=15):
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    if not sta_if.isconnected():
        print(f"Conectando a la red WiFi '{ssid}'...")
        sta_if.connect(ssid, password)
        start_time = time.time()
        while not sta_if.isconnected():
            if time.time() - start_time > timeout_s:
                print(f"\n⏰ Timeout: No se pudo conectar a WiFi en {timeout_s}s.")
                sta_if.active(False)
                return None
            print(".", end="")
            time.sleep(1)
    ip_address = sta_if.ifconfig()[0]
    print(f"\n✅ Conectado a WiFi. Dirección IP: {ip_address}")
    return ip_address

# ---------------------------
# --- Existing HTTP page (unchanged) ---
# ---------------------------
HTML_PAGE = """(your same HTML page here)"""
# For brevity I'm not repeating the whole HTML string in this paste,
# but when you deploy, keep the same HTML_PAGE content you already had.

# ---------------------------
# --- Existing async HTTP handler (kept) ---
# ---------------------------
async def handle_client(reader, writer):
    global pwm_speed
    print("HTTP client connected.")
    try:
        request_line = await reader.readline()
        request_str = request_line.decode('utf-8')
        parts = request_str.split()
        if len(parts) < 2:
            writer.close()
            await writer.wait_closed()
            return
        full_path = parts[1]
        path_parts = full_path.split('?')
        request_path = path_parts[0]
        query_string = path_parts[1] if len(path_parts) > 1 else ''
        while await reader.readline() != b"\r\n": pass

        sync_commands = {
            '/forward': move_forward,
            '/backward': move_backward,
            '/left': turn_left,
            '/right': turn_right,
            '/stop_chassis': stop_all_chassis,
            '/stop': stop_all,
            '/led_on': led_on,
            '/led_off': led_off
        }
        async_commands = {
            '/forklift_up': forklift_up,
            '/forklift_down': forklift_down,
            '/cam_a': camera_rotate_a,
            '/cam_b': camera_rotate_b
        }

        writer.write(b'HTTP/1.1 200 OK\r\n')
        writer.write(b'Content-Type: text/html\r\n')
        writer.write(b'Connection: close\r\n\r\n')

        if request_path == '/':
            writer.write(HTML_PAGE.encode('utf-8'))
        elif request_path in sync_commands:
            sync_commands[request_path]()
        elif request_path in async_commands:
            asyncio.create_task(async_commands[request_path]())
        elif request_path == '/set_speed' and 'value=' in query_string:
            try:
                speed_val = int(query_string.split('=')[1])
                if 0 <= speed_val <= 1023:
                    pwm_speed = speed_val
                    print(f"Velocidad PWM actualizada a: {pwm_speed}")
            except ValueError:
                print("Error: Valor de velocidad inválido.")

        await writer.drain()

    except Exception as e:
        print("⚠️ Error handling HTTP client:", e)
    finally:
        writer.close()
        await writer.wait_closed()
        print("HTTP client disconnected.")

# ---------------------------
# --- NEW: TCP handler for the Android app (line-based) ---
# ---------------------------
async def handle_tcp_client(reader, writer):
    """
    Very small line-based protocol. The Android app connects and sends
    newline-terminated commands like:
      forward
      left
      set_speed:512
    The ESP parses and executes them.
    """
    global pwm_speed
    peer = None
    try:
        # get peer addr if available
        try:
            peer = writer.get_extra_info('peername')
        except:
            peer = None
        print("TCP client connected.", peer)

        while True:
            line = await reader.readline()
            if not line:
                break
            cmd_line = line.decode('utf-8').strip()
            if cmd_line == "":
                continue
            print("TCP RECV:", cmd_line)

            # parse set_speed:512  or set_speed=512
            if ':' in cmd_line:
                cmd, val = cmd_line.split(':', 1)
            elif '=' in cmd_line:
                cmd, val = cmd_line.split('=', 1)
            else:
                cmd, val = cmd_line, None

            # synchronous commands (immediate)
            if cmd == 'forward':
                move_forward()
            elif cmd == 'backward':
                move_backward()
            elif cmd == 'left':
                turn_left()
            elif cmd == 'right':
                turn_right()
            elif cmd == 'stop_chassis':
                stop_all_chassis()
            elif cmd == 'stop':
                stop_all()
            elif cmd == 'led_on':
                led_on()
            elif cmd == 'led_off':
                led_off()
            elif cmd == 'set_speed' and val is not None:
                try:
                    speed_val = int(val)
                    if 0 <= speed_val <= 1023:
                        pwm_speed = speed_val
                        print("Velocidad PWM actualizada a:", pwm_speed)
                except:
                    print("Invalid speed value:", val)
            # async commands
            elif cmd == 'forklift_up':
                asyncio.create_task(forklift_up())
            elif cmd == 'forklift_down':
                asyncio.create_task(forklift_down())
            elif cmd == 'cam_a':
                asyncio.create_task(camera_rotate_a())
            elif cmd == 'cam_b':
                asyncio.create_task(camera_rotate_b())
            else:
                print("Comando desconocido:", cmd_line)

            # send a short acknowledgement back (optional)
            try:
                writer.write(("OK\n").encode('utf-8'))
                await writer.drain()
            except Exception as e:
                print("Err writing ACK:", e)

    except Exception as e:
        print("⚠️ Error in TCP handler:", e)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass
        print("TCP client disconnected.", peer)

# ---------------------------
# --- Main: starts both HTTP and TCP servers ---
# ---------------------------
async def main():
    stop_all()

    WIFI_SSID = "Rescue-BOT"
    WIFI_PASS = "0123456789"

    ip_address = connect_to_wifi(WIFI_SSID, WIFI_PASS, timeout_s=15)
    if not ip_address:
        print("Error: cannot join WiFi.")
        return

    print("Open browser to http://%s (HTTP control still available)" % ip_address)
    print("Or connect with the Android app to port 12345 (TCP)")

    try:
        http_server = await asyncio.start_server(handle_client, "0.0.0.0", 80)
        tcp_server = await asyncio.start_server(handle_tcp_client, "0.0.0.0", 12345)
        print("✅ HTTP server started on :80 and TCP server on :12345")
        while True:
            await asyncio.sleep(5)
    except Exception as e:
        print("🚨 Server error:", e)
    finally:
        stop_all()
        print("Servers stopped - all motors turned off.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        stop_all()
        asyncio.new_event_loop()

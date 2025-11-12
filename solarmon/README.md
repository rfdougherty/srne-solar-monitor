# Solar Monitor - Modbus RTU-to-TCP Bridge

An Arduino IDE sketch for ESP32 that creates a Modbus RTU-to-TCP bridge, allowing SRNE solar inverters to be accessed over WiFi via Modbus TCP. This enables the Python monitoring script (`save_influx.py`) to communicate with the inverter without direct RS485 connections.

This code is heavily based on the eModbus Modbus bridge example.

## Hardware Requirements

- **Board**: XIAO ESP32S3
- **RS485 Interface**:
  - RX = GPIO9 (D10 on XIAO ESP32S3)
  - TX = GPIO8 (D09 on XIAO ESP32S3)
- **Status LED**: GPIO21 (LED_BUILTIN on XIAO ESP32S3)
- **RS485 Transceiver**: HiLetgo TTL to RS485 485 to Serial UART board (or similar MAX485-based module)
- **WiFi**: 2.4 GHz WiFi network
- **Power Supply**: 48V to 12V buck converter (20A) + 12V to 5V step-down circuit

## Hardware Connections

### RS485 Interface

This project uses a **HiLetgo TTL to RS485 485 to Serial UART board** to interface between the ESP32 and the inverter's RS485 port. An old Ethernet cable was repurposed to connect the RS485 board to the inverter's RS485 port.

**RS485 Wiring:**

- Connect the RS485 board's RX/TX pins to the ESP32 (RX=GPIO9, TX=GPIO8)
- Connect the RS485 board's A/B terminals to the inverter's RS485 port via the Ethernet cable
- Ensure proper ground connection between all components

### Power Supply

The system is powered directly from the 48V battery bank:

1. **48V to 12V Conversion**: A 20A 48V to 12V buck converter ([Amazon](https://www.amazon.com/dp/B0DLFVSYMB)) provides an efficient 12V power bus that avoids using the inverter for DC power
2. **12V to 5V Conversion**: A small 12V to 5V step-down circuit powers the ESP32 board
3. **Power Chain**: 48V Battery → 48V/12V Buck Converter → 12V/5V Circuit → ESP32

**Important**: Ensure all power converters are properly rated for your system's current requirements and include appropriate fusing for safety.

## Software Requirements

### Arduino IDE Setup

1. **Install Arduino IDE** (version 1.8.x or 2.x)

2. **Install ESP32 Board Support**:
   - Go to File → Preferences
   - Add to Additional Board Manager URLs: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Go to Tools → Board → Boards Manager
   - Search for "ESP32" and install "esp32 by Espressif Systems"

3. **Install Required Libraries**:
   - Go to Sketch → Include Library → Manage Libraries
   - Install the following:
     - **eModbus** (by eModbus)
     - **ArduinoOTA** (usually included with ESP32 board support)
     - **Streaming** (by Mikal Hart)

4. **Select Board**:
   - Tools → Board → ESP32 Arduino → XIAO_ESP32S3

## Configuration

### WiFi Credentials

Edit `solarmon.ino` and define your WiFi credentials before compiling:

```cpp
#define MY_SSID "your_wifi_ssid"
#define MY_PASS "your_wifi_password"
```

Alternatively, you can define these in the Arduino IDE's build flags or use PlatformIO's build environment.

### Network Settings

The default configuration:

- **Modbus TCP Port**: 502
- **IP Address**: Assigned via DHCP (check Serial Monitor for actual IP)
- **Max Clients**: 4 simultaneous connections
- **Inactivity Timeout**: 600ms

### Modbus RTU Settings

- **Baud Rate**: 9600
- **Data Bits**: 8
- **Stop Bits**: 1
- **Parity**: None (8N1)
- **Timeout**: 1000ms

### Pin Configuration

If you need to change pins, modify these defines in `solarmon.ino`:

```cpp
#define STAT_LED 21      // Status LED pin
#define RS485_RX 9       // RS485 receive pin
#define RS485_TX 8       // RS485 transmit pin
```

## Installation

1. **Connect Hardware**:
   - Connect RS485 transceiver to GPIO8 (TX) and GPIO9 (RX)
   - Connect status LED to GPIO21 (or use built-in LED)
   - Connect ESP32 to your computer via USB

2. **Configure WiFi**:
   - Edit `MY_SSID` and `MY_PASS` in `solarmon.ino`

3. **Upload Sketch**:
   - Select the correct board and port in Arduino IDE
   - Click Upload

4. **Monitor Serial Output**:
   - Open Serial Monitor (115200 baud)
   - You should see:

     ```text
     __ OK __
     IP address: 192.168.x.x
     Use the shown IP and port 502 to send requests!
     ```

5. **Note the IP Address**:
   - Use this IP address in `save_influx.py` with the `--host` parameter

## Usage

### Basic Operation

Once uploaded and running:

- The ESP32 connects to WiFi automatically
- The Modbus bridge starts on port 502
- Status LED blinks every 3 seconds to indicate operation
- LED stays on when WiFi is connected

### Serial Commands

Send commands via Serial Monitor:

- `s` - Display WiFi signal strength (RSSI in dBm)

### Over-The-Air (OTA) Updates

The sketch includes ArduinoOTA support, allowing you to update the firmware wirelessly:

- OTA is automatically enabled
- Use Arduino IDE's OTA upload feature or other OTA tools
- Ensure the ESP32 and your computer are on the same network

## Features

- **Modbus RTU-to-TCP Bridge**: Translates Modbus RTU (RS485) to Modbus TCP (WiFi)
- **WiFi Connectivity**: Connects to your local WiFi network
- **Status LED**: Visual indication of operation (heartbeat every 3 seconds)
- **OTA Updates**: Over-the-air firmware updates via ArduinoOTA
- **Serial Debugging**: Serial monitor output for troubleshooting
- **Multiple Clients**: Supports up to 4 simultaneous TCP connections
- **Function Code Support**: Accepts all Modbus function codes (except FC 06 on server ID 1)

## Modbus Bridge Configuration

The bridge maps Modbus server IDs:

- **Server ID 1**: Maps to remote Modbus RTU device ID 1, accepts all function codes except FC 06

## Troubleshooting

### WiFi Connection Issues

- Verify SSID and password are correct
- Ensure 2.4 GHz WiFi (ESP32 doesn't support 5 GHz)
- Check Serial Monitor for connection status
- Try moving ESP32 closer to router

### Modbus Communication Issues

- Verify RS485 wiring (RX, TX, GND)
- Check baud rate matches inverter (default: 9600)
- Ensure RS485 transceiver is properly powered
- Verify inverter Modbus device ID matches (default: 1)
- Check that inverter is powered and responding

### Serial Monitor Shows No Output

- Verify baud rate is set to 115200
- Check USB cable connection
- Try resetting the ESP32

### Cannot Connect via TCP

- Verify IP address from Serial Monitor
- Check firewall settings on your computer
- Ensure ESP32 and computer are on same network
- Verify port 502 is not blocked

### Status LED Not Blinking

- Check LED wiring (GPIO21)
- Verify LED polarity
- Check if WiFi is connected (LED should be on when connected)

## Integration with save_influx.py

Once the bridge is running, use the displayed IP address with the Python monitoring script:

```bash
python save_influx.py --host 192.168.1.69
```

Replace `192.168.1.69` with the actual IP address shown in the Serial Monitor.

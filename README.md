# srne-solar-monitor
Monitor SRNE solar charger/inverter

Based on [SRNE-Hybrid-Inverter-Monitor](https://github.com/shakthisachintha/SRNE-Hybrid-Inverter-Monitor).

## Hardware Setup

The `solarmon/` directory contains an Arduino sketch for an ESP32 that runs a Modbus RTU-to-TCP bridge, allowing the Python monitoring script to communicate with the SRNE inverter over WiFi. See the [solarmon README](solarmon/README.md) for hardware setup and configuration details.

## Installation

### 1. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python save_influx.py
```

### Command Line Options

- `--host` - Modbus TCP host IP address (default: `192.168.1.69`)
- `--port` - Modbus TCP port (default: `502`)
- `--device-id` - Modbus TCP device ID (default: `1`)
- `--interval` - Data update interval in seconds (default: `10`)
- `--influx-host` - InfluxDB host (default: `localhost`)
- `--influx-port` - InfluxDB port (default: `8086`)
- `--influx-user` - InfluxDB username (optional)
- `--influx-password` - InfluxDB password (optional)
- `--influx-database` - InfluxDB database name (default: `solarmon`)
- `--latitude` - Latitude for weather data (default: `45.5157`)
- `--longitude` - Longitude for weather data (default: `-122.6403`)
- `--timezone` - Timezone for weather data (default: `America/Los_Angeles`)

### Example

```bash
python save_influx.py \
  --host 192.168.1.100 \
  --interval 30 \
  --influx-host localhost \
  --influx-database solar_data \
  --latitude 40.7128 \
  --longitude -74.0060 \
  --timezone America/New_York
```

## Features

- Monitors SRNE inverter parameters (battery, PV, inverter output)
- Logs data to InfluxDB for time-series analysis
- Fetches weather data from Open-Meteo API
- Configurable update intervals and connection settings


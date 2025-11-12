# !python
from SRNEinverter import SRNEInverter, OutputPriority, ChargerPriority
import srnecommands
import time
import argparse
import traceback
from datetime import datetime, timezone
from influxdb import InfluxDBClient
import openmeteo_requests
import requests_cache
from retry_requests import retry

def flatten_dict(d, parent_key='', sep='_'):
    """
    Recursively flatten a nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for nested dictionaries
        sep: Separator between keys (default: '_')
    
    Returns:
        Flattened dictionary with scalar values
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def get_weather_data(openmeteo, latitude, longitude, timezone):
    """
    Fetch current weather data from Open-Meteo API.
    
    Args:
        openmeteo: Open-Meteo API client
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        timezone: Timezone string
    
    Returns:
        Dictionary with weather data fields, or None if error
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ["temperature_2m", "relative_humidity_2m", "precipitation", "cloud_cover"],
            "timezone": timezone,
        }
        
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        # Process current data
        current = response.Current()
        current_temperature_2m = current.Variables(0).Value()
        current_relative_humidity_2m = current.Variables(1).Value()
        current_precipitation = current.Variables(2).Value()
        current_cloud_cover = current.Variables(3).Value()
        
        return {
            "weather_temperature_2m": current_temperature_2m,
            "weather_relative_humidity_2m": current_relative_humidity_2m,
            "weather_precipitation": current_precipitation,
            "weather_cloud_cover": current_cloud_cover
        }
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        traceback.print_exc()
        return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Monitor SRNE Inverter and log data to InfluxDB')
    parser.add_argument('--interval', '-i', type=int, default=10, 
                       help='Data update interval in seconds (default: 10)')
    parser.add_argument('--host', type=str, default='192.168.1.69',
                       help='Modbus TCP host IP address (default: 192.168.1.69)')
    parser.add_argument('--port', type=int, default=502,
                       help='Modbus TCP port (default: 502)')
    parser.add_argument('--device-id', '-d', type=int, default=1,
                       help='Modbus TCP device ID (default: 1)')
    parser.add_argument('--influx-host', type=str, default='localhost',
                       help='InfluxDB host (default: localhost)')
    parser.add_argument('--influx-port', type=int, default=8086,
                       help='InfluxDB port (default: 8086)')
    parser.add_argument('--influx-user', type=str, default='',
                       help='InfluxDB username (optional)')
    parser.add_argument('--influx-password', type=str, default='',
                       help='InfluxDB password (optional)')
    parser.add_argument('--influx-database', type=str, default='solarmon',
                       help='InfluxDB database name (default: solarmon)')
    parser.add_argument('--latitude', type=float, default=45.5157,
                       help='Latitude for weather data (default: 45.5157)')
    parser.add_argument('--longitude', type=float, default=-122.6403,
                       help='Longitude for weather data (default: -122.6403)')
    parser.add_argument('--timezone', type=str, default='America/Los_Angeles',
                       help='Timezone for weather data (default: America/Los_Angeles)')
    args = parser.parse_args()

    # Initialize inverter
    inverter = SRNEInverter(args.host, args.port, device_id=args.device_id, debug=True, mock=False)
    
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    
    # Initialize InfluxDB client (InfluxDB v1)
    try:
        client = InfluxDBClient(
            host=args.influx_host,
            port=args.influx_port,
            username=args.influx_user if args.influx_user else None,
            password=args.influx_password if args.influx_password else None,
            database=args.influx_database
        )
        
        # Create database if it doesn't exist
        try:
            databases = client.get_list_database()
            db_exists = any(db['name'] == args.influx_database for db in databases)
            if not db_exists:
                client.create_database(args.influx_database)
                print(f"Created database '{args.influx_database}'")
        except Exception as db_error:
            # If get_list_database fails, try to create the database anyway
            try:
                client.create_database(args.influx_database)
                print(f"Created database '{args.influx_database}'")
            except Exception:
                pass  # Database might already exist
        
        # Test connection by switching to the database
        client.switch_database(args.influx_database)
        print(f"Connected to InfluxDB at {args.influx_host}:{args.influx_port}")
        
    except Exception as e:
        print(f"Error connecting to InfluxDB: {e}")
        print("Please check your InfluxDB connection settings")
        traceback.print_exc()
        return
    
    print(f"Logging inverter data to InfluxDB database '{args.influx_database}' every {args.interval} seconds")
    print("Press Ctrl+C to stop")
    
    # Main loop
    try:
        while True:
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n{timestamp_str}")
            
            # Try to get inverter data
            inverter_data_available = False
            flattened_record = {}
            try:
                # Get inverter data
                record = inverter.get_record() 
                
                # Flatten the record for InfluxDB storage
                flattened_record = flatten_dict(record)
                
                # Try to get output priority (this can fail when inverter is offline)
                try:
                    val = inverter.get_inverter_output_priority()
                    print(f"Output Priority: {val.value}")
                except (ValueError, Exception) as e:
                    if inverter._debug:
                        print(f"Warning: Could not read output priority: {e}")
                
                print(record)
                inverter_data_available = True
                
            except Exception as e:
                print(f"Inverter offline or error reading inverter data: {e}")
                if inverter._debug:
                    traceback.print_exc()
            
            # Always try to get weather data (independent of inverter status)
            weather_data = get_weather_data(openmeteo, args.latitude, args.longitude, args.timezone)
            if weather_data:
                print(f"Weather: Temp={weather_data['weather_temperature_2m']:.1f}°C, "
                      f"Humidity={weather_data['weather_relative_humidity_2m']:.1f}%, "
                      f"Precip={weather_data['weather_precipitation']:.2f}mm, "
                      f"Cloud={weather_data['weather_cloud_cover']:.1f}%")
            
            # Prepare fields for InfluxDB (convert values to appropriate types)
            fields = {}
            
            # Add inverter data if available
            if inverter_data_available:
                for key, value in flattened_record.items():
                    # Convert value to appropriate type
                    if isinstance(value, (int, float)):
                        fields[key] = float(value)
                    elif isinstance(value, bool):
                        fields[key] = int(value)
                    elif isinstance(value, str):
                        # Try to convert numeric strings
                        try:
                            if '.' in value:
                                fields[key] = float(value)
                            else:
                                fields[key] = int(value)
                        except ValueError:
                            fields[key] = value
                    else:
                        fields[key] = str(value)
            
            # Add weather data to fields if available
            if weather_data:
                for key, value in weather_data.items():
                    if isinstance(value, (int, float)):
                        fields[key] = float(value)
                    else:
                        fields[key] = value
            
            # Only save if we have at least some data
            if fields:
                # Create InfluxDB data point (JSON format for v1)
                json_body = [{
                    "measurement": "inverter_data",
                    "time": datetime.now(timezone.utc).isoformat(),
                    "fields": fields
                }]
                
                # Write point to InfluxDB
                try:
                    client.write_points(json_body)
                    if inverter_data_available and weather_data:
                        print(f"Inverter and weather data saved to InfluxDB database '{args.influx_database}'")
                    elif inverter_data_available:
                        print(f"Inverter data saved to InfluxDB database '{args.influx_database}'")
                    elif weather_data:
                        print(f"Weather data saved to InfluxDB database '{args.influx_database}'")
                except Exception as e:
                    print(f"Error writing to InfluxDB: {e}")
                    traceback.print_exc()
            else:
                print("No data available to save")
            
            # Wait for the specified interval
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n\nStopping data collection...")
        print(f"Data saved to InfluxDB database: {args.influx_database}")

if __name__ == "__main__":
    main()

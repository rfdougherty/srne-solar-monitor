from SRNEinverter import SRNEInverter, OutputPriority, ChargerPriority
import srnecommands
import csv
import time
import argparse
from pathlib import Path
from datetime import datetime

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

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Monitor SRNE Inverter and log data to CSV')
    parser.add_argument('--interval', '-i', type=int, default=10, 
                       help='Data update interval in seconds (default: 60)')
    parser.add_argument('--output', '-o', type=str, default='inverter_data.csv',
                       help='Output CSV file path (default: inverter_data.csv)')
    parser.add_argument('--host', type=str, default='192.168.1.69',
                       help='Modbus TCP host IP address (default: 192.168.1.69)')
    parser.add_argument('--port', type=int, default=502,
                       help='Modbus TCP port (default: 502)')
    parser.add_argument('--device-id', '-d', type=int, default=1,
                       help='Modbus TCP device ID (default: 1)')
    args = parser.parse_args()

    # Initialize inverter
    inverter = SRNEInverter(args.host, args.port, device_id=args.device_id, debug=True, mock=False)
    
    csv_file = Path(args.output)
    
    # Check if CSV file exists, if not create it with headers
    file_exists = csv_file.exists()
    
    if not file_exists:
        # Get initial record to determine headers
        try:
            initial_record = inverter.get_record()
            flattened_record = flatten_dict(initial_record)
            headers = ['timestamp'] + list(flattened_record.keys())
            
            # Create file and write headers
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            print(f"Created CSV file: {csv_file}")
            print(f"Headers: {headers}")
        except Exception as e:
            print(f"Error initializing CSV file: {e}")
            return
    
    print(f"Logging inverter data to {csv_file} every {args.interval} seconds")
    print("Press Ctrl+C to stop")
    
    # Main loop
    try:
        while True:
            try:
                # Get inverter data
                record = inverter.get_record() 
                
                # Flatten the record for CSV storage
                flattened_record = flatten_dict(record)
                
                # Print to console for monitoring
                print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(record)

                val = inverter.get_inverter_output_priority()
                print(f"Output Priority: {val.value}")
                
                # Prepare row data
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                row_data = [timestamp] + list(flattened_record.values())
                
                # Append to CSV (open, write, close for data integrity)
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(row_data)
                
                print(f"Data saved to {csv_file}")
                
            except Exception as e:
                print(f"Error reading/writing data: {e}")
            
            # Wait for the specified interval
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n\nStopping data collection...")
        print(f"Data saved in: {csv_file}")

if __name__ == "__main__":
    main()

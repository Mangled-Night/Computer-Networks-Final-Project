import csv
from datetime import datetime
import os

# Initialize an empty list to hold the stats for each operation
stats = []
def record_stats(operation_type, file_size_MB, transfer_time_s, data_rate_MBps):
    # Append the operation details as a dictionary to the stats list
    stats.append({
        "timestamp": datetime.now().isoformat(),
        "operation_type": operation_type,
        "file_size_MB": file_size_MB,
        "transfer_time_s": transfer_time_s,
        "data_rate_MBps": data_rate_MBps
    })

fieldnames = ["timestamp", "operation_type", "file_size_MB", "transfer_time_s", "data_rate_MBps"]
# Saves stats to a csv file
def save_stats_to_csv(filename="operation_stats.csv"):
    # Check if the file exists
    file_exists = os.path.exists(filename)
    file_empty = not file_exists or os.path.getsize(filename) == 0

    # Create an empty file if it does not exist
    if not file_exists:
        open(filename, 'x').close()  # Create the file without writing anything

    # Open the file in append mode
    with open(filename, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Write the header if the file is new or empty
        if file_empty:
            writer.writeheader()

        # Write the stats data
        writer.writerows(stats)

    # Clear stats after saving to avoid duplication
    stats.clear()


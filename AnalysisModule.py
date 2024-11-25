import csv
from datetime import datetime
import logging

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
# Saves stats to a csv file
def save_stats_to_csv(filename="operation_stats.csv"):

    # Define CSV fieldnames based on dictionary keys in stats
    fieldnames = ["timestamp", "operation_type", "file_size_MB", "transfer_time_s", "data_rate_MBps"]

    # Open the file in write mode and write the data from stats
    with open(filename, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()  # Write CSV headers
        writer.writerows(stats)  # Write each recorded operation's data as a row


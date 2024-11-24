import csv
from datetime import datetime

# Initialize an empty list to hold the stats for each operation
stats = []

def record_stats(operation_type, file_size_MB, transfer_time_s, data_rate_MBps, response_time_s):
    # Append the operation details as a dictionary to the stats list
    stats.append({
        "timestamp": datetime.now().isoformat(),
        "operation_type": operation_type,
        "file_size_MB": file_size_MB,
        "transfer_time_s": transfer_time_s,
        "data_rate_MBps": data_rate_MBps,
        "response_time_s": response_time_s
    })
# Saves stats to a csv file
def save_stats_to_csv(filename="operation_stats.csv"):

    # Define CSV fieldnames based on dictionary keys in stats
    fieldnames = ["timestamp", "operation_type", "file_size_MB", "transfer_time_s", "data_rate_MBps", "response_time_s"]

    # Open the file in write mode and write the data from stats
    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()  # Write CSV headers
        writer.writerows(stats)  # Write each recorded operation's data as a row

    print(f"Statistics saved to {filename}")
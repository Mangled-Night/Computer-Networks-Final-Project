from AnalysisModule import record_stats, save_stats_to_csv

# Record some example stats
record_stats("upload", 5.2, 10, 0.52, 0.2)
record_stats("download", 3.1, 8, 0.39, 0.15)

# Save the stats to CSV
save_stats_to_csv()
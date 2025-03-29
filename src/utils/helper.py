# src/utils/helpers.py
def print_log(message, log_file="fleet_logs.txt"):
    with open(log_file, "a") as f:
        f.write(message + "\n")

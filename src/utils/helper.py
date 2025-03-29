# src/utils/helpers.py
import logging
import os

# Configure logging to write to fleet_logs.txt in the project root.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_file_path = os.path.join(project_root, "fleet_logs.txt")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()  # Optional: also output to console
    ]
)

def log_event(message, level="info"):
    if level == "info":
        logging.info(message)
    elif level == "debug":
        logging.debug(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
    elif level == "critical":
        logging.critical(message)

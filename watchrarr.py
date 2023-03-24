"""
watchrarr.py: Recursively watch a directory for RAR files and extract them upon creation

Copyright (C) 2023 HomeLabineer
This project is licensed under the MIT License. See the LICENSE file for details.

This script monitors a specified directory for the creation of RAR files (including split or spanned RAR archives)
and automatically extracts them. 
"""

import sys
import os
import time
import argparse
import logging
import rarfile
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
import logging.handlers
import re
import json
import yaml

def load_extracted_files(file_path):
    """
    Load extracted files information from a JSON file.

    :param file_path: Path to the JSON file.
    :return: A dictionary containing extracted files information.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_extracted_files(file_path, extracted_files):
    with open(file_path, 'w') as f:
        json.dump(extracted_files, f)

def process_existing_rar_files(path, handler):
    logging.info("Performing initial recursive search for RAR files")
    for root, _, files in os.walk(path):
        for file in files:
            _, file_ext = os.path.splitext(file.lower())
            if WatcherEventHandler.rar_pattern.match(file_ext):
                file_path = os.path.join(root, file)
                handler.extract_rar(file_path)

def validate_path(config):
    if "path" in config:
        return config["path"]
    else:
        raise ValueError("Path must be specified either in the config file or as an argument.")

def validate_polling(config):
    if "polling" in config:
        if not isinstance(config["polling"], bool):
            raise ValueError("polling must be a boolean value (True or False).")
        return config["polling"]
    return None

def validate_interval(config):
    if "interval" in config:
        if not isinstance(config["interval"], (int, float)) or config["interval"] <= 0 or config["interval"] > 300:
            raise ValueError("interval must be a positive number greater than 0 seconds and less than or equal to 5 minutes (300 seconds).")
        return config["interval"]
    return None

def validate_log_file(config):
    if "log_file" in config:
        if not isinstance(config["log_file"], str):
            raise ValueError("log_file must be a string.")
        return config["log_file"]
    return None

def validate_debug(config):
    if "debug" in config:
        if not isinstance(config["debug"], bool):
            raise ValueError("debug must be a boolean value (True or False).")
        return config["debug"]
    return None

def validate_max_log_size(config):
    if "max_log_size" in config:
        if not isinstance(config["max_log_size"], int) or config["max_log_size"] < 10 or config["max_log_size"] > 100:
            raise ValueError("max_log_size must be an integer between 10 MB and 100 MB.")
        config["max_log_size"] = config["max_log_size"] * 1024 * 1024
        return config["max_log_size"]
    return None

def validate_log_backup_count(config):
    if "log_backup_count" in config:
        if not isinstance(config["log_backup_count"], int) or config["log_backup_count"] < 1 or config["log_backup_count"] > 100:
            raise ValueError("log_backup_count must be an integer between 1 and 100.")
        return config["log_backup_count"]
    return None

def update_args_from_config(args, config_file_path):
    """
    Update command-line arguments with values from a configuration file.

    :param args: The argparse.Namespace object containing command-line arguments.
    :param config_file_path: The path to the configuration file.
    """
    try:
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r') as config_file:
                config = yaml.safe_load(config_file)
                
            if config is None:
                raise ValueError("Configuration file is empty. Please provide the required configurations.")
        else:
            raise FileNotFoundError(f"Config file not found: {config_file_path}")

        args.path = validate_path(config)
        args.polling = validate_polling(config) or args.polling
        args.interval = validate_interval(config) or args.interval
        args.log_file = validate_log_file(config) or args.log_file
        args.debug = validate_debug(config) or args.debug
        args.max_log_size = validate_max_log_size(config) or args.max_log_size
        args.log_backup_count = validate_log_backup_count(config) or args.log_backup_count

    except FileNotFoundError as e:
        logging.error(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML config file: {e}")
        sys.exit(1)
    except ValueError as e:
        logging.error(f"Error: {e}")
        sys.exit(1)

class WatcherEventHandler(FileSystemEventHandler):
    rar_pattern = re.compile(r"\.rar$|\.r\d\d$|\.part\d+\.rar$")

    def __init__(self, extracted_files):
        self.extracted_files = extracted_files

    def on_modified(self, event):
        logging.debug(f"File {event.src_path} has been modified") # Ignoring modifications, focusing on created RAR files

    def on_created(self, event):
        logging.debug(f"File {event.src_path} has been created") # Created is the focus but ignoring any non-rar archives from INFO
        if event.is_directory:
            return

        _, file_ext = os.path.splitext(event.src_path.lower())
        if WatcherEventHandler.rar_pattern.match(file_ext):
            logging.info(f"*** New RAR file {event.src_path} found ***")
            self.extract_rar(event.src_path)

    def on_deleted(self, event):
        logging.debug(f"File {event.src_path} has been deleted")  # Ignoring deletions

    def on_moved(self, event):
        logging.debug(f"File {event.src_path} has been moved to {event.dest_path}")  # Ignoring moved files

    def is_first_volume(rar_file):
        """Check if the RAR file is the first volume of a split archive."""
        for info in rar_file.infolist():
            if info.flags & rarfile.RAR_FIRST_VOLUME:
                return True
        return False

    def extract_rar(self, rar_file_path):
        if rar_file_path in self.extracted_files:
            logging.info(f"Skipping already extracted file: {rar_file_path}")
            return
        try:
            with rarfile.RarFile(rar_file_path) as rf:
                if not is_first_volume(rf):  # Check if it's the first volume of a split archive
                    logging.info(f"Skipping non-first volume: {rar_file_path}")
                    return

                target_dir = os.path.dirname(rar_file_path)
                for entry in rf.infolist():
                    temp_file_path = os.path.join(target_dir, entry.filename + ".tmp")
                    final_file_path = os.path.join(target_dir, entry.filename)
                    logging.info(f"Extracting {entry.filename} to {temp_file_path}")

                    try:
                        with open(temp_file_path, 'wb') as tmp_file:
                            tmp_file.write(rf.read(entry))
                    except (OSError, rarfile.Error) as e:
                        logging.error(f"Failed to write {temp_file_path}: {e}")
                        continue

                    try:
                        os.rename(temp_file_path, final_file_path)  # Remove .tmp extension after extraction
                    except OSError as e:
                        logging.error(f"Failed to rename {temp_file_path} to {final_file_path}: {e}")
                        continue

                    logging.info(f"File {final_file_path} has been created")  # Now we want to know about it in INFO
        except rarfile.Error as e:
            logging.error(f"Failed to extract {rar_file_path}: {e}")
        self.extracted_files[rar_file_path] = True

def setup_logging(args):
    """
    Set up logging for the script.

    :param args: The argparse.Namespace object containing command-line arguments.
    """
    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    log_handler = logging.handlers.RotatingFileHandler(args.log_file, maxBytes=int(args.max_log_size), backupCount=args.log_backup_count)
    log_handler.setFormatter(logging.Formatter(log_format))

    # Add a StreamHandler to print log messages to the console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))

    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG

    logging.root.addHandler(log_handler)
    # print("Handlers:", logging.root.handlers) 
    logging.root.addHandler(console_handler)
    # print("Handlers:", logging.root.handlers)
    logging.root.setLevel(log_level)
    # print("Handlers:", logging.root.handlers)

def main(args):
    """
    Main function for watchrarr.py script.

    :param args: The argparse.Namespace object containing command-line arguments.
    """

    # Update arguments from the configuration file
    update_args_from_config(args, args.config) 

    # Set up logging
    try:
        setup_logging(args)
    except Exception as e:
        print(f"Error setting up logging: {e}")
        sys.exit(1)

    # Load the extracted files information and create the event handler
    extracted_files_path = "extracted_files.json"
    extracted_files = load_extracted_files(extracted_files_path)
    event_handler = WatcherEventHandler(extracted_files)

    # Start the script line in log
    logging.info("Starting watchrarr.py") 

    # Process existing RAR files in the specified directory
    process_existing_rar_files(args.path, event_handler)

    # Set up and start the observer
    if args.polling:
        observer = PollingObserver(timeout=args.interval)
    else:
        observer = Observer()

    try:
        observer.schedule(event_handler, args.path, recursive=True)
        observer.start()
    except Exception as e:
        logging.error(f"Error setting up observer: {e}")
        sys.exit(1)
    
    # Main loop to monitor the directory and save extracted files information
    try:
        while True:
            time.sleep(1)
            save_extracted_files(extracted_files_path, event_handler.extracted_files)
    except KeyboardInterrupt:
        observer.stop()
        save_extracted_files(extracted_files_path, event_handler.extracted_files)
    observer.join()

if __name__ == "__main__":
    # Define command-line arguments
    parser = argparse.ArgumentParser(description="Recursively watch a directory for RAR files.")
    parser.add_argument("--path", default=None, help="Path to the directory you want to watch. (default=None)")
    parser.add_argument("--config", default="config.yaml", help="Path to the configuration file (YAML format).")
    parser.add_argument("--polling", action="store_true", help="Use polling observer (useful for NFS shares).")
    parser.add_argument("--interval", type=float, default=5, help="Polling interval in seconds (default: 5).")
    parser.add_argument("--log_file", default="watchrarr.log", help="Path to the log file where events will be recorded (default: watchrarr.log).")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument("--max_log_size", type=int, default=10, help="The maximum size of the log file in MB before it's rotated (default: 10).")
    parser.add_argument("--log_backup_count", type=int, default=9, help="The number of backup log files to keep before overwriting the oldest log file (default: 9).")
    # Update the args variable.
    args = parser.parse_args()

    main(args)

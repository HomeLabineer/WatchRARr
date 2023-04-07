"""
watchrarr.py: Recursively watch a directory for RAR files and extract them upon creation

------------------------------
WatchRARr Info
------------------------------
Copyright (C) 2023 HomeLabineer
This project is licensed under the MIT License. See the LICENSE file for details.
Script Name: watchrarr.py
Description: A script to recursively watch a directory for RAR files and extract them upon creation.
             The script processes both single RAR files and split/spanned RAR archives. It also maintains
             a SQLite database to keep track of processed files and avoid reprocessing them.

Usage:
  1. Configure the script by setting the necessary options in the config.yaml file.
  2. Save the script as watchrarr.py.
  3. Make sure to install the required Python libraries: unrar, watchdog, rarfile, and PyYAML.
  4. Run the script: python3 watchrarr.py
  5. The script will monitor the specified directory and extract RAR files upon creation.

Configuration Options (config.yaml):
  watch_directory: Directory to monitor for RAR files.
  log_file: Path to the log file.
  max_log_size: Maximum log file size in MB.
  log_rotations: Number of log files to keep in rotation.
  scan_interval: Scan interval in seconds.
  db_file: Path to the SQLite database file.
  logging_level: Logging level (DEBUG, INFO, WARNING, ERROR, or CRITICAL).

------------------------------
"""

__version__ = '1.2.6-develop'

import argparse
import logging
import os
import sqlite3
import sys
import yaml
import rarfile
import shutil
import time
import re
from pathlib import Path
from time import sleep
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from logging.handlers import RotatingFileHandler
# from logging import _nameToLevel as log_levels_dict


def main(args):
    # Configure logging
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler = RotatingFileHandler(args.log_file, mode='a', maxBytes=args.max_log_size * 1024 * 1024,
                                      backupCount=args.log_rotations, encoding=None, delay=0)
    log_handler.setFormatter(log_formatter)
    
    # Set the level of the log_handler based on the logging_level argument
    log_handler.setLevel(getattr(logging, args.logging_level.upper()))

    logger = logging.getLogger()
    logger.addHandler(log_handler)
    logger.setLevel(getattr(logging, args.logging_level.upper()))

    logging.info(f"WatchRARr v{__version__} successfully started")
    logging.info("Configuration file loaded successfully.")

    # Initialize the SQLite database
    conn = sqlite3.connect(args.db_file)
    create_processed_files_table(conn)

    # Initial scan of the directory
    manual_scan(args, conn)

    # Set up a Watchdog observer to monitor the directory
    event_handler = RarEventHandler(args)
    observer = Observer()
    observer.schedule(event_handler, args.watch_directory, recursive=True)
    observer.start()

    try:
        while True:
            sleep(args.scan_interval)
            manual_scan(args, conn)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def is_rar_archive(file):
    """Check if the given file is a RAR archive, including split archives."""
    if file.lower().endswith('.rar'):
        return True
    elif file.lower()[-4:-3] == '.' and file.lower()[-3:].isdigit() and int(file.lower()[-3:]) < 100:
        return True
    return False

def get_related_rar_files(file_path):
    directory, file_name = os.path.split(file_path)
    base_name, _ = os.path.splitext(file_name)
    base_name = re.sub(r'\.part\d+', '', base_name)
    related_files = []

    for entry in os.listdir(directory):
        if entry.startswith(base_name) and entry.endswith(".rar"):
            related_files.append(os.path.join(directory, entry))

    return related_files

def wait_for_transfer_completion(file_path):
    check_interval = 5
    stable_duration = 10
    stable_start_time = None

    related_files = get_related_rar_files(file_path)
    logging.info(f"Found {len(related_files)} related RAR files for {file_path}")
    file_sizes = {f: -1 for f in related_files}

    logging.info(f"Waiting for transfer completion of {file_path} and related files...")

    while True:
        all_files_stable = True

        for f in related_files:
            current_size = os.path.getsize(f)

            if current_size != file_sizes[f]:
                all_files_stable = False
                file_sizes[f] = current_size
                stable_start_time = None
                break

        if all_files_stable:
            if stable_start_time is None:
                stable_start_time = time.time()
            elif time.time() - stable_start_time >= stable_duration:
                break

        time.sleep(check_interval)

def process_rar_file(filepath, args):
    """Process a RAR file by extracting its contents and storing its path in the SQLite database."""

    # Wait for the file transfer to complete before processing
    wait_for_transfer_completion(filepath)
    
    # Connect to the SQLite database
    conn = sqlite3.connect(args.db_file)
    cursor = conn.cursor()

    # Check if the file has been processed before
    cursor.execute('SELECT mtime FROM processed_files WHERE filepath = ?', (filepath,))
    result = cursor.fetchone()

    if result is None:
        # Extract the RAR archive and store its path in the database
        logging.info(f"Extracting {filepath}")
        extract_rar(filepath)
        try:
            cursor.execute('INSERT INTO processed_files (filepath, mtime) VALUES (?, ?)', (filepath, os.path.getmtime(filepath)))
            conn.commit()
        except sqlite3.IntegrityError:
            logging.warning(f"File path {filepath} already exists in the database. Skipping insertion.")
    else:
        logging.debug(f"File {filepath} has already been processed.")

    conn.close()

def create_processed_files_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_files (
            filepath TEXT PRIMARY KEY,
            mtime REAL
        )
    """)
    conn.commit()
    logging.info("Processed_files table initialized in the SQLite database.")

def manual_scan(args, conn):
    """Perform a manual scan of the watch_directory to process existing RAR files."""
    logging.info("Starting manual directory scan...")
    
    cursor = conn.cursor()

    for dirpath, dirnames, filenames in os.walk(args.watch_directory):
        for file in filenames:
            if file.lower().endswith('.rar'):
                filepath = os.path.join(dirpath, file)
                file_mtime = os.path.getmtime(filepath)
                
                cursor.execute("SELECT mtime FROM processed_files WHERE filepath=?", (filepath,))
                result = cursor.fetchone()
                
                if result is None or file_mtime > result[0]:
                    process_rar_file(filepath, args)
                    cursor.execute("INSERT OR REPLACE INTO processed_files (filepath, mtime) VALUES (?, ?)", (filepath, file_mtime))
                    conn.commit()
                else:
                    logging.debug(f"File {filepath} has already been processed.")

    logging.info("Finished manual directory scan.")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Watch a directory for new RAR archives and extract them.")
    parser.add_argument('-c', '--config', help="Path to the YAML configuration file.", default="config.yaml")
    parser.add_argument('-w', '--watch_directory', help="Path to the directory to watch for RAR files.")
    parser.add_argument('-d', '--db_file', help="Path to the SQLite database file.")
    parser.add_argument('-l', '--log_file', help="Path to the log file.")
    parser.add_argument('-i', '--scan_interval', help="Scan interval in seconds.", type=int)
    parser.add_argument('--logging_level', help="Logging level. Choose from DEBUG, INFO, WARNING, ERROR, and CRITICAL.")
    # parser.add_argument('--logging_level', choices=[x.lower() for x in list(log_levels_dict.keys())[:-1]], default="INFO", help='Logging level (default="INFO")')
    parser.add_argument('--max_log_size', help="Maximum log file size in MB.", type=int)
    parser.add_argument('--log_rotations', help="Number of log files to keep in rotation.", type=int)
    return parser.parse_args()


def extract_rar(filepath):
    """Extract a RAR file and rename extracted files to remove .tmp extension."""
    try:
        with rarfile.RarFile(filepath) as rf:
            target_dir = os.path.dirname(filepath)

            logging.info(f"Number of files in the archive: {len(rf.infolist())}")

            start_time = time.time()
            extracted_files_size = 0

            # Extract files with a .tmp extension
            for rar_info in rf.infolist():
                tmp_file_path = os.path.join(target_dir, rar_info.filename + '.tmp')
                logging.info(f"Extracting {rar_info.filename} to {tmp_file_path}")
                extracted_files_size += rar_info.file_size
                with open(tmp_file_path, 'wb') as tmp_file:
                    with rf.open(rar_info) as rar_file:
                        # Read and wrdddddddddddddddite data in chunks
                        chunk_size = 1024 * 1024  # 1 MiB
                        while (chunk := rar_file.read(chunk_size)):
                            tmp_file.write(chunk)

            # Rename files to remove .tmp extension
            for rar_info in rf.infolist():
                tmp_file_path = os.path.join(target_dir, rar_info.filename + '.tmp')
                final_file_path = os.path.join(target_dir, rar_info.filename)
                logging.info(f"Renaming {tmp_file_path} to {final_file_path}")
                shutil.move(tmp_file_path, final_file_path)

            elapsed_time = time.time() - start_time
            extracted_files_size_mb = extracted_files_size / (1024 * 1024)
            logging.info(f"Successfully extracted {filepath} to {target_dir}")
            logging.info(f"{filepath} took {elapsed_time:.2f} seconds and extracted files size is {extracted_files_size_mb:.2f} MB.")
    except (rarfile.Error, IOError, OSError) as e:
        logging.error(f"Failed to extract {filepath}: {str(e)}")

class RarEventHandler(FileSystemEventHandler):
    def __init__(self, args):
        self.args = args

    def on_created(self, event):
        """Handle RAR file creation events."""
        if not event.is_directory:
            file = event.src_path
            logging.info(f"File created: {file}")
            if is_rar_archive(file):
                logging.info(f"New RAR file detected: {file}")
                process_rar_file(file, self.args)

    def on_modified(self, event):
        if not event.is_directory:
            file = event.src_path
            logging.debug(f"File modified: {file}")

    def on_deleted(self, event):
        if not event.is_directory:
            file = event.src_path
            logging.debug(f"File deleted: {file}")

if __name__ == '__main__':
    args = parse_args()

    # Load configuration from the YAML file
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Update args with values from the config file, unless they were provided as command-line arguments
    for key, value in config.items():
        if getattr(args, key) is None:
            setattr(args, key, value)

    main(args)
# WatchRARr

WatchRARr is a Python script that monitors a specified directory for the creation of RAR files (including split or spanned RAR archives) and automatically extracts them upon creation. It utilizes the `watchdog` library for monitoring file system events and the `rarfile` library for handling RAR archives.

---

## Requirements

- Python 3.6 or higher
- `watchdog` library
- `rarfile` library
- `PyYAML` library

---

## Installation

### Platform-Specific Instructions

---

#### Docker

Using WatchRARr with Docker makes the installation and setup process easier and more consistent across different platforms. Below are the steps to run WatchRARr using Docker:

1. Make sure you have Docker installed on your system. If not, you can download it from the [official website](https://www.docker.com/get-started).

2. Clone the repository:

```bash
git clone https://github.com/HomeLabineer/WatchRARr.git
cd WatchRARr
```

1. Make a `config.yaml` by copying `config-template.yaml`:
```bash
mv config-template.yaml config.yaml
```

2. Edit the `config.yaml` as needed, here is mine as an example:
```yaml
# watchrarr.py configuration file
# Copyright (C) 2023 HomeLabineer
# This project is licensed under the MIT License. See the LICENSE file for details.

# Path to the directory you want to watch.
# path: test # Comment out if using docker

# If using docker, uncomment the following line and make sure your docker-compose properly maps the desired directory to watch:
path: /app/watch
# docker-compose ex: - /mnt/data:/app/watch

# Use polling observer (useful for NFS shares). Set to 'true' or 'false'.
polling: False

# Polling interval in seconds. Must be a positive number greater than 0 and less than or equal to 300.
interval: 60

# Path to the log file where events will be recorded.
# log_file: watchrarr.log # Comment out if using docker

# If using docker, uncomment the following line and make sure your docker-compose properly maps the desired logs directory:
log_file: /app/logs/watchrarr.log
# docker-compose ex: - logs

# Enable debug logging. Set to 'true' or 'false'.
debug: false

# The maximum size of the log file in MB before it's rotated. Must be an integer between 10 MB and 100 MB.
max_log_size: 10

# The number of backup log files to keep before overwriting the oldest log file. Must be an integer between 1 and 100.
log_backup_count: 9
```

4. Edit the `docker-compose.yaml` as needed, here is mine as an example:
```yaml
services:
  watchrarr:
    image: homelabineer/watchrarr:latest
    container_name: watchrarr
    restart: unless-stopped
    volumes:
      - /mnt/docker_data/watchrarr/config.yaml:/app/config.yaml
      - /mnt/docker_data/watchrarr/logs:/app/logs
      - /mnt/media/Complete:/app/watch
```

5. Start the WatchRARr container:
```bash
docker-compose up -d
```

---

#### Linux / macOS

1. Install Python 3.6 or newer if you haven't already. You can download Python from the [official website](https://www.python.org/downloads/).

2. Clone the repository:
```bash
git clone https://github.com/HomeLabineer/WatchRARr.git
cd watchrarr
```
3. Install required packages:
```bash
pip install -r requirements.txt
```
4. Copy the `config-template.yaml` as `config.yaml`:
```bash
cp config-template.yaml config.yaml
```
5. Run the script:
```bash
python3 watchrarr.py
```

---

#### Windows

> :warning: **Disclaimer:** The WatchRARr project was primarily developed and tested on Linux and macOS systems. The instructions provided below for Windows are theoretical and may require adjustments to work correctly. If you are a Windows user and would like to contribute by improving the compatibility of this program or the documentation, please consider submitting a merge request.  Any reported issues for Windows will likely be directed here and closed without resolution.

1. Install Python 3.7 or newer if you haven't already. You can download Python from the [official website](https://www.python.org/downloads/). Make sure to add Python to your PATH during installation.

2. Clone the repository using a Git client, or download and extract the ZIP file from the repository page.

3. Open a command prompt and navigate to the watchrarr directory:

```ps
cd path\to\watchrarr
```
 
4. Install required packages:

```ps
pip install -r requirements.txt
```

5. Copy the `config-template.yaml` as `config.yaml`:

```bash
cp config-template.yaml config.yaml
```

6. Run the script:

```ps
python3 watchrarr.py
```

---

## Usage

```bash
usage: watchrarr.py [-h] [--path PATH] [--config CONFIG] [--polling] [--interval INTERVAL] [--log_file LOG_FILE] [--debug] [--max_log_size MAX_LOG_SIZE] [--log_backup_count LOG_BACKUP_COUNT]

Recursively watch a directory for RAR files.

optional arguments:
-h, --help show this help message and exit
--path PATH Path to the directory you want to watch.
--config CONFIG Path to the configuration file (YAML format).
--polling Use polling observer (useful for NFS shares).
--interval INTERVAL Polling interval in seconds.
--log_file LOG_FILE Path to the log file where events will be recorded.
--debug Enable debug logging.
--max_log_size MAX_LOG_SIZE
The maximum size of the log file in megabytes before its rotated.
--log_backup_count LOG_BACKUP_COUNT
The number of backup log files to keep before overwriting the oldest log file.

Default values for these options can be found in the example config.yaml file.
```

---

## Example

To watch a directory called `my_directory` and use the default settings: `python watchrarr.py --path my_directory`

---

## Configuration

The script can be configured using command-line arguments or by specifying the settings in a YAML configuration file. By default, the script looks for a `config.yaml` file in the same directory as the script. You can also provide a custom configuration file using the `--config` argument.

Here is an example `config.yaml` file with all the available options:

```yaml
path: test
polling: true
interval: 5
log_file: watchrarr.log
debug: false
max_log_size: 10
log_backup_count: 8
```

---

## Contributing

Thank you for your interest in contributing to WatchRARr! We appreciate your help in making this project better. Here are some guidelines to help ensure a smooth contribution process:

### Reporting issues

If you encounter any issues with the project, please create a new issue on the [Issues](https://github.com/HomeLabineer/WatchRARr/issues) page. When reporting an issue, please provide the following information:

- A clear and concise description of the issue
- Steps to reproduce the issue
- Expected and actual behavior
- Any relevant logs or error messages

### Submitting pull requests

If you would like to submit a pull request, please follow these steps:

1. Fork the repository and create your own branch with a descriptive name, such as `feature/my-new-feature` or `bugfix/my-bugfix`.

2. Make your changes in the new branch, ensuring that you follow the project's coding standards and best practices.

3. Write tests, if applicable, to cover any new functionality or to reproduce and fix any reported issues.

4. Update the documentation, including README and inline comments, to reflect your changes.

5. Before submitting your pull request, make sure your branch is up-to-date with the main branch and that your code passes all tests and linter checks.

6. Create a pull request with a clear and concise description of your changes. In your pull request message, please include any relevant information, such as the issue being addressed, new features added, or bugfixes applied.

### Coding Standards and Best Practices

When contributing to this project, please adhere to the following coding standards and best practices:

- Write clear and concise code, with appropriate comments explaining the functionality of each section or function.
- Follow the established code structure and organization.
- Use meaningful variable and function names that accurately describe their purpose.
- Write tests to cover new functionality or to reproduce and fix any reported issues.
- Keep functions small and focused, adhering to the Single Responsibility Principle.

### Code Style

This project follows the [PEP8](https://www.python.org/dev/peps/pep-0008/) naming convention for Python code. Please ensure your contributions adhere to these guidelines.

Some key points from PEP8 naming convention:

- Use `snake_case` for variable and function names.
- Use `CamelCase` for class names.
- Constants should be in `UPPER_CASE_WITH_UNDERSCORES`.
- Keep names descriptive and not too long.

For more details, please refer to the [official PEP8 guidelines](https://www.python.org/dev/peps/pep-0008/#naming-conventions).

### Testing practices

To ensure the quality and reliability of the project, please follow these testing practices when contributing:

- Write unit tests for new features and bug fixes.
- Ensure that your code passes all existing tests before submitting a pull request.
- Update or add new tests as needed to maintain high test coverage.

By following these guidelines, you'll help us maintain a high-quality, reliable, and easy-to-understand codebase. Thank you for your contribution!

---

## Credits

This project was developed using various programming tools, including the ChatGPT-4 language model. ChatGPT-4 was used to assist with tasks such as generating code snippets, providing suggestions for code improvements, and writing documentation such as this README.

---

# License

This project is licensed under the MIT License. See the LICENSE file for details.
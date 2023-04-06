# WatchRARr

WatchRARr is a Python application designed to recursively watch a directory for RAR files and extract them upon creation. The script processes both single RAR files and split/spanned RAR archives. It also maintains a SQLite database to keep track of processed files and avoid reprocessing them.

---

## Table of Contents

- [Requirements](#requirements)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Planned](#planned)
- [Contributing](#contributing)
- [Reporting issues](#reportingissues)
- [Submitting pull requests](#submittingpullrequests)
- [Credits](#credits)
- [License](#license)

---

## Features

- Recursively watches for file changes within a specified directory for rar archives
- When detected, waits for the rar archive or all files  in a split archive to complete transfer into directory and then extracts the archive
- Appends .tmp to the extracted file name until extraction process is complete so other programs don't pick it  up early and copy/move a partial file
- Logs the file path to a database so it never attempts to extract an archive twice
- Scans the watched directory at startup and at a scheduled interval (configurable by user) to ensure no archives have been missed
- Comes with a [helper script](db-manager.sh) to manage the db - This allows you to easily see what is in the db, remove entries, manually add entries, take db backups and restore from backup
- Designed best to run as a Docker container along with the rest of your *arr apps!

Check out [examples.txt](examples.txt) to see examples of logging in action

---

## Support

Hey, it's great if you just appreciate my work and want to use it for free.  If you have found it helpful at all and want to support my work, you can:

<a href="https://github.com/sponsors/homelabineer">
  <img src="https://img.shields.io/badge/Sponsor_on-GitHub-green?logo=github&style=flat-square" alt="GitHub Sponsors" />
</a>
<a href="https://www.patreon.com/homelabineer">
  <img src="https://img.shields.io/badge/Support_on-Patreon-orange?logo=patreon&style=flat-square" alt="Patreon" />
</a>
<a href="https://paypal.me/homelabineer?country.x=US&locale.x=en_US">
  <img src="https://img.shields.io/badge/Donate-PayPal-green.svg?style=flat-square&logo=paypal" alt="PayPal" />
</a>

---

## Requirements

- Python 3.9 or newer
    - `watchdog` library
    - `rarfile` library
    - `PyYAML` library
    - `UnRAR` library  
*** OR ***
- Docker
    - Docker Compose (optional)

---

## Installation

### Docker

1. Create your local Docker data folder - mine is just called `watchrarr`
2. Create config.yaml in this directory, there is a template available [right here](config-template.yaml)
2. Create your docker-compose.yaml wherever you store it (Or add to an existing one)
3. Edit the `docker-compose.yaml` file to match your local paths and preferences.
2. Start the Docker container:
```
docker-compose up -d watchrarr
```

### Script

1. Clone the repository:
```
git clone https://github.com/HomeLabineer/watchrarr.git
cd watchrarr
```
2. Install the required Python packages:
```
pip install -r requirements.txt
```
3. Edit the `config.yaml` file to match your local paths and preferences.
4. Run the script:
```
python3 watchrarr.py
```

---

## Configuration

Edit the `config.yaml` file to configure the application. The available settings include:

- `log_file`: The log file path.
- `max_log_size`: The maximum log file size in MB.
- `log_rotations`: The number of log files to keep in rotation.
- `scan_interval`: The scan interval in seconds.
- `db_file`: The SQLite database file path.
- `logging_level`: The logging level (DEBUG, INFO, WARNING, ERROR, or CRITICAL).
- `watch_directory`: The directory to watch for RAR files.

---

## Usage

- If running in Docker, ensure the `watch_directory` setting in the `config.yaml` file matches the host directory mounted in the `docker-compose.yaml` file.
- If running as a script, set the `watch_directory` setting in the `config.yaml` file to the desired directory path.

Once the application is running, it will continuously monitor the specified directory for RAR files and extract them when detected.

---

## Planned

- Alerting - Prometheus, Telegram, Slack, Discord, etc
- Logging overhaul - Make things prettier, less chatter, good debugging and ultimately helps improve alerting, if enabled
- Migration function in db-manager.sh script - quickly update pathing, translate windows to linux network pathing (The slashes / are opposite \\ )
- I may rethink how I am detecting a previously extracted archive as I could simply (or in addition to current method) check if the extracted file exists
- At startup the first time, it will extract EVERY archive found if they are not already in the db.  If for some reason this is unwanted, a helper script to add all existing archives to the db first could be used.  That or even simply adding a falg or configuration to enable first run.  If true and .db file doesn't exist, then add archives to db without extracting.  Stop container, switch to false and fire it back up.  IDK which way user's would prefer, maybe both?  Options can be nice.

---


## Contributing

Thank you for your interest in contributing to WatchRARr! We appreciate your help in making this project better. Here are some guidelines to help ensure a smooth contribution process:

If you want to contribute and support my work, you can do so at the following:

<a href="https://github.com/sponsors/homelabineer">
  <img src="https://img.shields.io/badge/Sponsor_on-GitHub-green?logo=github&style=flat-square" alt="GitHub Sponsors" />
</a>
<a href="https://www.patreon.com/homelabineer">
  <img src="https://img.shields.io/badge/Support_on-Patreon-orange?logo=patreon&style=flat-square" alt="Patreon" />
</a>
<a href="https://paypal.me/homelabineer?country.x=US&locale.x=en_US">
  <img src="https://img.shields.io/badge/Donate-PayPal-green.svg?style=flat-square&logo=paypal" alt="PayPal" />
</a>

---

### Reporting issues

If you encounter any issues with the project, please create a new issue on the [Issues](https://github.com/HomeLabineer/WatchRARr/issues) page. When reporting an issue, please provide the following information:

- A clear and concise description of the issue
- Steps to reproduce the issue
- Expected and actual behavior
- Any relevant logs or error messages

---

### Submitting pull requests

If you would like to submit a pull request, please follow these steps:

1. Fork the repository and create your own branch with a descriptive name, such as `feature/my-new-feature` or `bugfix/my-bugfix`.

2. Make your changes in the new branch, ensuring that you follow the project's coding standards and best practices.

3. Write tests, if applicable, to cover any new functionality or to reproduce and fix any reported issues.

4. Update the documentation, including README and inline comments, to reflect your changes.

5. Before submitting your pull request, make sure your branch is up-to-date with the main branch and that your code passes all tests and linter checks.

6. Create a pull request with a clear and concise description of your changes. In your pull request message, please include any relevant information, such as the issue being addressed, new features added, or bugfixes applied.

---

## Credits

This project was developed using various programming tools, including the ChatGPT-4 language model. ChatGPT-4 was used to assist with tasks such as generating code snippets, providing suggestions for code improvements, and writing documentation such as this README.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.



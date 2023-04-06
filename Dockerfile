# """
# DOCKERFILE - A Docker image configuration file for WatchRARr

# ------------------------------
# WatchRARr Info
# ------------------------------
# Copyright (C) 2023 HomeLabineer
# This project is licensed under the MIT License. See the LICENSE file for details.
# Script Name: watchrarr.py
# Description: A script to recursively watch a directory for RAR files and extract them upon creation.
#              The script processes both single RAR files and split/spanned RAR archives. It also maintains
#              a SQLite database to keep track of processed files and avoid reprocessing them.
# """

# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy files into the container at /app
COPY requirements.txt .
COPY watchrarr.py ./
COPY logs/watchrarr.log .
COPY db/extracted-files.db .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Install SQLite
RUN apt-get update && \
    apt-get install -y sqlite3

# Install the native unrar library
RUN apt-get update && \
    apt-get install -y wget build-essential && \
    wget https://www.rarlab.com/rar/unrarsrc-6.1.7.tar.gz && \
    tar -xvf unrarsrc-6.1.7.tar.gz && \
    cd unrar && \
    make lib && \
    make install-lib && \
    cd .. && \
    rm -rf unrar && \
    rm unrarsrc-6.1.7.tar.gz && \
    apt-get remove -y wget build-essential && \
    apt-get autoremove -y

# Create the db and logs folders, extracted-files.db, and watchrarr.log files
# RUN mkdir -p db logs && \
#     touch db/extracted-files.db && \
#     touch logs/watchrarr.log && \
#     chmod 666 logs/watchrarr.log && \
#     chmod 666 db/extracted-files.db
RUN mkdir -p watch

# Expose the volume for the entire /app directory
VOLUME /app

# Set the UnRAR library path
ENV UNRAR_LIB_PATH /usr/lib/libunrar.so

# Run the application
CMD ["python", "watchrarr.py"]

# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Install SQLite
RUN apt-get update && \
    apt-get install -y sqlite3

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World

# Make port 80 available to the world outside this container
EXPOSE 80

# Run the application
CMD ["python", "watchrarr.py"]

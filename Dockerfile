#**************************************
# MIT License
# Dockerfile to run the ddns.py script
#**************************************

# Use Python 3.10 on Debian Bullseye as the base image
FROM python:3.10-bullseye

# Set the working directory inside the container
WORKDIR /usr/src/app

# Update package list and install nano
RUN apt-get update && apt-get install -y nano

# Copy the requirements file into the container
COPY requirements.txt ./

# Install Python dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .

# Command to run when the container starts
CMD ["python", "./ddns.py"]

# Use an official Python runtime as a base image
ARG BASE_IMAGE=python:3.9-slim

FROM ${BASE_IMAGE} 

# Set the working directory inside the container
WORKDIR /app

# Copy the Python script into the container
COPY fips_python.py /app/

# Install any dependencies (if any) via pip
# For example, if you have a `requirements.txt`, uncomment the following line
# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r requirements.txt
# comment out to test successful case


RUN python -m pip install cryptography


# Execute the Python script when the container starts
CMD ["python", "fips_python.py"]


#docker build -t fips-test .
#docker run --rm fips-test
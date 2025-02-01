import subprocess
import docker

# Set the base image as an argument (example)
# Working case
# ARG = "python:3.8-slim"
# ARG = "python:slim-bookworm"
ARG = "python:3.9.20-slim-bullseye"

# failed case
#ARG = "python:3.14.0a2-slim-bullseye"
# Initialize the Docker client
client = docker.from_env()

# Pull the base image (ensure it exists locally)
try:
    print(f"Pulling image {ARG}...")
    client.images.pull(ARG)
    print(f"Image {ARG} pulled successfully.")
except docker.errors.ImageNotFound:
    print(f"Image '{ARG}' not found.")
except docker.errors.APIError as e:
    print(f"API error occurred while pulling the image: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

# Retrieve and print the image labels
try:
    image = client.images.get(ARG)
    labels = image.attrs.get('Config', {}).get('Labels', {})
    configs = image.attrs.get('Config', {})
    print(f"Configs: {configs}")
    print(f"Labels: {labels}")
except docker.errors.ImageNotFound:
    print(f"Image '{ARG}' not found.")
except Exception as e:
    print(f"An error occurred while retrieving image labels: {e}")

# Run the docker build command with the passed build argument
docker_command = ["docker", "build", "--build-arg", f"BASE_IMAGE={ARG}", "-t", "fips-test", "."]
try:
    print("Running docker build...")
    exit_code = subprocess.call(docker_command)
    print(f"Docker build exited with code {exit_code}")

    if exit_code == 0:
        print("Docker build succeeded.")
    else:
        print(f"Error occurred during Docker build. Exit code: {exit_code}")
except Exception as e:
    print(f"An error occurred while running docker build: {e}")
    raise SystemExit(1)  # Use `raise` to properly raise the exception

# Run the docker container using the built image
docker_command_run = ["docker", "run", "--rm", "fips-test"]
try:
    print("Running docker container...")
    exit_code = subprocess.call(docker_command_run)
    print(f"Docker run exited with code {exit_code}")

    if exit_code == 0:
        print("The container ran successfully.")
    else:
        print(f"An error occurred during Docker run. Exit code: {exit_code}")
except Exception as e:
    print(f"An error occurred while running the Docker container: {e}")

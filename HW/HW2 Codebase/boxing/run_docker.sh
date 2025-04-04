#!/bin/bash

# Variables
IMAGE_NAME=boxing_flask
CONTAINER_TAG=latest
HOST_PORT=5002
CONTAINER_PORT=5002
DB_VOLUME_PATH=  # Adjust this to the desired host path for the database persistence
BUILD=  # Set this to true if you want to build the image

# Check if we need to build the Docker image
if [ "$BUILD" = true ]; then
  echo "Building Docker image..."

else
  echo "Skipping Docker image build..."
fi

# Check if the database directory exists; if not, create it
if [ ! -d "${DB_VOLUME_PATH}" ]; then
  echo "Creating database directory at ${DB_VOLUME_PATH}..."

fi

# Stop and remove the running container if it exists
if [ "$(docker ps -q -a -f name=${IMAGE_NAME}_container)" ]; then
    echo "Stopping running container: ${IMAGE_NAME}_container"


    # Check if the stop was successful
    if [ $? -eq 0 ]; then
        echo "Removing container: ${IMAGE_NAME}_container"

    else
        echo "Failed to stop container: ${IMAGE_NAME}_container"
        exit 1
    fi
else
    echo "No running container named ${IMAGE_NAME}_container found."
fi

# Run the Docker container with the necessary ports and volume mappings
echo "Running Docker container..."

echo "Docker container is running on port ${HOST_PORT}."

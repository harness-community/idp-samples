ARG BASE_IMAGE=node:18-slim



# Stage 1: Build stage
FROM node:18-slim AS build

# Set the working directory in the container
WORKDIR /app

# Copy the package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install any dependencies (if you have additional dependencies, add them here)
RUN npm install

# Copy the application code to the container
COPY . .

# Stage 2: Test stage
FROM ${BASE_IMAGE}  AS test

# Set the working directory
WORKDIR /app

# Copy the application code and dependencies from the build stage
COPY --from=build /app /app

# Install OpenSSL (necessary for the fallback FIPS check in case /proc/sys/crypto/fips_enabled is not available)
RUN apt-get update && apt-get install -y openssl

# Run the Node.js script
CMD ["node", "fips_check.js"]

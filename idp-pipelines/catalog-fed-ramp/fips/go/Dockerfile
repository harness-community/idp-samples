ARG BASE_IMAGE=debian:bullseye-slim

# Stage 1: Build the Go program
FROM golang:1.21 AS builder

# Set the working directory
WORKDIR /app

# Copy the Go source code into the container
COPY fips_check.go .
COPY go.mod .

# Download Go modules and build the application
RUN go mod tidy
RUN go build -o fips-checker fips_check.go

# Stage 2: Testing the Go program
FROM ${BASE_IMAGE} AS stage

# Install dependencies (OpenSSL and others if needed)
RUN apt-get update && \
    apt-get install -y openssl gcc libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the built Go binary from the build stage
COPY --from=builder /app/fips-checker .

# Run the Go program
CMD ["./fips-checker"]
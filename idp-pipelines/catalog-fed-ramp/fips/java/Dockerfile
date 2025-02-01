# Stage 1: Build Stage (Using javac to compile the source code)
FROM openjdk:11-jdk-slim AS build

# Set the working directory
WORKDIR /app/src

# Copy the source code into the container
COPY src/* /app/src


# Compile the Java source code into .class files
RUN javac -d out -processor  FIPSCheck


# Create the .jar file from compiled .class files
RUN jar cf app.jar -C out .


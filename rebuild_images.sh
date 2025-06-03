#!/bin/bash
# Script to rebuild all Docker images with latest versions
# Created on June 2025

echo "Rebuilding Docker images with latest component versions..."
echo "Building Hadoop base image..."
docker build -t ppatcoding/hadoop-base:0.2 ./docker/hadoop/

echo "Building Airflow image..."
docker build -t ppatcoding/airflow:latest ./docker/airflow/

echo "Images rebuilt successfully!"
echo "You can now run 'docker compose up -d' to start the containers"

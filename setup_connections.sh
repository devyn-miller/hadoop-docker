#!/bin/bash
# setup_connections.sh - Script to set up connections in Airflow

# Check if Airflow container is running
if ! docker ps | grep -q "airflow-webserver"; then
    echo "Error: Airflow webserver container is not running."
    echo "Please start the containers with: docker compose up -d"
    exit 1
fi

echo "Setting up connections in Airflow..."

# Set up Spark connection
docker exec -it airflow-webserver bash -c "airflow connections add 'spark_default' \
    --conn-type 'spark' \
    --conn-host 'local[*]' \
    --conn-extra '{\"deploy-mode\": \"client\"}'"

# Set up PostgreSQL connection
docker exec -it airflow-webserver bash -c "airflow connections add 'postgres_default' \
    --conn-type 'postgres' \
    --conn-host 'postgres' \
    --conn-login 'airflow' \
    --conn-password 'airflow' \
    --conn-port '5432' \
    --conn-schema 'airflow'"

# Set up HDFS connection (optional but useful)
docker exec -it airflow-webserver bash -c "airflow connections add 'hdfs_default' \
    --conn-type 'hdfs' \
    --conn-host 'localhost' \
    --conn-port '9000'"

# Set up Hive connection
docker exec -it airflow-webserver bash -c "airflow connections add 'hive_cli_default' \
    --conn-type 'hive_cli' \
    --conn-host 'localhost' \
    --conn-port '10000' \
    --conn-schema 'default'"

echo "Connections have been set up successfully!"
echo "You can verify them in the Airflow UI under Admin > Connections"

# Using Hadoop and Airflow in the Docker Environment

This guide explains how to use the Hadoop ecosystem components with Apache Airflow in your Docker setup.

## Getting Started

1. **Start the environment**:
   ```bash
   docker compose up -d
   ```

2. **Verify the environment is running**:
   ```bash
   docker ps
   ```

   You should see the `airflow-webserver` and `airflow-database` containers running.

3. **Access the Airflow web interface**:
   Open your browser and go to: http://localhost:8080

## Working with Hadoop Components

### HDFS Operations

Connect to the container and use HDFS commands:

```bash
# Connect to the container
docker exec -it airflow-webserver bash

# List HDFS directories
hdfs dfs -ls /

# Create a directory
hdfs dfs -mkdir -p /user/airflow/data

# Upload local file to HDFS
hdfs dfs -put /path/to/local/file.txt /user/airflow/data/

# View a file in HDFS
hdfs dfs -cat /user/airflow/data/file.txt
```

### Hive Operations

```bash
# Connect to the container
docker exec -it airflow-webserver bash

# Start Hive CLI
hive

# Or run Hive queries directly
hive -e "SHOW DATABASES;"
hive -e "CREATE DATABASE IF NOT EXISTS test_db;"
hive -e "USE test_db; CREATE TABLE IF NOT EXISTS test_table (id INT, name STRING);"
```

### Spark Operations

```bash
# Connect to the container
docker exec -it airflow-webserver bash

# Start Spark shell
spark-shell

# Start PySpark
pyspark

# Submit a Spark job
spark-submit /path/to/spark/script.py
```

### Sqoop Operations

```bash
# Connect to the container
docker exec -it airflow-webserver bash

# List tables in a database
sqoop list-tables --connect jdbc:postgresql://postgres:5432/airflow \
  --username airflow --password airflow

# Import data from Postgres to HDFS
sqoop import --connect jdbc:postgresql://postgres:5432/airflow \
  --username airflow --password airflow \
  --table table_name --target-dir /user/airflow/data/table_name \
  -m 1
```

## Using the Example Airflow DAG

An example DAG has been included in `airflow/dags/hadoop_example_dag.py` that demonstrates:

1. Creating directories in HDFS
2. Generating and uploading sample data
3. Creating a Hive table and loading data
4. Processing data with Spark
5. Exporting data to PostgreSQL using Sqoop

To use this DAG:

1. Open the Airflow UI at http://localhost:8080
2. Enable the "hadoop_ecosystem_example" DAG
3. Trigger the DAG manually or wait for scheduled execution

## Using Helper Scripts

A utility script is provided to simplify common operations:

```bash
# Show HDFS status
./hadoop_utilities.sh hdfs-status

# List data in HDFS
./hadoop_utilities.sh list-data

# Show Hive tables
./hadoop_utilities.sh hive-tables

# Start Spark shell
./hadoop_utilities.sh spark-shell

# Start PySpark shell
./hadoop_utilities.sh pyspark

# Clean up test data
./hadoop_utilities.sh cleanup

# Check health of all components
./hadoop_utilities.sh health-check
```

## Troubleshooting

If you encounter issues:

1. **Check logs**:
   ```bash
   docker logs airflow-webserver
   ```

2. **Check component connectivity**:
   ```bash
   ./hadoop_utilities.sh health-check
   ```

3. **Common connection issues**:
   - Ensure PostgreSQL container is running
   - Verify port mappings in docker-compose.yml
   - Check network connectivity between containers

4. **Dependency issues**:
   As mentioned in the README, you might encounter dependency issues between components. If so:
   - Check version compatibility between Hadoop components
   - Verify Java version requirements
   - Look for missing libraries or conflicting dependencies

## Reference Documentation

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Apache Hadoop Documentation](https://hadoop.apache.org/docs/)
- [Apache Hive Documentation](https://hive.apache.org/documentation.html)
- [Apache Spark Documentation](https://spark.apache.org/documentation.html)
- [Apache Sqoop Documentation](https://sqoop.apache.org/docs/)

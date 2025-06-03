#!/bin/bash
# hadoop_utilities.sh - Helper script for common Hadoop operations

# Usage function
show_usage() {
    echo "Usage: $0 [command]"
    echo "Commands:"
    echo "  hdfs-status        - Show HDFS status and available space"
    echo "  list-data          - List data in the user's HDFS directory"
    echo "  hive-tables        - Show available Hive tables"
    echo "  spark-shell        - Launch Spark shell"
    echo "  pyspark            - Launch PySpark shell"
    echo "  cleanup            - Remove test data from HDFS"
    echo "  health-check       - Check status of all components"
    exit 1
}

# Check if Airflow container is running
check_container() {
    if ! docker ps | grep -q "airflow-webserver"; then
        echo "Error: Airflow webserver container is not running."
        echo "Please start the containers with: docker compose up -d"
        exit 1
    fi
}

# Execute command in container
exec_in_container() {
    docker exec -it airflow-webserver bash -c "$1"
}

# Main logic based on command argument
case "$1" in
    hdfs-status)
        check_container
        echo "HDFS Cluster Status:"
        exec_in_container "hdfs dfsadmin -report"
        ;;
    list-data)
        check_container
        echo "HDFS User Data:"
        exec_in_container "hdfs dfs -ls -R /user/airflow"
        ;;
    hive-tables)
        check_container
        echo "Hive Tables:"
        exec_in_container "hive -e 'SHOW DATABASES; USE default; SHOW TABLES;'"
        ;;
    spark-shell)
        check_container
        echo "Starting Spark Shell..."
        docker exec -it airflow-webserver spark-shell
        ;;
    pyspark)
        check_container
        echo "Starting PySpark..."
        docker exec -it airflow-webserver pyspark
        ;;
    cleanup)
        check_container
        echo "Cleaning up test data..."
        exec_in_container "hdfs dfs -rm -r -f /user/airflow/test_data"
        echo "Done!"
        ;;
    health-check)
        check_container
        echo "=== Hadoop Ecosystem Health Check ==="
        echo "1. HDFS Status:"
        exec_in_container "hdfs dfs -ls / > /dev/null && echo 'HDFS: OK' || echo 'HDFS: FAILED'"
        
        echo "2. Hive Connection:"
        exec_in_container "hive -e 'SHOW DATABASES;' > /dev/null && echo 'Hive: OK' || echo 'Hive: FAILED'"
        
        echo "3. Spark Setup:"
        exec_in_container "spark-shell --version > /dev/null && echo 'Spark: OK' || echo 'Spark: FAILED'"
        
        echo "4. Sqoop Version:"
        exec_in_container "sqoop version > /dev/null && echo 'Sqoop: OK' || echo 'Sqoop: FAILED'"
        
        echo "5. PostgreSQL Connection:"
        exec_in_container "PGPASSWORD=airflow psql -h postgres -U airflow -d airflow -c 'SELECT 1;' > /dev/null && echo 'PostgreSQL: OK' || echo 'PostgreSQL: FAILED'"
        ;;
    *)
        show_usage
        ;;
esac

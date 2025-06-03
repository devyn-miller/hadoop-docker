#!/usr/bin/env python
# weather_data_pipeline.py - Example DAG for processing weather data
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.apache.hive.operators.hive import HiveOperator

# Default arguments for DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'weather_data_pipeline',
    default_args=default_args,
    description='Process weather data using Hadoop ecosystem',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 6, 2),
    catchup=False,
    tags=['example', 'weather', 'processing'],
)

# Task 1: Download sample weather data
download_data = BashOperator(
    task_id='download_weather_data',
    bash_command='''
    mkdir -p /tmp/weather_data
    cat > /tmp/weather_data/sample_weather.csv << EOF
date,location,temp_c,humidity,pressure,weather_condition
2025-06-01,San Francisco,18,72,1012,Sunny
2025-06-01,New York,24,65,1008,Cloudy
2025-06-01,Chicago,22,68,1010,Rainy
2025-06-01,Miami,30,80,1005,Sunny
2025-06-01,Seattle,16,82,1015,Rainy
2025-06-02,San Francisco,19,70,1014,Sunny
2025-06-02,New York,25,62,1009,Sunny
2025-06-02,Chicago,20,72,1011,Cloudy
2025-06-02,Miami,31,78,1006,Sunny
2025-06-02,Seattle,15,85,1014,Rainy
EOF
    echo "Sample weather data created at /tmp/weather_data/sample_weather.csv"
    ''',
    dag=dag,
)

# Task 2: Create HDFS directory and upload data
upload_to_hdfs = BashOperator(
    task_id='upload_to_hdfs',
    bash_command='''
    hdfs dfs -mkdir -p /user/airflow/weather_data
    hdfs dfs -put -f /tmp/weather_data/sample_weather.csv /user/airflow/weather_data/
    hdfs dfs -ls /user/airflow/weather_data/
    ''',
    dag=dag,
)

# Task 3: Create Hive table for weather data
create_weather_table = HiveOperator(
    task_id='create_weather_table',
    hql="""
    CREATE TABLE IF NOT EXISTS weather_data (
        date STRING,
        location STRING,
        temp_c INT,
        humidity INT,
        pressure INT,
        weather_condition STRING
    )
    ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
    TBLPROPERTIES ('skip.header.line.count'='1');
    
    LOAD DATA INPATH '/user/airflow/weather_data/sample_weather.csv' 
    OVERWRITE INTO TABLE weather_data;
    
    SELECT * FROM weather_data LIMIT 5;
    """,
    dag=dag,
)

# Task 4: Create a Spark script for processing
create_spark_script = BashOperator(
    task_id='create_spark_script',
    bash_command='''
    cat > /usr/local/airflow/dags/process_weather.py << EOF
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, to_date, count, when

def process_weather_data():
    # Initialize Spark session
    spark = SparkSession.builder \\
        .appName("Weather Data Processing") \\
        .enableHiveSupport() \\
        .getOrCreate()
    
    # Read data from Hive
    weather_df = spark.sql("SELECT * FROM weather_data")
    
    # Convert date string to date type
    weather_df = weather_df.withColumn("date", to_date(col("date"), "yyyy-MM-dd"))
    
    # Calculate average temperature by location
    avg_temp_by_location = weather_df.groupBy("location") \\
        .agg(
            avg("temp_c").alias("avg_temperature"),
            avg("humidity").alias("avg_humidity"),
            count("*").alias("days_count")
        )
    
    # Calculate weather frequency
    weather_frequency = weather_df.groupBy("location", "weather_condition").count() \\
        .orderBy("location", col("count").desc())
    
    # Add temperature category
    categorized_weather = weather_df.withColumn(
        "temp_category",
        when(col("temp_c") < 18, "cold")
        .when(col("temp_c") < 25, "mild")
        .otherwise("hot")
    )
    
    # Show results
    print("Average Temperature by Location:")
    avg_temp_by_location.show()
    
    print("Weather Condition Frequency by Location:")
    weather_frequency.show()
    
    print("Categorized Weather Data:")
    categorized_weather.show()
    
    # Save results to HDFS
    avg_temp_by_location.write.mode("overwrite").csv("/user/airflow/weather_data/avg_temp")
    weather_frequency.write.mode("overwrite").csv("/user/airflow/weather_data/weather_freq")
    categorized_weather.write.mode("overwrite").csv("/user/airflow/weather_data/categorized")
    
    return "Weather data processed successfully"

if __name__ == "__main__":
    process_weather_data()
EOF
    chmod +x /usr/local/airflow/dags/process_weather.py
    echo "Spark processing script created"
    ''',
    dag=dag,
)

# Task 5: Run the Spark job
run_spark_job = SparkSubmitOperator(
    task_id='process_weather_with_spark',
    application='/usr/local/airflow/dags/process_weather.py',
    conn_id='spark_default',
    verbose=True,
    dag=dag,
)

# Task 6: Create summary tables in Hive
create_summary_tables = HiveOperator(
    task_id='create_summary_tables',
    hql="""
    -- Create table for average temperatures
    CREATE TABLE IF NOT EXISTS avg_temperature_by_location (
        location STRING,
        avg_temperature DOUBLE,
        avg_humidity DOUBLE,
        days_count BIGINT
    )
    ROW FORMAT DELIMITED FIELDS TERMINATED BY ',';
    
    -- Load processed data
    LOAD DATA INPATH '/user/airflow/weather_data/avg_temp/part-*' 
    OVERWRITE INTO TABLE avg_temperature_by_location;
    
    -- Query the results
    SELECT * FROM avg_temperature_by_location ORDER BY avg_temperature DESC;
    """,
    dag=dag,
)

# Task 7: Export results to PostgreSQL
export_to_postgres = BashOperator(
    task_id='export_to_postgres',
    bash_command='''
    # Create PostgreSQL table
    PGPASSWORD=airflow psql -h postgres -U airflow -d airflow -c "
    DROP TABLE IF EXISTS weather_summary;
    CREATE TABLE weather_summary (
        location VARCHAR(100),
        avg_temperature DOUBLE PRECISION,
        avg_humidity DOUBLE PRECISION,
        days_count INT
    );"
    
    # Export using Sqoop
    sqoop export \
    --connect jdbc:postgresql://postgres:5432/airflow \
    --username airflow \
    --password airflow \
    --table weather_summary \
    --export-dir /user/airflow/weather_data/avg_temp \
    --input-fields-terminated-by ',' \
    --columns "location,avg_temperature,avg_humidity,days_count" \
    -m 1
    
    # Verify data was exported
    echo "Verifying exported data:"
    PGPASSWORD=airflow psql -h postgres -U airflow -d airflow -c "SELECT * FROM weather_summary;"
    ''',
    dag=dag,
)

# Define task dependencies
download_data >> upload_to_hdfs >> create_weather_table >> create_spark_script
create_spark_script >> run_spark_job >> create_summary_tables >> export_to_postgres

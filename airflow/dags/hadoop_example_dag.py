#!/usr/bin/env python
# hadoop_example_dag.py - Sample DAG showcasing Hadoop ecosystem usage in Airflow
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
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
    'hadoop_ecosystem_example',
    default_args=default_args,
    description='Sample DAG using Hadoop ecosystem components',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 6, 2),
    catchup=False,
    tags=['example', 'hadoop', 'spark', 'hive', 'sqoop'],
)

# Task 1: Create HDFS directory structure
hdfs_mkdir = BashOperator(
    task_id='create_hdfs_directory',
    bash_command='hdfs dfs -mkdir -p /user/airflow/test_data',
    dag=dag,
)

# Task 2: Generate sample data and upload to HDFS
generate_data = BashOperator(
    task_id='generate_sample_data',
    bash_command='''
    echo "1,John,35
2,Jane,28
3,Jim,42
4,Sarah,24
5,Michael,55" > /tmp/sample_data.csv && 
    hdfs dfs -put -f /tmp/sample_data.csv /user/airflow/test_data/
    ''',
    dag=dag,
)

# Task 3: Create Hive table and load data
create_hive_table = HiveOperator(
    task_id='create_hive_table',
    hql="""
    CREATE TABLE IF NOT EXISTS users (
        id INT,
        name STRING,
        age INT
    )
    ROW FORMAT DELIMITED FIELDS TERMINATED BY ',';
    
    LOAD DATA INPATH '/user/airflow/test_data/sample_data.csv' 
    OVERWRITE INTO TABLE users;
    """,
    dag=dag,
)

# Task 4: Run Spark job to process data
spark_job = SparkSubmitOperator(
    task_id='run_spark_job',
    application='/usr/local/airflow/dags/spark_process_users.py',
    conn_id='spark_default',
    verbose=True,
    application_args=['/user/airflow/test_data/processed'],
    dag=dag,
)

# Task 5: Verify processed data
verify_data = BashOperator(
    task_id='verify_processed_data',
    bash_command='hdfs dfs -ls /user/airflow/test_data/processed && hdfs dfs -cat /user/airflow/test_data/processed/part-* | head -10',
    dag=dag,
)

# Task 6: Create PostgreSQL table for export
create_pg_table = BashOperator(
    task_id='create_postgres_table',
    bash_command='''
    PGPASSWORD=airflow psql -h postgres -U airflow -d airflow -c "
    DROP TABLE IF EXISTS processed_users;
    CREATE TABLE processed_users (
        id INT,
        name VARCHAR(100),
        age INT,
        category VARCHAR(20)
    );"
    ''',
    dag=dag,
)

# Task 7: Export data from HDFS to PostgreSQL using Sqoop
sqoop_export = BashOperator(
    task_id='sqoop_export',
    bash_command="""
    sqoop export \
    --connect jdbc:postgresql://postgres:5432/airflow \
    --username airflow \
    --password airflow \
    --table processed_users \
    --export-dir /user/airflow/test_data/processed \
    --input-fields-terminated-by ',' \
    --columns "id,name,age,category" \
    -m 1
    """,
    dag=dag,
)

# Task 8: Verify data in PostgreSQL
verify_pg_data = BashOperator(
    task_id='verify_postgres_data',
    bash_command='PGPASSWORD=airflow psql -h postgres -U airflow -d airflow -c "SELECT * FROM processed_users LIMIT 10;"',
    dag=dag,
)

# Define task dependencies
hdfs_mkdir >> generate_data >> create_hive_table >> spark_job >> verify_data
verify_data >> create_pg_table >> sqoop_export >> verify_pg_data

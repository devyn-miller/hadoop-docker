#!/usr/bin/env python
# spark_process_users.py - Sample PySpark script for processing user data
from pyspark.sql import SparkSession
import sys

def main():
    """
    Process users data using Spark
    - Reads user data from Hive
    - Adds age category
    - Writes processed data to HDFS
    """
    # Initialize Spark session with Hive support
    spark = SparkSession.builder \
        .appName("Process Users") \
        .enableHiveSupport() \
        .getOrCreate()
    
    # Read data from Hive table
    users_df = spark.sql("SELECT * FROM users")
    
    # Process data - add a category column based on age
    from pyspark.sql.functions import when, col
    processed_df = users_df.withColumn(
        "category",
        when(col("age") < 30, "young")
        .when(col("age") < 50, "middle-aged")
        .otherwise("senior")
    )
    
    # Show results for debugging
    print("Processed data:")
    processed_df.show()
    
    # Write processed data back to HDFS
    output_path = sys.argv[1] if len(sys.argv) > 1 else "/user/airflow/test_data/processed"
    processed_df.write.mode("overwrite").csv(output_path)
    
    print(f"Data successfully written to {output_path}")
    spark.stop()

if __name__ == "__main__":
    main()

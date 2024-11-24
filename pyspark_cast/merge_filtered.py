import os
import time
from pyspark.sql import SparkSession

os.environ["PYSPARK_PYTHON"] = r"C:\\Python310\\python.exe"
os.environ["PYSPARK_DRIVER_PYTHON"] = r"C:\\Python310\\python.exe"

spark: SparkSession = SparkSession.builder \
    .master("local[6]") \
    .appName("Wikipedia Merge Parts") \
    .config("spark.executor.memory", "6g") \
    .config("spark.driver.memory", "6g") \
    .config("spark.executor.memoryOverhead", "2g") \
    .config("spark.executor.cores", "2") \
    .config("spark.dynamicAllocation.enabled", "true") \
    .config("spark.shuffle.service.enabled", "true") \
    .config("spark.driver.maxResultSize", "2g") \
    .config("spark.network.timeout", "1200s") \
    .config("spark.sql.broadcastTimeout", "1200s") \
    .config("spark.driver.maxResultSize", "4g") \
    .config("spark.sql.shuffle.partitions", "500") \
    .config("spark.executor.heartbeatInterval", "60s") \
    .config("spark.sql.execution.pythonUTF8StringEncoding", "true") \
    .getOrCreate()
sc = spark.sparkContext

OUTPUT_PATH = r".\\OUTPUT_FOLDER"
MERGE_PATH = r".\\FILTERED_MERGED"

start = time.time()
rdd = sc.textFile(f"{OUTPUT_PATH}/chunk_*/part-*")

filtered_rdd = rdd.filter(lambda line: line.strip() != "")

filtered_rdd.coalesce(1).saveAsTextFile(MERGE_PATH)

spark.stop()
end = time.time()

print(f"Time to execute: {end - start:.2f}s")
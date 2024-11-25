import os
import time
from pyspark.sql import SparkSession

# Paths for input and output
PHASE_1_CSV = r"..\\data\\phase_1.csv"
PHASE_2_CSV = r"..\\data\\phase_2.csv"
OUTPUT_PATH = r"..\\data\\FINAL_DATA"

# Spark setup
os.environ["PYSPARK_PYTHON"] = r"C:\\Python310\\python.exe"
os.environ["PYSPARK_DRIVER_PYTHON"] = r"C:\\Python310\\python.exe"

spark: SparkSession = SparkSession.builder \
    .master("local[6]") \
    .appName("Merge CSV files") \
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

start = time.time()
schema1 = ["game_name", "released", "publishers", "developers", "moby_score", "critics_score", "players_score", "genre", "perspective", "gameplay", "description"]
schema2 = ["game_name", "engine", "platforms", "director", "producer", "designer", "programmer", "artist", "writer", "composer"]

df1 = spark.read.csv(PHASE_1_CSV, header=False, sep="|").toDF(*schema1)
df2 = spark.read.csv(PHASE_2_CSV, header=False, sep="|").toDF(*schema2)

merged_df = df1.join(df2, on=["game_name"], how="full_outer")
merged_df = merged_df.fillna("N/A")
single_partition_df = merged_df.coalesce(1)
single_partition_df.write.csv(
        OUTPUT_PATH,
        header=False,
        mode="overwrite",
        sep="|",
        lineSep="\n"
    )
spark.stop()
end = time.time()

print(f"Time to execute: {end - start:.2f}s")
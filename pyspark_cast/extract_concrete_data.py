import os
import re
import time
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

# Paths for input and output
FILEPATH = r".\\FILTERED_MERGED\\part-00000"
OUTPUTPATH = r".\\EXTRACTED_INFO"

# Spark setup
os.environ["PYSPARK_PYTHON"] = r"C:\\Python310\\python.exe"
os.environ["PYSPARK_DRIVER_PYTHON"] = r"C:\\Python310\\python.exe"

spark: SparkSession = SparkSession.builder \
    .master("local[6]") \
    .appName("Extract conrete data") \
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

#regexes for information extraction
TITLE = r"<title>(.+)(?=<\/title>)" #not from infobox, because title is sometimes missing there, but not the page title
ENGINE = r"\|\s*engine\s=(.+)(?:\n)"
PLATFORMS = r"\|\s*platforms\s*=\s*(.+)(?:\n)"
DIRECTOR = r"\|\s*director\s*=\s*(.+)(?:\n)"
PRODUCER = r"\|\s*producer\s*=\s*(.+)(?:\n)"
DESIGNER = r"\|\s*designer\s*=\s*(.+)(?:\n)"
PROGRAMMER = r"\|\s*programmer\s*=\s*(.+)(?:\n)"
ARTIST = r"\|\s*artist\s*=\s*(.+)(?:\n)"
WRITER = r"\|\s*writer\s*=\s*(.+)(?:\n)"
COMPOSER = r"\|\s*composer\s*=\s*(.+)(?:\n)"

def clean_text(text):
    text = re.sub(r"[\[\]\{\}\|]|Unbulleted list|&lt;|&gt;", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def edit_title(title: str):
    title = title.lower()
    title = re.sub(r":|'|\(\s*(?:\d\d\d\d)?\s*video\s*game\s*\)", "", title)
    title = "-".join(title.strip().split(" "))

    return title

def extract_page_info(page: str) -> dict:
    title_match = clean_text((lambda m: m.group(1) if m else "N/A")(re.search(TITLE, page)))
    engine_match = clean_text((lambda m: m.group(1) if m else "N/A")(re.search(ENGINE, page)))
    platforms_match = clean_text((lambda m: m.group(1) if m else "N/A")(re.search(PLATFORMS, page)))
    director_match = clean_text((lambda m: m.group(1) if m else "N/A")(re.search(DIRECTOR, page)))
    producer_match = clean_text((lambda m: m.group(1) if m else "N/A")(re.search(PRODUCER, page)))
    designer_match = clean_text((lambda m: m.group(1) if m else "N/A")(re.search(DESIGNER, page)))
    programmer_match = clean_text((lambda m: m.group(1) if m else "N/A")(re.search(PROGRAMMER, page)))
    artist_match = clean_text((lambda m: m.group(1) if m else "N/A")(re.search(ARTIST, page)))
    writer_match = clean_text((lambda m: m.group(1) if m else "N/A")(re.search(WRITER, page)))
    composer_match = clean_text((lambda m: m.group(1) if m else "N/A")(re.search(COMPOSER, page)))
    
    title_match = edit_title(title_match)

    return {
        "title": title_match,
        "engine": engine_match,
        "platforms": platforms_match,
        "director": director_match,
        "producer": producer_match,
        "designer": designer_match,
        "programmer": programmer_match,
        "artist": artist_match,
        "writer": writer_match,
        "composer": composer_match,
    }

#Yield pages from dump
def page_generator(filepath: str):
    with open(filepath, "rt", encoding="utf-8") as file:
        buffer = []
        in_page = False
        
        for line in file:
            if "<page>" in line:
                in_page = True
                buffer = []
            if in_page:
                buffer.append(line)
            if "</page>" in line and in_page:
                yield "".join(buffer)
                in_page = False
                 
def process_wiki_dump(file_path, output_path):
    os.makedirs(output_path, exist_ok=True)
    
    schema = StructType([
        StructField("title", StringType(), True),
        StructField("engine", StringType(), True),
        StructField("platforms", StringType(), True),
        StructField("director", StringType(), True),
        StructField("producer", StringType(), True),
        StructField("designer", StringType(), True),
        StructField("programmer", StringType(), True),
        StructField("artist", StringType(), True),
        StructField("writer", StringType(), True),
        StructField("composer", StringType(), True),
    ])
    
    pages = list(page_generator(file_path))
    rdd = sc.parallelize(pages)
    print("Number of video game pages: ", rdd.count())
    extracted_rdd = rdd.map(extract_page_info)
    df = spark.createDataFrame(extracted_rdd, schema=schema)
    
    single_partition_df = df.coalesce(1)
    single_partition_df.write.csv(
        output_path,
        header=False,
        mode="overwrite",
        sep="|",
        lineSep="\n"
    )

if __name__ == "__main__":
    start = time.time()
    process_wiki_dump(FILEPATH, OUTPUTPATH)
    spark.stop()
    end = time.time()
    
    print(f"Time to execute: {end - start:.2f}s")
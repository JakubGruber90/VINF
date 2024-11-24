import os
import re
import bz2
import time
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

# Paths for input and output
FILEPATH = r".\\enwiki-latest-pages-articles1.xml-p1p41242.bz2"
OUTPUTPATH = r".\\OUTPUT_FOLDER"

# Spark setup
os.environ["PYSPARK_PYTHON"] = r"C:\\Python310\\python.exe"
os.environ["PYSPARK_DRIVER_PYTHON"] = r"C:\\Python310\\python.exe"

spark: SparkSession = SparkSession.builder \
    .master("local[6]") \
    .appName("Wikipedia XML Processing") \
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

# Regexes for video game page filtering
#namespace regex 0 -> namespace for Main/Article
NAMESPACE_REGEX = r"<ns>0"

#regex for redirect page
REDIRECT_REGEX = r"<redirect.+?/>"

#video game page regexes
video_game_title = r"(<title>.+?[Vv]ideo [Gg]ame(?!\s+[Ss]eries|\s+[Cc]ompany).+?</title>)"
video_game_infobox = r"\{\{\s*[Ii]nfobox\s+[Vv]ideo\s+[Gg]ame"
video_game_short_desc = r"({{Short description\|.+?video game}})"
video_game_categories = r"(\[\[Category:.*?(?:[Vv]ideo games|[Mm]ultiplayer games|[Pp]lay[Ss]tation|[Xx][Bb]ox|[Bb]rowser games|[Ff]irst-[Pp]erson [Ss]hooter|[Gg]ame [Oo]f [Tt]he [Yy]ear|[Gg]ame [Aa]ward|[Ww]indows [Gg]ames|IOS [Gg]ames).*?\]\])"

VIDEO_GAME_FILTER_REGEXES = {
    video_game_title,
    video_game_short_desc,
    video_game_infobox,
}

INFOBOX_REGEX = r"\{\{\s*[Ii]nfobox\s+[Vv]ideo\s+[Gg]ame(.+?)\}\}"
TITLE_REGEX = r"<title>(.+?)</title>"

def extract_infobox(page: str):
    title_match = re.search(TITLE_REGEX, page)
    infobox_match = re.search(INFOBOX_REGEX, page, re.DOTALL)
    if not title_match or not infobox_match:
        return None
    title = title_match.group(1).strip()
    infobox_content = infobox_match.group(1).strip()
    
    infobox_dict = {}
    for line in infobox_content.split("\n"):
        if "=" in line:
            key, value = map(str.strip, line.split("=", 1))
            infobox_dict[key] = value
    
    return (title, infobox_dict)

# Filter function
def filter_page(page: str) -> bool:
    if not re.search(NAMESPACE_REGEX, page):
        return None
    
    if re.search(REDIRECT_REGEX, page):
        return None
    
    for pattern in VIDEO_GAME_FILTER_REGEXES:
        if re.search(pattern, page):
            return extract_infobox(page)
    return None

#Yield pages from dump
def page_generator(filepath: str):
    with bz2.open(filepath, "rt", encoding="utf-8") as file:
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
     
def process_chunk_with_spark(chunk, output_path, chunk_counter):
    rdd = sc.parallelize(chunk)
    extracted_rdd = rdd.map(filter_page).filter(lambda x: x is not None)
    
    results = extracted_rdd.collect()
    processed_results = []
    for title, infobox in results:
        flattened_infobox = "; ".join(f"{k}: {v}" for k, v in infobox.items())
        processed_results.append((title, flattened_infobox))
        
    if processed_results:
        schema = StructType([
            StructField("Title", StringType(), True),
            StructField("Infobox", StringType(), True)
        ])

        df = spark.createDataFrame(processed_results, schema=schema)
        chunk_output_path = os.path.join(output_path, f"chunk_{chunk_counter}.csv")
        df.write.csv(chunk_output_path, header=True, mode="overwrite")
        print(f"Saved chunk {chunk_counter} to {chunk_output_path}")
    else:
        print(f"No relevant pages in chunk {chunk_counter}.")
            
def process_wiki_dump_in_chunks(file_path, output_path, chunk_size=20000):
    chunk_counter = 0
    current_chunk = []
    os.makedirs(output_path, exist_ok=True)
    
    for page in page_generator(file_path):
        current_chunk.append(page)
        
        if len(current_chunk) >= chunk_size:
            process_chunk_with_spark(current_chunk, output_path, chunk_counter)
            current_chunk = []
            chunk_counter +=1
        
    if current_chunk:
        print(f"Processing final chunk {chunk_counter}...")
        process_chunk_with_spark(current_chunk, output_path, chunk_counter)

if __name__ == "__main__":
    start = time.time()
    process_wiki_dump_in_chunks(FILEPATH, OUTPUTPATH)
    spark.stop()
    end = time.time()
    
    print(f"Time to execute: {end - start:.2f}s")
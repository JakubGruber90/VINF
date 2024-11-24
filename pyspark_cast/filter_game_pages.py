import os
import re
import bz2
import time
from pyspark.sql import SparkSession

# Paths for input and output
FILEPATH = r".\\enwiki-latest-pages-articles.xml.bz2"
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

# Filter function
def filter_page(page: str) -> bool:
    if not re.search(NAMESPACE_REGEX, page):
        return False
    
    if re.search(REDIRECT_REGEX, page):
        return False
    
    for pattern in VIDEO_GAME_FILTER_REGEXES:
        if re.search(pattern, page):
            return True
    return False

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
    filtered_rdd = rdd.filter(filter_page)
    chunk_output_path = os.path.join(output_path, f"chunk_{chunk_counter}")
    filtered_rdd.saveAsTextFile(chunk_output_path)
    print(f"Saved chunk {chunk_counter} to {chunk_output_path}")
            
def process_wiki_dump_in_chunks(file_path, output_path, chunk_size=40000):
    chunk_counter = 0
    current_chunk = []
    
    for page in page_generator(file_path):
        current_chunk.append(page)
        
        if len(current_chunk) >= chunk_size:
            process_chunk_with_spark(current_chunk, output_path, chunk_counter)
            current_chunk = []
            chunk_counter += 1
    
    if current_chunk:
        process_chunk_with_spark(current_chunk, output_path, chunk_counter)

    print(f"Processed and saved {chunk_counter + 1} chunks.")

if __name__ == "__main__":
    start = time.time()
    process_wiki_dump_in_chunks(FILEPATH, OUTPUTPATH)
    spark.stop()
    end = time.time()
    
    print(f"Time to execute: {end - start:.2f}s")
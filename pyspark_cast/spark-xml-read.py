from pyspark.sql import SparkSession
from pyspark import SparkConf
from pyspark.sql.types import StructType, StructField, StringType

conf = SparkConf().setAppName("Test-xml").set("spark.jars.packages", "com.databricks:spark-xml_2.12:0.14.0")

# Initialize Spark session
spark = SparkSession.builder.config(conf=conf).getOrCreate()

# Define the schema for the XML file
xml_schema = StructType([
    StructField('title', StringType(), False),
    StructField('revision',
        StructType([StructField('text', StringType(), False)]),
    False)
])

# Read the XML file (use file:// to specify a local path)
df = spark.read.format("com.databricks.spark.xml") \
    .option("rowTag", "page") \
    .schema(xml_schema) \
    .load(r'file:///C:/FIIT_STU/ING_studium/1.rocnik/zimny_semester/VINF/pyspark_cast/OUTPUT_FOLDER/test.xml')  # Adjust this path to your actual local file

# Print the schema of the loaded XML
df.printSchema()

# Select only the 'title' column and write to JSON
df1 = df.select("title")
df1.write \
    .mode('overwrite') \
    .text(r'file:///C:/FIIT_STU/ING_studium/1.rocnik/zimny_semester/VINF/pyspark_cast/OUTPUT_FOLDER/titles')  # Adjust path for local output

# Select only the 'revision.text' column and write to JSON
df2 = df.select("revision.text")
df2.write \
    .mode('overwrite') \
    .text(r'file:///C:/FIIT_STU/ING_studium/1.rocnik/zimny_semester/VINF/pyspark_cast/OUTPUT_FOLDER/texts')  # Adjust path for local output

# Select both 'title' and 'revision.text' columns and write to JSON
df3 = df.select("title", "revision.text")
df3.write \
    .mode('overwrite') \
    .text(r'file:///C:/FIIT_STU/ING_studium/1.rocnik/zimny_semester/VINF/pyspark_cast/OUTPUT_FOLDER/together')  # Adjust path for local output

import sqlite3
import csv

import mysql.connector
import pandas as pd



HOST     = '127.0.0.1'
DATABASE = 'local_norp'
USER     = 'root'
PASSWORD = 'your password'
# ----------------------------------------------------------------------------------------------------------------------------
# CREATE DATABASE
# ----------------------------------------------------------------------------------------------------------------------------
conn = mysql.connector.connect(
    host=HOST,
    user=USER,
    password=PASSWORD
)

# Create a cursor object
cursor = conn.cursor()

# Drop the database if it exists
cursor.execute("DROP DATABASE IF EXISTS {}".format(DATABASE))
print(f"Dropped {DATABASE} database successfully.")

# Create the database
cursor.execute("CREATE DATABASE {}".format(DATABASE))
print(f"Created {DATABASE} successfully.")

# Use the database
cursor.execute("USE {}".format(DATABASE))

# Commit the changes
conn.commit()

if conn.is_connected():
    cursor.close()
    conn.close()
    print("MySQL connection is closed.")

# Connect to the database
conn = mysql.connector.connect(
    host=HOST,
    user=USER,
    password=PASSWORD,
    database=DATABASE
)

# Create a cursor object
cursor = conn.cursor()
print("Connection Successful")

# Create the table if it does not already exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS economic_income_and_benefits (
    year DECIMAL NOT NULL, 
    id VARCHAR(14) NOT NULL, 
    zipcode VARCHAR(11) NOT NULL, 
    total_households DECIMAL NOT NULL, 
    median_household_income DECIMAL, 
    mean_household_income DECIMAL,
    PRIMARY KEY (year, id)
)
""")
cursor.execute("""
CREATE TABLE `nyc_crime_data` (
	`Crime_ID` DECIMAL(38, 0) NOT NULL  KEY,
	`Report` VARCHAR(14) NOT NULL, 
	`Crime_Date` DATE, 
	`Crime_Time` TIME NOT NULL, 
	`Crime_Class` VARCHAR(11) NOT NULL, 
	`Crime_Type` VARCHAR(36) NOT NULL, 
	`Area_Name` VARCHAR(13) NOT NULL, 
	`Latitude` DECIMAL(38, 15), 
	`Longitude` DECIMAL(38, 14)
);
""")
cursor.execute("""
CREATE TABLE `nyc_criminal_crime` (
    `Entry_#` INT NOT NULL KEY,
    `Report` VARCHAR(14) NOT NULL, 
    `first_name` VARCHAR(14) NOT NULL, 
    `last_name` VARCHAR(14) NOT NULL, 
    `DOB` DATE NOT NULL,
    `height` VARCHAR(14),
    `criminal_id` INT NOT NULL
);
""")

# Function to upload data from a text file
def upload_data_from_file(file_path, insert_query):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header if present

        # Insert data row by row
        for row in reader:
            row = [None if value == "NULL" or value == "" else value for value in row]
            cursor.execute(insert_query, row)
    conn.commit()

# Path to the text file with data
table_data = {
    # "economic_income_and_benefits": {
    #     "file_path":"test_economic_income_and_benefits_data.txt",
    #     "insert_query": "INSERT INTO economic_income_and_benefits (year, id, zipcode, total_households, median_household_income, mean_household_income) VALUES (%s, %s, %s, %s, %s, %s)",
    # },
    "nyc_crime_data": {
        "file_path":"test_nyc_crime_data.txt",
        "insert_query": "INSERT INTO nyc_crime_data (Crime_ID, `Report`, Crime_Date, Crime_Time, Crime_Class, Crime_Type, Area_Name, Latitude, Longitude) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
    },    
    "nyc_criminal_crime": {
        "file_path":"test_nyc_criminal_crime.txt",
        "insert_query": "INSERT INTO nyc_criminal_crime (`Entry_#`, `Report`,first_name,last_name,DOB,height,criminal_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    },    
}

for table in table_data:
    upload_data_from_file(table_data[table]["file_path"], table_data[table]["insert_query"])
    print(f"Done for {table}")

# Close the database connection
conn.close()
print("Data uploaded successfully.")

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

#! US SHOOTINGS
cursor.execute("""
CREATE TABLE us_shootings (
    IncidentID INT PRIMARY KEY,
    Address TEXT,
    IncidentDate DATE,
    State VARCHAR(50),
    CityOrCountry VARCHAR(100),
    VictimsKilled INT,
    VictimsInjured INT,
    SuspectsInjured INT,
    SuspectsKilled INT,
    SuspectsArrested INT
);
""")

cursor.execute("""
CREATE TABLE experiencing_homelessness_age_demographics (
    CALENDAR_YEAR VARCHAR(10),
    LOCATION VARCHAR(100),
    AGE_GROUP_PUBLIC VARCHAR(20),
    EXPERIENCING_HOMELESSNESS_CNT INT
);
""")

cursor.execute("""
CREATE TABLE us_population (
    CensurYear INT,
    State VARCHAR(100),
    PopulationCount INT
);
""")

cursor.execute("""
CREATE TABLE food_access (
    CensusTract BIGINT,
    State VARCHAR(100),
    County VARCHAR(100),
    Urban BOOLEAN,
    Pop2010 INT,
    Ohu2010 INT,
    LILATracts_1And10 BOOLEAN,
    LILATracts_halfAnd10 BOOLEAN,
    LILATracks_1And20 BOOLEAN,
    LILATractsVehicle BOOLEAN,
    HUNVFlag BOOLEAN,
    LowIncomeTracts BOOLEAN,
    PovertyRate FLOAT,
    MedianFamilyIncome FLOAT,
    LA1and10 BOOLEAN,
    LAhalfand10 BOOLEAN,
    LA1and20 BOOLEAN,
    LATracts_half BOOLEAN,
    LATracts1 BOOLEAN,
    LATracts10 BOOLEAN,
    LATracts20 BOOLEAN,
    LATractsVehicle_20 BOOLEAN,
    LAPOP1_10 FLOAT,
    LAPOP05_10 FLOAT,
    LAPOP1_20 FLOAT,
    LALOWI1_10 FLOAT,
    LALOWI05_10 FLOAT,
    LALOWI1_20 FLOAT,
    lapophalf FLOAT,
    lalowihalf FLOAT,
    lakidshalf FLOAT,
    laseniorshalf FLOAT,
    lawhitehalf FLOAT,
    lablackhalf FLOAT,
    laasianhalf FLOAT,
    lanhopihalf FLOAT,
    laaianhalf FLOAT,
    laomultirhalf FLOAT,
    lahisphalf FLOAT,
    lahunvhalf FLOAT,
    lasnaphalf FLOAT,
    lapop1 FLOAT,
    lalowi1 FLOAT,
    lakids1 FLOAT,
    laseniors1 FLOAT,
    lawhite1 FLOAT,
    lablack1 FLOAT,
    laasian1 FLOAT,
    lanhopi1 FLOAT,
    laaian1 FLOAT,
    laomultir1 FLOAT,
    lahisp1 FLOAT,
    lahunv1 FLOAT,
    lasnap1 FLOAT,
    lapop10 FLOAT,
    lalowi10 FLOAT,
    lakids10 FLOAT,
    laseniors10 FLOAT,
    lawhite10 FLOAT,
    lablack10 FLOAT,
    laasian10 FLOAT,
    lanhopi10 FLOAT,
    laaian10 FLOAT,
    laomultir10 FLOAT,
    lahisp10 FLOAT,
    lahunv10 FLOAT,
    lasnap10 FLOAT,
    lapop20 FLOAT,
    lalowi20 FLOAT,
    lakids20 FLOAT,
    laseniors20 FLOAT,
    lawhite20 FLOAT,
    lablack20 FLOAT,
    laasian20 FLOAT,
    lanhopi20 FLOAT,
    laaian20 FLOAT,
    laomultir20 FLOAT,
    lahisp20 FLOAT,
    lahunv20 FLOAT,
    lasnap20 FLOAT,
    TractLOWI FLOAT,
    TractKids FLOAT,
    TractSeniors FLOAT,
    TractWhite FLOAT,
    TractBlack FLOAT,
    TractAsian FLOAT,
    TractNHOPI FLOAT,
    TractAIAN FLOAT,
    TractOMultir FLOAT,
    TractHispanic FLOAT,
    TractHUNV FLOAT,
    TractSNAP FLOAT
);
""")
cursor.execute("""CREATE TABLE us_population_county (
    PopulationCount INT,
    County VARCHAR(100)
);
""")

# Function to upload data from a text file
def upload_data_from_file(file_path, insert_query):
    with open(file_path, 'r') as file:
        reader = csv.reader(file, delimiter=";")

        # Insert data row by row
        for row in reader:
            cleaned_row = [
                None if field.strip() == "" else 
                1 if field.strip().lower() == "true" else 
                0 if field.strip().lower() == "false" else 
                field.strip() 
                for field in row
            ]
            cursor.execute(insert_query, cleaned_row)
    conn.commit()

# Path to the text file with data
table_data = {
    "experiencing_homelessness_age_demographics": {
        "file_path":"experiencing_homelessness_age_demographics.txt",
        "insert_query": """INSERT INTO experiencing_homelessness_age_demographics (
    	CALENDAR_YEAR, LOCATION, AGE_GROUP_PUBLIC, EXPERIENCING_HOMELESSNESS_CNT
		) VALUES (%s, %s, %s, %s);"""
	},    
    "us_shootings": {
        "file_path":"us_shootings.txt",
        "insert_query": """INSERT INTO us_shootings (
            IncidentID, Address, IncidentDate, State, CityOrCountry, VictimsKilled, VictimsInjured, 
            SuspectsInjured, SuspectsKilled, SuspectsArrested
        ) VALUES (%s, %s, (STR_TO_DATE(%s,'%M %d, %Y')), %s, %s, %s, %s, %s, %s, %s);
        """
    },
    "us_population_county": {
        "file_path":"us_population_county.txt",
        "insert_query": """INSERT INTO us_population_county (
            PopulationCount, County
        ) VALUES (%s, %s);
        """
    }, 
    "us_population": {
        "file_path":"us_population.txt",
        "insert_query": """INSERT INTO us_population (
            CensurYear, State, PopulationCount
        ) VALUES (%s, %s, %s);
        """
    }, 
    "food_access": {
        "file_path":"food_access.txt",
        "insert_query": """INSERT INTO food_access (
		CensusTract, State, County, Urban, Pop2010, Ohu2010, LILATracts_1And10, LILATracts_halfAnd10, 
		LILATracks_1And20, LILATractsVehicle, HUNVFlag, LowIncomeTracts, PovertyRate, MedianFamilyIncome, 
		LA1and10, LAhalfand10, LA1and20, LATracts_half, LATracts1, LATracts10, LATracts20, LATractsVehicle_20, 
		LAPOP1_10, LAPOP05_10, LAPOP1_20, LALOWI1_10, LALOWI05_10, LALOWI1_20, lapophalf, lalowihalf, 
		lakidshalf, laseniorshalf, lawhitehalf, lablackhalf, laasianhalf, lanhopihalf, laaianhalf, laomultirhalf, 
		lahisphalf, lahunvhalf, lasnaphalf, lapop1, lalowi1, lakids1, laseniors1, lawhite1, lablack1, laasian1, 
		lanhopi1, laaian1, laomultir1, lahisp1, lahunv1, lasnap1, lapop10, lalowi10, lakids10, laseniors10, 
		lawhite10, lablack10, laasian10, lanhopi10, laaian10, laomultir10, lahisp10, lahunv10, lasnap10, 
		lapop20, lalowi20, lakids20, laseniors20, lawhite20, lablack20, laasian20, lanhopi20, laaian20, 
		laomultir20, lahisp20, lahunv20, lasnap20, TractLOWI, TractKids, TractSeniors, TractWhite, TractBlack, 
		TractAsian, TractNHOPI, TractAIAN, TractOMultir, TractHispanic, TractHUNV, TractSNAP
	) VALUES (
		%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
		%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
		%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
		%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
	);
	""",
    },
}

for table in table_data:
    if table == "food_access": 
        continue
    else:
        upload_data_from_file(table_data[table]["file_path"], table_data[table]["insert_query"])
        print(f"Done for {table}")

# Close the database connection
conn.close()
print("Data uploaded successfully.")

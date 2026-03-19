import sqlite3
import csv

import mysql.connector
import pandas as pd



HOST     = 'mysql'
DATABASE = 'local_norp'
USER     = 'root'
PASSWORD = 'root'
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

cursor.execute("""
CREATE TABLE unemployment_rates_by_state (
    State VARCHAR(255),
    Rate_2022 DECIMAL(3,1),
    Rate_2023 DECIMAL(3,1),
    Rate_Change DECIMAL(3,1),
    State_Rank INT,
    PRIMARY KEY (State)
);
""")

cursor.execute("""
CREATE TABLE ngos_with_categorization (
    Ein BIGINT PRIMARY KEY,
    Name TEXT,
    Fulladdr TEXT,
    City VARCHAR(255),
    State VARCHAR(2),
    Zip VARCHAR(20),
    County VARCHAR(255),
    Ntee_Code VARCHAR(20),
    Category VARCHAR(255),
    Is_Category_Llm_Generated BOOLEAN
);
""")

# FAA Releasable Aircraft (seeded from FAA_Releasable_Aircraft_*.csv)
cursor.execute("""
CREATE TABLE faa_master (
    n_number VARCHAR(16) NOT NULL PRIMARY KEY,
    serial_number TEXT,
    mfr_mdl_code TEXT,
    eng_mfr_mdl TEXT,
    year_mfr TEXT,
    owner_type TEXT,
    registrant_name TEXT,
    street TEXT,
    street2 TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    region TEXT,
    county TEXT,
    country TEXT,
    last_action_date TEXT,
    cert_issue_date TEXT,
    certification TEXT,
    airworthiness_classification TEXT,
    approved_operations TEXT,
    type_aircraft TEXT,
    type_engine TEXT,
    status_code TEXT,
    mode_s_code TEXT,
    fract_owner TEXT,
    air_worth_date TEXT,
    other_names1 TEXT,
    other_names2 TEXT,
    other_names3 TEXT,
    other_names4 TEXT,
    other_names5 TEXT,
    expiration_date TEXT,
    unique_id TEXT,
    kit_mfr TEXT,
    kit_model TEXT,
    mode_s_code_hex TEXT
);
""")
cursor.execute("""
CREATE TABLE faa_acftref (
    code VARCHAR(32) NOT NULL PRIMARY KEY,
    mfr_code TEXT,
    model_code TEXT,
    series_code TEXT,
    mfr TEXT,
    model TEXT,
    type_acft TEXT,
    type_eng TEXT,
    ac_cat TEXT,
    build_cert_ind TEXT,
    no_eng TEXT,
    no_seats TEXT,
    ac_weight TEXT,
    speed TEXT,
    tc_data_sheet TEXT,
    tc_data_holder TEXT
);
""")
cursor.execute("""
CREATE TABLE faa_engine (
    code VARCHAR(16) NOT NULL PRIMARY KEY,
    mfr TEXT,
    model TEXT,
    eng_type TEXT,
    horsepower TEXT,
    thrust TEXT
);
""")
cursor.execute("""
CREATE TABLE faa_dealer (
    certificate_number VARCHAR(32) NOT NULL PRIMARY KEY,
    ownership TEXT,
    certificate_date TEXT,
    expiration_date TEXT,
    expired TEXT,
    certificate_issue_count TEXT,
    dealer_name TEXT,
    street TEXT,
    street2 TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    other_names_count TEXT,
    other_names_1 TEXT,
    other_names_2 TEXT,
    other_names_3 TEXT,
    other_names_4 TEXT,
    other_names_5 TEXT,
    other_names_6 TEXT,
    other_names_7 TEXT,
    other_names_8 TEXT,
    other_names_9 TEXT,
    other_names_10 TEXT,
    other_names_11 TEXT,
    other_names_12 TEXT,
    other_names_13 TEXT,
    other_names_14 TEXT,
    other_names_15 TEXT,
    other_names_16 TEXT,
    other_names_17 TEXT,
    other_names_18 TEXT,
    other_names_19 TEXT,
    other_names_20 TEXT,
    other_names_21 TEXT,
    other_names_22 TEXT,
    other_names_23 TEXT,
    other_names_24 TEXT,
    other_names_25 TEXT
);
""")
cursor.execute("""
CREATE TABLE faa_docindex (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    type_collateral TEXT,
    collateral_aircraft TEXT,
    collateral_engine TEXT,
    collateral_propeller TEXT,
    collateral_spare_parts TEXT,
    collateral_document TEXT,
    collateral_unidentified TEXT,
    party TEXT,
    doc_id TEXT,
    drdate TEXT,
    processing_date TEXT,
    corr_date TEXT,
    corr_id TEXT,
    serial_id TEXT,
    doc_type TEXT
);
""")
cursor.execute("""
CREATE TABLE faa_dereg (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    n_number TEXT,
    serial_number TEXT,
    mfr_mdl_code TEXT,
    status_code TEXT,
    registrant_name TEXT,
    street_mail TEXT,
    street2_mail TEXT,
    city_mail TEXT,
    state_abbrev_mail TEXT,
    zip_code_mail TEXT,
    eng_mfr_mdl TEXT,
    year_mfr TEXT,
    certification TEXT,
    airworthiness_classification TEXT,
    approved_operations TEXT,
    region TEXT,
    county_mail TEXT,
    country_mail TEXT,
    air_worth_date TEXT,
    cancel_date TEXT,
    mode_s_code TEXT,
    owner_type TEXT,
    exp_country TEXT,
    last_act_date TEXT,
    cert_issue_date TEXT,
    street_physical TEXT,
    street2_physical TEXT,
    city_physical TEXT,
    state_abbrev_physical TEXT,
    zip_code_physical TEXT,
    county_physical TEXT,
    country_physical TEXT,
    other_names1 TEXT,
    other_names2 TEXT,
    other_names3 TEXT,
    other_names4 TEXT,
    other_names5 TEXT,
    kit_mfr TEXT,
    kit_model TEXT,
    mode_s_code_hex TEXT
);
""")
cursor.execute("""
CREATE TABLE faa_reserved (
    n_number VARCHAR(16) NOT NULL PRIMARY KEY,
    registrant TEXT,
    street TEXT,
    street2 TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    rsv_date TEXT,
    tr TEXT,
    exp_date TEXT,
    n_num_chg TEXT,
    purge_date TEXT
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

def upload_data_from_csv(file_path, insert_query):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader, None)

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
    "unemployment_rates_by_state": {
        "file_path":"create_unemployment_rates_by_state.csv",
        "insert_query": """INSERT INTO unemployment_rates_by_state (
            State, Rate_2022, Rate_2023, Rate_Change, State_Rank
        ) VALUES (%s, %s, %s, %s, %s);
        """
    },
    "ngos_with_categorization": {
        "file_path":"ngos_with_categorization.csv",
        "insert_query": """INSERT INTO ngos_with_categorization (
            Ein, Name, Fulladdr, City, State, Zip, County, Ntee_Code, Category, Is_Category_Llm_Generated
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
    }
}

faa_table_data = {
    "faa_master": {
        "file_path": "FAA_Releasable_Aircraft_master.csv",
        "insert_query": """INSERT INTO faa_master (
            n_number, serial_number, mfr_mdl_code, eng_mfr_mdl, year_mfr, owner_type, registrant_name,
            street, street2, city, state, zip_code, region, county, country, last_action_date,
            cert_issue_date, certification, airworthiness_classification, approved_operations,
            type_aircraft, type_engine, status_code, mode_s_code, fract_owner, air_worth_date,
            other_names1, other_names2, other_names3, other_names4, other_names5, expiration_date,
            unique_id, kit_mfr, kit_model, mode_s_code_hex
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
        """,
    },
    "faa_acftref": {
        "file_path": "FAA_Releasable_Aircraft_acftref.csv",
        "insert_query": """INSERT INTO faa_acftref (
            code, mfr_code, model_code, series_code, mfr, model, type_acft, type_eng, ac_cat,
            build_cert_ind, no_eng, no_seats, ac_weight, speed, tc_data_sheet, tc_data_holder
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
    },
    "faa_engine": {
        "file_path": "FAA_Releasable_Aircraft_engine.csv",
        "insert_query": """INSERT INTO faa_engine (
            code, mfr, model, eng_type, horsepower, thrust
        ) VALUES (%s, %s, %s, %s, %s, %s);
        """,
    },
    "faa_dealer": {
        "file_path": "FAA_Releasable_Aircraft_dealer.csv",
        "insert_query": """INSERT INTO faa_dealer (
            certificate_number, ownership, certificate_date, expiration_date, expired,
            certificate_issue_count, dealer_name, street, street2, city, state, zip_code,
            other_names_count, other_names_1, other_names_2, other_names_3, other_names_4,
            other_names_5, other_names_6, other_names_7, other_names_8, other_names_9,
            other_names_10, other_names_11, other_names_12, other_names_13, other_names_14,
            other_names_15, other_names_16, other_names_17, other_names_18, other_names_19,
            other_names_20, other_names_21, other_names_22, other_names_23, other_names_24,
            other_names_25
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
        """,
    },
    "faa_docindex": {
        "file_path": "FAA_Releasable_Aircraft_docindex.csv",
        "insert_query": """INSERT INTO faa_docindex (
            type_collateral, collateral_aircraft, collateral_engine, collateral_propeller,
            collateral_spare_parts, collateral_document, collateral_unidentified, party, doc_id,
            drdate, processing_date, corr_date, corr_id, serial_id, doc_type
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
    },
    "faa_dereg": {
        "file_path": "FAA_Releasable_Aircraft_dereg.csv",
        "insert_query": """INSERT INTO faa_dereg (
            n_number, serial_number, mfr_mdl_code, status_code, registrant_name, street_mail,
            street2_mail, city_mail, state_abbrev_mail, zip_code_mail, eng_mfr_mdl, year_mfr,
            certification, airworthiness_classification, approved_operations, region, county_mail,
            country_mail, air_worth_date, cancel_date, mode_s_code, owner_type, exp_country,
            last_act_date, cert_issue_date, street_physical, street2_physical, city_physical,
            state_abbrev_physical, zip_code_physical, county_physical, country_physical,
            other_names1, other_names2, other_names3, other_names4, other_names5, kit_mfr,
            kit_model, mode_s_code_hex
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
        """,
    },
    "faa_reserved": {
        "file_path": "FAA_Releasable_Aircraft_reserved.csv",
        "insert_query": """INSERT INTO faa_reserved (
            n_number, registrant, street, street2, city, state, zip_code, rsv_date, tr, exp_date,
            n_num_chg, purge_date
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
    },
}

for table in table_data:
    if table == "food_access":
        continue
    elif table in ("unemployment_rates_by_state", "ngos_with_categorization"):
        upload_data_from_csv(table_data[table]["file_path"], table_data[table]["insert_query"])
        print(f"Done for {table}")
    else:
        upload_data_from_file(table_data[table]["file_path"], table_data[table]["insert_query"])
        print(f"Done for {table}")

for faa_table in faa_table_data:
    upload_data_from_csv(
        faa_table_data[faa_table]["file_path"],
        faa_table_data[faa_table]["insert_query"],
    )
    print(f"Done for {faa_table}")

# Close the database connection
conn.close()
print("Data uploaded successfully.")

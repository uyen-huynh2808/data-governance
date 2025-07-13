import os
import pandas as pd
from pymongo import MongoClient
import subprocess
from pathlib import Path

# MongoDB Configuration
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["university_data"]

# Hive Configuration
hive_db = "university_data"
csv_dir = Path("data")
tables = [
    "students", "courses", "enrollments", 
    "grades", "consent_logs", "access_logs"
]

def ingest_to_mongo():
    print("Ingesting data into MongoDB...")
    for table in tables:
        csv_path = csv_dir / f"{table}.csv"
        if not csv_path.exists():
            print(f"Skipping {table}.csv: File not found.")
            continue
        df = pd.read_csv(csv_path)
        mongo_db[table].drop()
        mongo_db[table].insert_many(df.to_dict(orient="records"))
        print(f"Inserted {len(df)} records into MongoDB collection '{table}'.")

def ingest_to_hive():
    print("Creating Hive tables and loading data...")

    hive_classpath = (
        "/PATH_TO/hive/lib/*:"
        "/PATH_TO/hadoop/share/hadoop/common/*:"
        "/PATH_TO/hadoop/share/hadoop/common/lib/*:"
        "/PATH_TO/hadoop/share/hadoop/mapreduce/*:"
        "/PATH_TO/hadoop/share/hadoop/mapreduce/lib/*:"
        "/PATH_TO/hadoop/share/hadoop/hdfs/*:"
        "/PATH_TO/hadoop/share/hadoop/hdfs/lib/*:"
        "/PATH_TO/hadoop/share/hadoop/yarn/*:"
        "/PATH_TO/hadoop/share/hadoop/yarn/lib/*"
    )

    java_cmd = [
        "java",
        "--add-opens", "java.base/java.net=ALL-UNNAMED",
        "--add-opens", "java.base/java.lang=ALL-UNNAMED",
        "--add-opens", "java.base/java.nio=ALL-UNNAMED",
        "-cp", hive_classpath,
        "org.apache.hadoop.hive.cli.CliDriver"
    ]

    # Step 1: Create the database
    with open("create_db.hql", "w") as f:
        f.write(f"CREATE DATABASE IF NOT EXISTS {hive_db};\n")

    subprocess.run(java_cmd + ["-f", "create_db.hql"], check=True)

    # Step 2: Create tables and load data
    for table in tables:
        csv_path = csv_dir / f"{table}.csv"
        if not csv_path.exists():
            print(f"Skipping {table}.csv: File not found.")
            continue

        schema = infer_hive_schema(csv_path)
        create_script = f"""
            USE {hive_db};
            DROP TABLE IF EXISTS {table};
            CREATE EXTERNAL TABLE {table} (
                {schema}
            )
            ROW FORMAT DELIMITED
            FIELDS TERMINATED BY ','
            STORED AS TEXTFILE
            LOCATION 'hdfs:///user/hive/warehouse/{hive_db}.db/{table}';
        """
        load_script = f"LOAD DATA LOCAL INPATH '{csv_path.resolve()}' INTO TABLE {hive_db}.{table};"

        with open(f"{table}_load.hql", "w") as f:
            f.write(create_script + load_script)

        subprocess.run(java_cmd + ["-f", f"{table}_load.hql"], check=True)
        print(f"Hive table '{table}' created and data loaded.")

def infer_hive_schema(csv_path):
    df = pd.read_csv(csv_path, nrows=1)
    hive_types = {
        "object": "STRING", "int64": "INT", "float64": "DOUBLE",
        "bool": "BOOLEAN", "datetime64[ns]": "TIMESTAMP"
    }
    schema = []
    for col, dtype in df.dtypes.items():
        hive_type = hive_types.get(str(dtype), "STRING")
        schema.append(f"`{col}` {hive_type}")
    return ",\n".join(schema)

if __name__ == "__main__":
    ingest_to_mongo()
    ingest_to_hive()
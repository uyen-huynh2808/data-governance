import json, requests, time
from requests.auth import HTTPBasicAuth

ATLAS_ENDPOINT = "http://localhost:21000/api/atlas/v2"
HEADERS = {"Content-Type": "application/json"}
AUTH = HTTPBasicAuth("admin", "admin")

def create_entity(entity_json):
    resp = requests.post(f"{ATLAS_ENDPOINT}/entity/bulk", headers=HEADERS, data=json.dumps(entity_json), auth=AUTH)
    try:
        data = resp.json()
    except Exception as e:
        print("Response error:", e)
        print(resp.text)
        return None

    if resp.status_code == 200 and "guidAssignments" in data:
        return list(data["guidAssignments"].values())[0]
    else:
        print(f"Failed: {resp.status_code}")
        print(json.dumps(data, indent=2))
        return None

def register_db(db_name):
    print(f"[DB] {db_name}")
    return create_entity({
        "entities": [{
            "guid": "-1", "typeName": "hive_db",
            "attributes": {
                "qualifiedName": f"{db_name}@cl1",
                "name": db_name,
                "clusterName": "cl1",
                "owner": "data_engineer",
                "location": f"hdfs:///user/hive/warehouse/{db_name}.db",
                "createTime": int(time.time() * 1000)
            }
        }]
    })

def register_table(db, table):
    print(f"[TABLE] {table}")
    return create_entity({
        "entities": [{
            "guid": "-1", "typeName": "hive_table",
            "attributes": {
                "qualifiedName": f"{db}.{table}@cl1",
                "name": table,
                "owner": "data_engineer",
                "location": f"hdfs:///user/hive/warehouse/{db}.db/{table}",
                "tableType": "MANAGED_TABLE",
                "createTime": int(time.time() * 1000)
            },
            "relationshipAttributes": {
                "db": {
                    "typeName": "hive_db",
                    "uniqueAttributes": {"qualifiedName": f"{db}@cl1"}
                }
            }
        }]
    })

def register_column(db, table, col_name):
    print(f"  └─ [COLUMN] {col_name}")
    return create_entity({
        "entities": [{
            "guid": "-1", "typeName": "hive_column",
            "attributes": {
                "qualifiedName": f"{db}.{table}.{col_name}@cl1",
                "name": col_name,
                "type": "string"
            },
            "relationshipAttributes": {
                "table": {
                    "typeName": "hive_table",
                    "uniqueAttributes": {"qualifiedName": f"{db}.{table}@cl1"}
                }
            }
        }]
    })

def register_process(input_table, output_table):
    print(f"[PROCESS] {input_table} -> {output_table}")
    now = int(time.time() * 1000)

    return create_entity({
        "entities": [{
            "typeName": "hive_process",
            "attributes": {
                "name": f"{input_table}_to_{output_table}",
                "qualifiedName": f"{input_table}_to_{output_table}@cl1",
                "userName": "data_engineer",
                "startTime": now,
                "endTime": now + 1000,
                "operationType": "QUERY",
                "queryText": f"INSERT INTO {output_table} SELECT ... FROM {input_table}",
                "queryPlan": f"Plan: logical transformation from {input_table} to {output_table}",
                "queryId": f"query_{input_table}_to_{output_table}",
                "inputs": [{
                    "typeName": "hive_table",
                    "uniqueAttributes": {"qualifiedName": f"university_data.{input_table}@cl1"}
                }],
                "outputs": [{
                    "typeName": "hive_table",
                    "uniqueAttributes": {"qualifiedName": f"university_data.{output_table}@cl1"}
                }],
                "description": f"ETL from {input_table} to {output_table}"
            }
        }]
    })

if __name__ == "__main__":
    db = "university_data"
    if not register_db(db):
        exit("DB creation failed.")

    tables = {
        "dim_student": ["student_id", "name", "email", "dob", "id_number", "pii_flag"],
        "fact_enrollments": ["enrollment_id", "student_id", "course_id", "grade", "status", "term_id"],
        "dim_course": ["course_id", "name", "department", "sensitivity_tag"],
        "dim_department": ["department_id", "name", "region"],
        "consent_logs": ["student_id", "consent_given", "consent_time", "method"],
        "access_logs": ["user_id", "role", "table_name", "access_type", "query_time"]
    }

    for table, columns in tables.items():
        table_guid = register_table(db, table)
        if not table_guid:
            print(f"Table {table} failed.")
            continue
        for col in columns:
            register_column(db, table, col)

    # Also create lineage source tables (empty, no columns)
    for src in ["students", "enrollments", "grades", "courses"]:
        register_table(db, src)

    # Register ETL processes
    register_process("students", "dim_student")
    register_process("enrollments", "fact_enrollments")
    register_process("grades", "fact_enrollments")
    register_process("courses", "dim_course")
    register_process("courses", "dim_department")

    print("\nAll metadata registered.")

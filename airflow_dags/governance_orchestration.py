from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.utils import timezone
from datetime import timedelta
import subprocess

default_args = {
    "owner": "admin",
    "start_date": timezone.utcnow() - timedelta(days=1),
    "retries": 1,
}

dag = DAG(
    dag_id="governance_orchestration",
    default_args=default_args,
    description="Master DAG for education data governance",
    schedule="0 1 * * 1",
    catchup=False,
)

# === Task 1: Generate synthetic data
def generate_data():
    subprocess.run(["python3", "/PATH_TO/data_generator/generate_data.py"], check=True)

generate_task = PythonOperator(
    task_id="generate_synthetic_data",
    python_callable=generate_data,
    dag=dag,
)

# === Task 2a: Ingest to MongoDB
def ingest_to_mongo():
    subprocess.run(["python3", "/PATH_TO/pipeline_tasks/ingest_data.py"], check=True)

ingest_mongo_task = PythonOperator(
    task_id="ingest_to_mongo",
    python_callable=ingest_to_mongo,
    dag=dag,
)

# === Task 2b: Load to Hive
def load_to_hive():
    subprocess.run(["python3", "/PATH_TO/pipeline_tasks/load_to_hive.py"], check=True)

load_hive_task = PythonOperator(
    task_id="load_to_hive",
    python_callable=load_to_hive,
    dag=dag,
)

# === Task 3: Compliance rule check 
def run_compliance_check():
    subprocess.run(["python3", "/PATH_TO/pipeline_tasks/compliance_monitor.py"], check=True)

compliance_task = PythonOperator(
    task_id="run_compliance_checks",
    python_callable=run_compliance_check,
    dag=dag,
)

# === Task 4: Update metadata lineage
def update_lineage():
    subprocess.run(["python3", "/PATH_TO/atlas_integration/update_lineage_metadata.py"], check=True)

lineage_task = PythonOperator(
    task_id="update_lineage_metadata",
    python_callable=update_lineage,
    dag=dag,
)

# === DAG dependencies
generate_task >> ingest_mongo_task >> load_hive_task
load_hive_task >> compliance_task
compliance_task >> lineage_task

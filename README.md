# Compliance Dashboard for Data Governance in Education

## Project Overview

Universities in Vietnam and international campuses must comply with data protection regulations like **Vietnam’s PDPD** and **GDPR** when handling **student data**. This project builds a **Compliance Dashboard** to monitor and ensure governance, data quality, and security over education-related data.

The system uses:
- **MongoDB** for semi-structured student records
- **Hadoop (HDFS + Hive)** for centralized storage
- **Apache Atlas** for data lineage
- **Apache Ranger** for access control
- **Great Expectations** for data quality
- A **custom compliance engine** for PDPD/GDPR monitoring

## Project Goals

- Track student data lineage from source to reporting layer
- Validate and report on data quality for sensitive records (e.g., grades, ID numbers)
- Restrict access to PII based on roles (e.g., Admin vs Professor)
- Alert on PDPD/GDPR violations (e.g., missing consent, unauthorized access)
- Provide a user-friendly dashboard for compliance status and audit

> The custom compliance rules engine enforces PDPD/GDPR policies such as consent validation and PII access monitoring based on predefined rules.

## Architecture

![architecture](https://github.com/user-attachments/assets/6586b4ef-bbb1-4a54-97d9-51eaf9bf1d10)

> Note:
> This project handles data generation and ingestion in batch mode, so MongoDB acts only as a temporary storage layer and may appear redundant.
> However, in a real-world scenario involving complex streaming sources or microservices, MongoDB (or other NoSQL stores) is useful for buffering semi-structured data before transformation and loading into Hive or a data warehouse.

## Technology Stack

| Component              | Tool / Framework             |
|------------------------|------------------------------|
| Data Source	| MongoDB, CSV (Faker) |
| Orchestration	| Apache Airflow | 
| Storage	| HDFS, Hive | 
| Metadata/Lineage	| Apache Atlas | 
| Security	| Apache Ranger | 
| Data Quality	| Great Expectations | 
| Rule Engine	| Python (YAML rules) | 
| Visualization	| Streamlit  | 

## Data Used

### MongoDB & CSV Files

All six datasets are first generated as CSV files using the Faker library, and then ingested into **both MongoDB** (for temporary storage and inspection) and **Hive** (as structured warehouse tables). MongoDB supports flexibility in handling semi-structured data during staging, while Hive supports downstream governance tools like Apache Atlas and Ranger.

The six datasets include:

1. `students`
2. `courses`
3. `enrollments`
4. `grades`
5. `consent_logs`
6. `access_logs`

Below is the schema and governance use for each dataset:

#### 1. Student Info (`students`)

| Field         | Type     | Description                 |
|--------------|----------|-----------------------------|
| student_id   | String   | Unique student identifier   |
| name         | String   | Full name                   |
| dob          | Date     | Date of birth               |
| email        | String   | Email address (PII)         |
| id_number    | String   | National ID (PII)           |
| consent_given| Boolean  | Consent status              |
| country      | String   | Country of residence        |

**Governance Use:**  PII tracking, consent validation, data subject identification (GDPR/PDPD).

#### 2. Course Info (`course`)

| Field           | Type     | Description                          |
|----------------|----------|--------------------------------------|
| course_id      | String   | Unique course identifier             |
| name           | String   | Course name                          |
| credits        | Integer  | Academic credit value                |
| department     | String   | Associated academic department       |
| sensitivity_tag| String   | Tag (e.g., `public`, `sensitive`)    |

**Governance Use:**  Governance tagging and data classification. Tracked via **Apache Atlas** for metadata lineage.

#### 3. Enrollment Logs (`enrollments`)

| Field         | Type     | Description                        |
|--------------|----------|------------------------------------|
| enrollment_id| String   | Unique enrollment identifier       |
| student_id   | String   | Foreign key to `students`          |
| course_id    | String   | Foreign key to `course_metadata`   |
| term         | String   | Academic term                      |
| status       | String   | Enrollment status (e.g., active)   |

**Governance Use:**  Acts as a fact table for analysis. Used in **quality checks**, such as orphan records or invalid keys.

#### 4. Grades (`grades`)

| Field       | Type     | Description                      |
|------------|----------|----------------------------------|
| student_id | String   | Foreign key to `students`        |
| course_id  | String   | Foreign key to `course_metadata` |
| grade      | String   | Letter grade                     |
| GPA        | Float    | GPA score                        |
| term       | String   | Academic term                    |

**Governance Use:**  Data quality validation (e.g., missing/null grades), **PDPD enforcement** for sensitive academic data.

#### 5. Consent Logs (`consent_logs`)

| Field         | Type     | Description                               |
|--------------|----------|-------------------------------------------|
| student_id   | String   | Foreign key to `students`                 |
| consent_given| Boolean  | Whether consent was granted               |
| consent_time    | Timestamp | When consent was recorded                 |
| method       | String   | Collection method (email/form/etc.)       |

**Governance Use:**  Used for **GDPR/PDPD monitoring**, consent lifecycle tracking, and audit trail generation.

#### 6. User Access Logs (`access_logs`)

| Field        | Type     | Description                             |
|-------------|----------|-----------------------------------------|
| user_id     | String   | ID of accessing user/system             |
| role        | String   | User role (e.g., analyst, admin)        |
| table_name       | String   | Dataset accessed (e.g., `students`)     |
| query_time  | Timestamp | Timestamp of access                     |
| access_type | String   | Operation type (read/write/delete)      |

**Governance Use:**  Represents **Apache Ranger audit logs**. Used to validate access control policies and detect violations.

## Data Model (Snowflake Schema)

This snowflake schema supports governance, quality validation, and lineage tracking using **Apache Atlas**, **Apache Ranger**, and **Great Expectations**. Data is denormalized where necessary for performance and compliance analysis.

### Fact Table: `fact_enrollments`

| Field         | Type    | Description                                |
|---------------|---------|--------------------------------------------|
| enrollment_id | String  | Unique enrollment record ID                |
| student_id    | String  | FK to `dim_student`                        |
| course_id     | String  | FK to `dim_course`                         |
| term_id       | String  | FK to `dim_term`                           |
| grade         | String  | Final grade (e.g., A, B)                  |
| status        | String  | Enrollment status (e.g., active, dropped)  |

**Governance Use:**  
- Basis for anomaly detection (e.g., invalid IDs) using **Great Expectations**  
- Allows mapping of academic and compliance events  

### Dimension Table: `dim_student`

| Field       | Type    | Description                     |
|-------------|---------|---------------------------------|
| student_id  | String  | Unique student identifier       |
| name        | String  | Student full name (PII)         |
| email       | String  | Email address (PII)             |
| dob         | Date    | Date of birth (PII)             |
| id_number   | String  | National ID (PII)               |
| pii_flag    | Boolean | Indicates PII presence          |

**Governance Use:**  
- Tagged as **PII** via **Apache Ranger**  
- Field-level access control and audit logs enabled

> Fields tagged as PII or sensitive are managed via Apache Ranger for field-level access control and audit logging.  

### Dimension Table: `dim_course`

| Field           | Type    | Description                         |
|------------------|---------|-------------------------------------|
| course_id       | String  | Unique course identifier            |
| name            | String  | Course name                         |
| department      | String  | Department name                     |
| sensitivity_tag | String  | Data classification (e.g. `public`, `sensitive`) |

**Governance Use:**  
- Tagged by **Apache Atlas** for lineage  
- Sensitivity labels inform access policies in **Ranger**

> Fields tagged as PII or sensitive are managed via Apache Ranger for field-level access control and audit logging.  

### Dimension Table: `dim_term`

| Field     | Type    | Description                |
|-----------|---------|----------------------------|
| term_id   | String  | Unique academic term ID    |
| year      | Integer | Academic year              |
| semester  | String  | Semester (e.g., First, Second) |

### Dimension Table: `dim_department`

| Field         | Type    | Description                      |
|---------------|---------|----------------------------------|
| department_id | String  | Unique department ID             |
| name          | String  | Department name                  |
| region        | String  | Regional location (e.g., APAC)   |

### Optimization

- **Partitioning:** Tables are partitioned by `region` (in `dim_department`) and `term_id` (in `fact_enrollments`) to improve Hive query performance and archiving strategy.
- **PII Tagging:** Fields such as `email`, `dob`, and `id_number` are tagged as PII for **access control** and **compliance auditing** via **Apache Ranger** and **Apache Atlas**.
- **Indexing/Bucketing:** Not applied in this setup. For larger datasets, Hive bucketing or indexing can be introduced. The current system relies on **partition pruning** for performance.

## Project Structure

1. `data_generator/`: Synthetic data generator using Faker
   - `generate_data.py`: Script to generate all CSVs with consistent keys and structure

2. `data/`: Input datasets (synthetic, Faker-generated)
   - `students.csv`
   - `enrollments.csv`
   - `grades.csv`
   - `consent_logs.csv`
   - `course.csv`
   - `access_logs.csv`

3. `pipeline_tasks/`: Modular Python scripts for pipeline task logic
   - `ingest_data.py`: Ingests data into MongoDB and HDFS
   - `load_to_hive.py`: Loads structured data into Hive with Snowflake schema
   - `compliance_monitor.py`: Triggers data quality checks and compliance validation

4. `config/`: Configuration files
   - `hive_schema.sql`: Hive table creation scripts
   - `pii_tags.json`: PII tag configuration for Atlas/Ranger

5. `compliance_rules/`: GDPR/PDPD rule definitions
   - `rules.yaml`: Defines compliance thresholds, null limits, consent conditions

6. `great_expectations/`: Data quality validation
   - `expectations/student_expectations.json`: Great Expectations suite for students data
   - `expectations/enrollment_expectations.json`: Expectations for enrollment data
   - `expectations/grades_expectations.json`: Expectations for grades
   - `checkpoints/student_checkpoint.json`: Checkpoint for students pipeline
   - `checkpoints/grades_checkpoint.json`: Checkpoint for grades pipeline

7. `ranger_policies/`: Access control rules using Apache Ranger
   - `student_policy.json`: Policy for student data
   - `grades_policy.json`: Policy for academic performance data
   - `access_log_policy.json`: Policy for monitoring access logs

8. `atlas_integration/`: Apache Atlas lineage automation
   - `update_lineage_metadata.py`: Script to update metadata and lineage

9. `airflow_dags/`: Workflow orchestration using Apache Airflow
   - `governance_orchestration.py`: Master DAG that calls all task functions

10. `dashboard/`: Streamlit-based monitoring UI
    - `streamlit_ui.py`: Visual dashboard for governance metrics and alerts

11. `notebooks/`: Interactive walkthroughs and documentation
    - `pipeline_walkthrough.ipynb`: Jupyter notebook that demonstrates how to run and monitor the full data governance pipeline, while also outlining its current limitations and potential areas for future development.


## Disclaimer

- All data in this project is **synthetically generated** using the Faker library.
- No real individuals, courses, or institutions are represented.
- This project is for **educational and demonstration purposes only**, especially in the context of data privacy, data governance, and compliance simulation.
- Features such as PII tagging, GDPR/PDPD enforcement, and access logging are simulated to reflect real-world architecture, not actual enforcement.
-----

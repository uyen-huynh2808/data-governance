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

## Architecture

```plaintext
         ┌─────────────┐     ┌────────────┐
         │  MongoDB    │     │ CSV Files  │
         └────┬────────┘     └────┬───────┘
              │                       │
              ▼                       ▼
     ┌────────────────────────────────────────┐
     │   Ingestion Pipeline (Apache Airflow)  │
     └────────────────┬───────────────────────┘
                      ▼
                 ┌────────┐
                 │  HDFS  │
                 └────┬───┘
                      ▼
              ┌──────────────┐
              │   Hive DWH   │  ◄── Snowflake Schema (education domain)
              └────┬─────────┘
                   ▼
     ┌─────────────────────────────────────────────────────────┐
     │  Lineage: Apache Atlas   ┃  Quality: Great Expectations │
     │  Security: Apache Ranger ┃  Compliance Rules Engine     │
     └────┬───────────────┬────────────────────────────────────┘
          ▼               ▼
   [Access Logs]     [Violations] ─────────────┐
                                              ▼
                                ┌────────────────────────┐
                                │ Compliance Dashboard    │
                                │ (Streamlit / Looker)    │
                                └────────────────────────┘
```

## Data Used
### MongoDB Collections
- students: personal info (name, email, dob, ID)
- enrollments: course registration records
- grades: term results, GPA

### CSV Files
- consent_logs.csv: Student consent history
- course_metadata.csv: Course names, tags, departments

## Data Model (Snowflake Schema)
### Fact Table: fact_enrollments
| enrollment_id | student_id | course_id | term_id | grade | status |
### Dimension Tables
- dim_student(student_id, name, email, dob, id_number, pii_flag)
- dim_course(course_id, name, department, sensitivity_tag)
- dim_term(term_id, year, semester)
- dim_department(department_id, name, region)
> Partitioning: region, term_id
> 
> Indexing: student_id, course_id
> 
> Tags for PII used by Apache Ranger

## Project Files
```plaintext
edu-compliance-dashboard/
├── airflow_dags/
│   ├── ingest_students.py
│   ├── load_to_hive.py
│   └── compliance_monitor.py
├── great_expectations/
│   ├── expectations/
│   │   └── student_expectations.json
│   └── checkpoints/
├── atlas_integration/
│   └── update_lineage_metadata.py
├── ranger_policies/
│   └── student_policy.json
├── compliance_rules/
│   └── rules.yaml
├── dashboard/
│   └── streamlit_ui.py
├── data/
│   ├── consent_logs.csv
│   └── course_metadata.csv
├── config/
│   ├── hive_schema.sql
│   └── pii_tags.json
├── README.md
└── requirements.txt
```

## Dashboard Features (Streamlit)
- Lineage graph (via Atlas API)
- Data quality test results (pass/fail %)
- Access control and audit logs (from Ranger)
- Real-time alerts and compliance status
- Export PDF/CSV reports

-----

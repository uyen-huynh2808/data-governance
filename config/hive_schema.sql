-- Force Hive to run in local mode
SET hive.exec.mode.local.auto.input.files.max=9999;
SET hive.exec.mode.local.auto=true;

-- Create the Hive database if not exists
CREATE DATABASE IF NOT EXISTS university_data;
USE university_data;

-- =====================
-- 1. Raw External Tables
-- =====================

CREATE EXTERNAL TABLE IF NOT EXISTS students (
  student_id STRING,
  name STRING,
  email STRING,
  dob DATE,
  country STRING,
  id_number STRING,
  consent_given BOOLEAN
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs:///user/hive/warehouse/university_data.db/students';

CREATE EXTERNAL TABLE IF NOT EXISTS courses (
  course_id STRING,
  name STRING,
  credits INT,
  sensitivity_tag STRING,
  department STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs:///user/hive/warehouse/university_data.db/courses';

CREATE EXTERNAL TABLE IF NOT EXISTS enrollments (
  enrollment_id STRING,
  student_id STRING,
  course_id STRING,
  term STRING,
  status STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs:///user/hive/warehouse/university_data.db/enrollments';

CREATE EXTERNAL TABLE IF NOT EXISTS grades (
  student_id STRING,
  course_id STRING,
  term STRING,
  grade STRING,
  GPA DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs:///user/hive/warehouse/university_data.db/grades';

CREATE EXTERNAL TABLE IF NOT EXISTS consent_logs (
  student_id STRING,
  consent_given BOOLEAN,
  consent_time TIMESTAMP,
  method STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs:///user/hive/warehouse/university_data.db/consent_logs';

CREATE EXTERNAL TABLE IF NOT EXISTS access_logs (
  user_id STRING,
  role STRING,
  table_name STRING,
  access_type STRING,
  query_time TIMESTAMP
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs:///user/hive/warehouse/university_data.db/access_logs';

-- =====================
-- 2. Dimension & Fact Tables
-- =====================

-- dim_student
CREATE TABLE IF NOT EXISTS dim_student (
  student_id STRING,
  name STRING,
  email STRING,
  dob DATE,
  id_number STRING,
  pii_flag BOOLEAN
)
STORED AS ORC;

INSERT OVERWRITE TABLE dim_student
SELECT
  student_id,
  name,
  email,
  dob,
  id_number,
  CASE
    WHEN email IS NOT NULL OR dob IS NOT NULL OR id_number IS NOT NULL THEN true
    ELSE false
  END AS pii_flag
FROM students;

-- dim_course
CREATE TABLE IF NOT EXISTS dim_course (
  course_id STRING,
  name STRING,
  department STRING,
  sensitivity_tag STRING
)
STORED AS ORC;

INSERT OVERWRITE TABLE dim_course
SELECT
  course_id,
  name,
  department,
  sensitivity_tag
FROM courses;

-- dim_term
CREATE TABLE IF NOT EXISTS dim_term (
  term_id STRING,
  year INT,
  semester STRING
)
STORED AS ORC;

INSERT OVERWRITE TABLE dim_term
SELECT DISTINCT
  CONCAT_WS('-', term, CAST(year(CURRENT_DATE) AS STRING)) AS term_id,
  year(CURRENT_DATE) AS year,
  term AS semester
FROM (
  SELECT term FROM enrollments
  UNION
  SELECT term FROM grades
) t;

-- Dynamic partition settings
SET hive.exec.dynamic.partition = true;
SET hive.exec.dynamic.partition.mode = nonstrict;

-- dim_department (partitioned)
CREATE TABLE IF NOT EXISTS dim_department (
  department_id STRING,
  name STRING
)
PARTITIONED BY (region STRING)
STORED AS ORC;

INSERT OVERWRITE TABLE dim_department PARTITION (region)
SELECT DISTINCT
  department AS department_id,
  department AS name,
  'APAC' AS region
FROM courses;

-- fact_enrollments (partitioned)
CREATE TABLE IF NOT EXISTS fact_enrollments (
  enrollment_id STRING,
  student_id STRING,
  course_id STRING,
  grade STRING,
  status STRING
)
PARTITIONED BY (term_id STRING)
STORED AS ORC;

INSERT OVERWRITE TABLE fact_enrollments PARTITION (term_id)
SELECT
  e.enrollment_id,
  e.student_id,
  e.course_id,
  g.grade,
  e.status,
  CONCAT_WS('-', e.term, CAST(YEAR(CURRENT_DATE) AS STRING)) AS term_id
FROM enrollments e
LEFT JOIN grades g
  ON e.student_id = g.student_id AND e.course_id = g.course_id AND e.term = g.term;

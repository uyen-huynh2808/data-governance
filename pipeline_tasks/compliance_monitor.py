import os
import subprocess
import pandas as pd
import yaml
import pexpect
from great_expectations.data_context import get_context

# Hive CLI-based Configuration
HIVE_DB = "university_data"
GE_DIR = os.path.abspath("great_expectations")
RULES_FILE = "compliance_rules/rules.yaml"

def query_hive(sql: str) -> pd.DataFrame:
    try:
        full_cmd = f"hive -e \"USE {HIVE_DB}; {sql}\""
        print(f"[QUERY] Executing: {sql.strip()[:100]}...")

        proc = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        stdout, stderr = proc.communicate(timeout=180)

        if proc.returncode != 0:
            print(f"[ERROR] Hive query failed with code {proc.returncode}:\n{stderr}")
            return pd.DataFrame()

        lines = stdout.strip().split("\n")
        if not lines or len(lines) < 2:
            return pd.DataFrame()

        columns = lines[0].split("\t")
        rows = [line.split("\t") for line in lines[1:] if line.strip()]
        return pd.DataFrame(rows, columns=columns)

    except subprocess.TimeoutExpired:
        proc.kill()
        print("[TIMEOUT] Hive query timed out.")
        return pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] Hive query failed: {e}")
        return pd.DataFrame()

def run_data_quality_checks():
    print("\n[INFO] Running Great Expectations Hive checkpoints...\n")
    context = get_context(context_root_dir=GE_DIR)
    results = {}

    for checkpoint_name in ["student_checkpoint", "grades_checkpoint"]:
        try:
            print(f"[INFO] Running checkpoint: {checkpoint_name}")

            # Load expectation suite
            suite = context.get_expectation_suite(expectation_suite_name=checkpoint_name.replace("_checkpoint", "") + ".expectation_suite")

            # Build batch manually
            batch = context.get_batch(
                batch_kwargs={
                    "datasource": "hive_cli_datasource",
                    "query": f"SELECT * FROM {checkpoint_name.replace('_checkpoint', '')}",
                    "data_asset_name": checkpoint_name.replace("_checkpoint", "")
                },
                expectation_suite_name=suite.expectation_suite_name
            )

            # Run validation operator manually
            validation_result = context.run_validation_operator(
                "action_list_operator",
                assets_to_validate=[batch]
            )

            success = validation_result["success"]
            results[checkpoint_name] = success
            print(f"[DQ] {checkpoint_name}: {'PASSED' if success else 'FAILED'}")

        except Exception as e:
            print(f"[ERROR] Failed to run checkpoint {checkpoint_name}: {e}")
            results[checkpoint_name] = False

    return results

def load_rules():
    with open(RULES_FILE, "r") as f:
        return yaml.safe_load(f)["rules"]

def check_compliance(rules):
    print("\n[INFO] Evaluating compliance rules on Hive...\n")
    violations = []

    for rule in rules:
        table = f"{rule['table']}"
        if rule["id"] == "consent_required":
            df = query_hive(f"SELECT * FROM {table} WHERE consent_given != true")
            if not df.empty:
                violations.append(f"{rule['name']} violated: {len(df)} records without consent.")
        elif rule["id"] == "pii_not_null_check":
            for col in rule["fields"]:
                df = query_hive(f"SELECT COUNT(*) as nulls FROM {table} WHERE {col} IS NULL")
                if not df.empty and int(df.iloc[0]['nulls']) > 0:
                    violations.append(f"{col} in {table} has {df.iloc[0]['nulls']} NULL values.")
        elif rule["id"] == "access_policy_violation":
            allowed_roles = "', '".join(rule["condition"]["allowed_values"])
            df = query_hive(
                f"""
                SELECT * FROM access_logs
                WHERE table_name = '{rule['filter_table']}'
                AND role NOT IN ('{allowed_roles}')
                """
            )
            if len(df) > rule["violation_threshold"]["max_violations_per_day"]:
                violations.append(f"{rule['name']} breached: unauthorized access logged.")
        elif rule["id"] == "gpa_outlier_check":
            df = query_hive(f"SELECT * FROM {table} WHERE GPA < 0.0 OR GPA > 4.0")
            if not df.empty:
                violations.append(f"{rule['name']} found {len(df)} GPA outliers.")
        elif rule["id"] == "duplicate_student_check":
            df = query_hive(
                f"""
                SELECT student_id, COUNT(*) as cnt
                FROM {table}
                GROUP BY student_id
                HAVING cnt > 1
                """
            )
            if not df.empty:
                violations.append(f"Duplicate student_id detected: {len(df)} duplicates.")
        elif rule["id"] == "consent_log_integrity":
            df = query_hive(
                f"""
                SELECT s.student_id
                FROM students s
                LEFT JOIN consent_logs c
                ON s.student_id = c.student_id
                WHERE c.student_id IS NULL
                """
            )
            if not df.empty:
                violations.append(f"{rule['name']} failed: {len(df)} students missing consent logs.")

    return violations

def main():
    dq_results = {"student_checkpoint": "SKIPPED", "grades_checkpoint": "SKIPPED"}
    rules = load_rules()
    compliance_violations = check_compliance(rules)

    print("\n==== COMPLIANCE SUMMARY ====")
    for cp, passed in dq_results.items():
        print(f"[DQ] {cp}: {'OK' if passed else 'FAILED'}")
    for v in compliance_violations:
        print(f"[ALERT] {v}")

    print(f"[SUMMARY] {len(compliance_violations)} of {len(rules)} compliance rules violated.")
    
    print("=============================\n")

if __name__ == "__main__": 
    main()   
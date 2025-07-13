import os
import subprocess
from pathlib import Path
import shutil
import sys

HIVE_SCRIPT = "config/hive_schema.sql"

def run_hive_script(script_path):
    print(f"\n[INFO] Running Hive script to build Snowflake schema: {script_path}...\n")
    try:
        subprocess.run(["hive", "-f", script_path], check=True)
    except FileNotFoundError:
        print("[ERROR] Hive CLI not found. Make sure Hive is installed and added to your PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Hive script execution failed with exit code {e.returncode}")
        sys.exit(e.returncode)

def main():
    print("[INFO] Starting Hive Snowflake schema creation...")
    if not Path(HIVE_SCRIPT).exists():
        print(f"[ERROR] Hive schema file not found: {HIVE_SCRIPT}")
        sys.exit(1)

    run_hive_script(HIVE_SCRIPT)
    print("\n[INFO] Snowflake schema successfully created in Hive.\n")

if __name__ == "__main__":
    main()

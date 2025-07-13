import streamlit as st
import yaml
import subprocess
import pandas as pd
import os

RULES_FILE = "compliance_rules/rules.yaml"
COMPLIANCE_LOG = "dashboard/compliance_output.log"

st.set_page_config(layout="wide", page_title="Compliance Dashboard")

# Load YAML rules
def load_rules():
    with open(RULES_FILE, "r") as f:
        return yaml.safe_load(f)["rules"]

# Parse compliance log
def parse_compliance_log():
    if not os.path.exists(COMPLIANCE_LOG):
        return {"dq": {}, "violations": []}

    dq = {}
    violations = []

    with open(COMPLIANCE_LOG, "r") as f:
        for line in f:
            if line.startswith("[DQ]"):
                parts = line.strip().split(":")
                if len(parts) >= 2:
                    name = parts[0].split()[1]
                    status = parts[1].strip()
                    dq[name] = status
            elif line.startswith("[ALERT]"):
                violations.append(line.strip().replace("[ALERT] ", ""))
    return {"dq": dq, "violations": violations}

# Run compliance monitor
def run_monitor():
    result = subprocess.run(["python", "pipeline_tasks/compliance_monitor.py"], capture_output=True, text=True)
    with open(COMPLIANCE_LOG, "w") as f:
        f.write(result.stdout)
    return result.stdout

# Layout
st.title("Data Governance Compliance Dashboard")
st.markdown("Monitor data quality, policy violations, and GDPR/PDPD compliance across education datasets.")

col1, col2 = st.columns([2, 1])
with col2:
    if st.button("Run Compliance Monitor"):
        st.info("Running compliance monitor...")
        run_monitor()
        st.success("Compliance monitor completed!")

rules = load_rules()
parsed = parse_compliance_log()

# --- DQ Results ---
st.subheader("Data Quality Checkpoints")
dq_results = parsed["dq"]

if dq_results:
    dq_table = pd.DataFrame.from_dict(dq_results, orient="index", columns=["Status"])
    dq_table.index.name = "Checkpoint"
    dq_table.reset_index(inplace=True)
    st.dataframe(dq_table, use_container_width=True)
else:
    st.warning("No data quality results found. Run the monitor to view results.")

# --- Compliance Rules ---
st.subheader("Compliance Rule Violations")
violations = parsed["violations"]

if violations:
    for v in violations:
        st.error(v)
else:
    st.success("No rule violations detected.")

# --- All Rule Overview ---
with st.expander("Rule Definition Summary"):
    rule_df = pd.DataFrame(rules)
    rule_df["fields"] = rule_df["fields"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
    st.dataframe(rule_df[["id", "name", "table", "fields"]], use_container_width=True)

# Footer
st.markdown("---")
st.caption("Data Governance Project • Streamlit Dashboard • Built for GDPR & PDPD Compliance Simulation")

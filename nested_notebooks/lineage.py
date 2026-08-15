import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Notebook Pipeline Lineage", layout="wide")
st.title("Notebook Pipeline Lineage")
st.caption("Column-level lineage across Bronze → Silver → Gold")

session = get_active_session()

# --- Column lineage definitions ---
BRONZE_COLUMNS = [
    "CUSTOMER_ID", "FULL_NAME", "COMPANY_NAME", "INVESTOR_TYPE",
    "REGION", "COUNTRY", "AUM_COMMITMENT_GBP", "RELATIONSHIP_START_DATE",
    "RELATIONSHIP_MANAGER", "RISK_PROFILE", "EMAIL", "STATUS",
]

SILVER_COLUMNS = [
    "GOLDEN_ID", "CUSTOMER_ID", "FULL_NAME", "COMPANY_NAME", "INVESTOR_TYPE",
    "REGION", "COUNTRY", "AUM_COMMITMENT_GBP", "RELATIONSHIP_START_DATE",
    "RELATIONSHIP_MANAGER", "RISK_PROFILE", "EMAIL", "STATUS", "IS_MASTER_RECORD",
]

GOLD_UK_COLUMNS = [
    "GOLDEN_ID", "CUSTOMER_ID", "FULL_NAME", "COMPANY_NAME", "INVESTOR_TYPE",
    "REGION", "COUNTRY", "AUM_COMMITMENT_GBP", "RELATIONSHIP_START_DATE",
    "RELATIONSHIP_MANAGER", "RISK_PROFILE", "EMAIL", "STATUS",
]

GOLD_IRELAND_COLUMNS = GOLD_UK_COLUMNS.copy()


def build_graphviz():
    """Build a Graphviz DOT string showing table nodes with columns and edges."""
    dot = """
    digraph lineage {
        rankdir=LR;
        graph [fontname="Helvetica", bgcolor="transparent", nodesep=0.4, ranksep=1.8];
        node [fontname="Helvetica", fontsize=10, shape=plain];
        edge [color="#999999", arrowsize=0.7];

        bronze [label=<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white" COLOR="#e0e0e0">
                <TR><TD COLSPAN="2" BGCOLOR="#f5f5f5" ALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="#666">Snowflake · Table</FONT></TD></TR>
                <TR><TD COLSPAN="2" BGCOLOR="#f5f5f5" ALIGN="LEFT"><B>CUSTOMERS</B></TD></TR>
                <TR><TD COLSPAN="2" BGCOLOR="#f5f5f5" ALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="#1976d2">Bronze</FONT></TD></TR>
    """
    for col in BRONZE_COLUMNS:
        bold = '<B>' + col + '</B>' if col in ("CUSTOMER_ID", "EMAIL") else col
        dot += f'            <TR><TD ALIGN="LEFT">{bold}</TD><TD ALIGN="RIGHT" PORT="{col}_r">→</TD></TR>\n'
    dot += """        </TABLE>
        >];

        silver [label=<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white" COLOR="#e0e0e0">
                <TR><TD COLSPAN="3" BGCOLOR="#f5f5f5" ALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="#666">Snowflake · Table</FONT></TD></TR>
                <TR><TD COLSPAN="3" BGCOLOR="#f5f5f5" ALIGN="LEFT"><B>CUSTOMERS_GOLDEN</B></TD></TR>
                <TR><TD COLSPAN="3" BGCOLOR="#f5f5f5" ALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="#2e7d32">Silver (Deduplicated)</FONT></TD></TR>
    """
    for col in SILVER_COLUMNS:
        bold = '<B>' + col + '</B>' if col in ("GOLDEN_ID", "IS_MASTER_RECORD") else col
        dot += f'            <TR><TD ALIGN="LEFT" PORT="{col}_l">→</TD><TD ALIGN="LEFT">{bold}</TD><TD ALIGN="RIGHT" PORT="{col}_r">→</TD></TR>\n'
    dot += """        </TABLE>
        >];

        gold_uk [label=<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white" COLOR="#e0e0e0">
                <TR><TD COLSPAN="2" BGCOLOR="#f5f5f5" ALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="#666">Snowflake · View</FONT></TD></TR>
                <TR><TD COLSPAN="2" BGCOLOR="#f5f5f5" ALIGN="LEFT"><B>CUSTOMERS_UK</B></TD></TR>
                <TR><TD COLSPAN="2" BGCOLOR="#f5f5f5" ALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="#e65100">Gold (UK filter)</FONT></TD></TR>
    """
    for col in GOLD_UK_COLUMNS:
        dot += f'            <TR><TD ALIGN="LEFT" PORT="{col}_l">→</TD><TD ALIGN="LEFT">{col}</TD></TR>\n'
    dot += """        </TABLE>
        >];

        gold_ie [label=<
            <TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="white" COLOR="#e0e0e0">
                <TR><TD COLSPAN="2" BGCOLOR="#f5f5f5" ALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="#666">Snowflake · Materialized View</FONT></TD></TR>
                <TR><TD COLSPAN="2" BGCOLOR="#f5f5f5" ALIGN="LEFT"><B>CUSTOMERS_IRELAND</B></TD></TR>
                <TR><TD COLSPAN="2" BGCOLOR="#f5f5f5" ALIGN="LEFT"><FONT POINT-SIZE="8" COLOR="#e65100">Gold (Ireland filter)</FONT></TD></TR>
    """
    for col in GOLD_IRELAND_COLUMNS:
        dot += f'            <TR><TD ALIGN="LEFT" PORT="{col}_l">→</TD><TD ALIGN="LEFT">{col}</TD></TR>\n'
    dot += """        </TABLE>
        >];

    """

    # Edges: Bronze right port -> Silver left port
    for col in BRONZE_COLUMNS:
        dot += f'    bronze:{col}_r -> silver:{col}_l [color="#1976d2"];\n'

    # Silver derived columns (from EMAIL right port to left port of derived)
    dot += '    bronze:EMAIL_r -> silver:GOLDEN_ID_l [color="#2e7d32", style=dashed];\n'
    dot += '    bronze:EMAIL_r -> silver:IS_MASTER_RECORD_l [color="#2e7d32", style=dashed];\n'

    # Edges: Silver right port -> Gold UK left port
    for col in GOLD_UK_COLUMNS:
        dot += f'    silver:{col}_r -> gold_uk:{col}_l [color="#e65100"];\n'

    # Edges: Silver right port -> Gold Ireland left port
    for col in GOLD_IRELAND_COLUMNS:
        dot += f'    silver:{col}_r -> gold_ie:{col}_l [color="#e65100"];\n'

    dot += "}\n"
    return dot


# --- Pipeline run history ---
lineage_df = session.sql("""
    SELECT RUN_ID, NOTEBOOK_NAME, STEP_NAME, SOURCE_OBJECT, TARGET_OBJECT,
           OPERATION, ROW_COUNT, EXECUTION_TIMESTAMP, DURATION_SECONDS, STATUS
    FROM PEPARTNERS_DB.CORE.PIPELINE_LINEAGE
    ORDER BY EXECUTION_TIMESTAMP DESC
""").to_pandas()

# --- Layout ---
tab1, tab2, tab3 = st.tabs(["Column Lineage Graph", "Lineage Matrix", "Run History"])

# --- Tab 1: Graphviz column lineage ---
with tab1:
    st.subheader("Column-Level Data Lineage")
    st.markdown("Tables shown with their columns. Arrows trace each column from source to target.")
    st.graphviz_chart(build_graphviz(), use_container_width=True)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**:blue[Blue arrows]** — Direct passthrough")
    with col2:
        st.markdown("**:green[Green dashed]** — Derived column (from EMAIL)")
    with col3:
        st.markdown("**:orange[Orange arrows]** — Silver → Gold passthrough")

    st.markdown("---")
    st.subheader("Task Graph (Scheduling)")
    task_dot = """
    digraph tasks {
        rankdir=LR;
        graph [fontname="Helvetica", bgcolor="transparent"];
        node [fontname="Helvetica", fontsize=10, shape=box, style="rounded,filled", fillcolor="#e3f2fd", color="#1565c0"];
        edge [color="#1565c0", arrowsize=0.7];

        t1 [label="TASK_DEDUPLICATE_CUSTOMERS\\n(root, every 24h)"];
        t2 [label="TASK_CUSTOMERS_UK_VIEW"];
        t3 [label="TASK_CUSTOMERS_IRELAND_MATVIEW"];

        t1 -> t2 -> t3;
    }
    """
    st.graphviz_chart(task_dot, use_container_width=True)

# --- Tab 2: Matrix view ---
with tab2:
    st.subheader("Column-Level Lineage Matrix")
    st.markdown("Each row shows how a column flows from **Bronze** through **Silver** to **Gold** layers.")

    rows = []
    for col in BRONZE_COLUMNS:
        rows.append({
            "Column": col,
            "Bronze (CUSTOMERS)": "Yes",
            "Silver (CUSTOMERS_GOLDEN)": "Passthrough",
            "Gold (CUSTOMERS_UK)": "Passthrough",
            "Gold (CUSTOMERS_IRELAND)": "Passthrough",
            "Transformation": "Direct",
        })
    rows.insert(0, {
        "Column": "GOLDEN_ID",
        "Bronze (CUSTOMERS)": "-",
        "Silver (CUSTOMERS_GOLDEN)": "NEW",
        "Gold (CUSTOMERS_UK)": "Passthrough",
        "Gold (CUSTOMERS_IRELAND)": "Passthrough",
        "Transformation": "DENSE_RANK() OVER (ORDER BY LOWER(EMAIL))",
    })
    rows.append({
        "Column": "IS_MASTER_RECORD",
        "Bronze (CUSTOMERS)": "-",
        "Silver (CUSTOMERS_GOLDEN)": "NEW",
        "Gold (CUSTOMERS_UK)": "Filter only",
        "Gold (CUSTOMERS_IRELAND)": "Filter only",
        "Transformation": "ROW_NUMBER() PARTITION BY EMAIL = 1",
    })

    lineage_table = pd.DataFrame(rows)
    st.dataframe(lineage_table, use_container_width=True, height=560)

    st.markdown("---")
    st.subheader("Inspect Column")
    selected_col = st.selectbox("Select column:", lineage_table["Column"].tolist())
    row = lineage_table[lineage_table["Column"] == selected_col].iloc[0]
    st.table(pd.DataFrame([row]))

# --- Tab 3: Run history ---
with tab3:
    st.subheader("Pipeline Run History")
    if lineage_df.empty:
        st.info("No pipeline runs recorded yet.")
    else:
        st.dataframe(lineage_df, use_container_width=True)

        st.markdown("---")
        st.subheader("Object-level Lineage")
        object_lineage = session.sql("""
            SELECT DISTINCT
                SOURCE_OBJECT AS "FROM",
                TARGET_OBJECT AS "TO",
                OPERATION,
                NOTEBOOK_NAME AS "EXECUTED_BY"
            FROM PEPARTNERS_DB.CORE.PIPELINE_LINEAGE
            WHERE STATUS = 'SUCCESS'
            ORDER BY SOURCE_OBJECT
        """).to_pandas()
        st.dataframe(object_lineage, use_container_width=True)

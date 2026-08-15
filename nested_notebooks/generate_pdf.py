#!/usr/bin/env python3
"""Generate PDF version of the Nested Notebooks Demo Script."""
import os
import subprocess
from fpdf import FPDF

BASE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.join(BASE, "images")
OUTPUT = os.path.join(BASE, "DEMO_SCRIPT.pdf")

# Convert SVGs to PNGs using rsvg-convert
png_files = {}
for svg in sorted(os.listdir(IMAGES)):
    if svg.endswith(".svg"):
        svg_path = os.path.join(IMAGES, svg)
        png_path = svg_path.replace(".svg", ".png")
        subprocess.run(
            ["rsvg-convert", "-w", "1600", "-o", png_path, svg_path],
            check=True,
        )
        png_files[svg.replace(".svg", "")] = png_path


class DemoPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("Arial", "", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
        self.add_font("Arial", "B", "/System/Library/Fonts/Supplemental/Arial Bold.ttf")
        self.add_font("Arial", "I", "/System/Library/Fonts/Supplemental/Arial Narrow Italic.ttf")

    def header(self):
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, "PE Partners | Nested Notebooks Demo", align="R")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Arial", "B", 18)
        self.set_text_color(26, 26, 46)
        self.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def subsection_title(self, title):
        self.set_font("Arial", "B", 14)
        self.set_text_color(91, 94, 166)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Arial", "", 11)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def quote_text(self, text):
        self.set_font("Arial", "I", 11)
        self.set_text_color(91, 94, 166)
        self.set_x(20)
        self.multi_cell(0, 6, f'"{text}"')
        self.set_x(10)
        self.set_font("Arial", "", 11)
        self.ln(2)

    def code_block(self, code):
        self.set_font("Arial", "", 9)
        self.set_fill_color(245, 245, 250)
        self.set_text_color(51, 51, 51)
        for line in code.split("\n"):
            self.cell(0, 5, f"  {line}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def add_image_full(self, png_key):
        if png_key in png_files:
            w = self.epw
            self.image(png_files[png_key], x=self.l_margin, w=w)
            self.ln(5)

    def bullet(self, text):
        self.set_font("Arial", "", 11)
        self.set_text_color(51, 51, 51)
        self.cell(5)
        self.cell(0, 6, f"  \u2022  {text}", new_x="LMARGIN", new_y="NEXT")


pdf = DemoPDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# Title page
pdf.ln(30)
pdf.set_font("Arial", "B", 28)
pdf.set_text_color(26, 26, 46)
pdf.cell(0, 15, "Nested Notebooks Demo", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)
pdf.set_font("Arial", "", 14)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 8, "Customer Deduplication Pipeline with Lineage Tracking", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(3)
pdf.cell(0, 8, "Snowflake Tasks | Workspace Notebooks | Pipeline Lineage", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(20)
pdf.add_image_full("01_pipeline_flow")

# Architecture page
pdf.add_page()
pdf.section_title("Architecture")
pdf.body_text(
    "This pipeline uses three layers: an Orchestration Layer (Snowflake Tasks), "
    "a Data Layer (tables and views), and an Observability Layer (lineage tracking)."
)
pdf.add_image_full("02_architecture")

# Section 1: The Problem
pdf.add_page()
pdf.section_title("1. The Problem")
pdf.quote_text(
    "Customer data often has duplicates \u2014 same person, multiple records, "
    "slightly different emails or entry dates. Before we can build reliable "
    "regional views, we need a single golden source of truth."
)
pdf.body_text("Show the CUSTOMERS table and identify duplicates by email:")
pdf.code_block(
    "SELECT EMAIL, COUNT(*) AS cnt\n"
    "FROM PEPARTNERS_DB.CORE.CUSTOMERS\n"
    "WHERE EMAIL IS NOT NULL\n"
    "GROUP BY EMAIL\n"
    "ORDER BY cnt DESC;"
)

# Section 2: The Solution
pdf.add_page()
pdf.section_title("2. The Solution: Notebook-Driven Pipeline")
pdf.quote_text(
    "We've built three notebooks that form a pipeline. Each one does one job, "
    "logs its lineage, and the whole thing is orchestrated by Snowflake Tasks."
)
pdf.ln(3)
pdf.subsection_title("Notebooks")
pdf.bullet("01_deduplicate_customers \u2014 Groups by email, assigns GOLDEN_ID, picks most recent as master")
pdf.bullet("02_customers_uk_view \u2014 Creates a view of UK master records")
pdf.bullet("03_customers_ireland_matview \u2014 Creates a materialized view of Ireland master records")
pdf.ln(5)
pdf.subsection_title("Key Design Decisions")
pdf.bullet("DENSE_RANK over email gives a stable golden ID")
pdf.bullet("IS_MASTER_RECORD flag keeps all records but marks the canonical one")
pdf.bullet("Views sit on top of the golden table \u2014 no data duplication")

# Section 3: Lineage
pdf.add_page()
pdf.section_title("3. Lineage Tracking")
pdf.quote_text(
    "Every notebook logs its source, target, operation, and row count to a lineage table. "
    "This gives us an auditable record of what happened, when, and where the data flowed."
)
pdf.code_block(
    "SELECT SOURCE_OBJECT AS \"FROM\", TARGET_OBJECT AS \"TO\",\n"
    "       OPERATION, NOTEBOOK_NAME, ROW_COUNT, EXECUTION_TIMESTAMP\n"
    "FROM PEPARTNERS_DB.CORE.PIPELINE_LINEAGE\n"
    "ORDER BY EXECUTION_TIMESTAMP DESC;"
)
pdf.add_image_full("03_lineage")
pdf.body_text(
    "This is custom lineage we control \u2014 complementing Snowflake's built-in ACCESS_HISTORY "
    "and object dependencies. It captures the notebook that created each object and the "
    "row counts at execution time."
)

# Section 4: Task Orchestration
pdf.add_page()
pdf.section_title("4. Task Orchestration")
pdf.quote_text(
    "These notebooks don't just run in isolation. They're wired into a dependent task graph."
)
pdf.add_image_full("04_task_graph")
pdf.body_text(
    "The root task runs daily. Each child only fires after its predecessor succeeds. "
    "If dedup fails, the downstream views don't get stale data \u2014 they simply don't run."
)
pdf.ln(3)
pdf.subsection_title("Manual Trigger")
pdf.code_block("EXECUTE TASK PEPARTNERS_DB.CORE.TASK_DEDUPLICATE_CUSTOMERS;")
pdf.subsection_title("Check Execution")
pdf.code_block(
    "SELECT name, state, scheduled_time, completed_time\n"
    "FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(\n"
    "    SCHEDULED_TIME_RANGE_START => DATEADD('minute', -5, CURRENT_TIMESTAMP()),\n"
    "    RESULT_LIMIT => 10\n"
    "))\n"
    "WHERE name LIKE 'TASK_CUSTOMERS%' OR name = 'TASK_DEDUPLICATE_CUSTOMERS'\n"
    "ORDER BY scheduled_time DESC;"
)

# Section 5: Results
pdf.add_page()
pdf.section_title("5. Results")
pdf.code_block(
    "-- Golden source: all records with master flag\n"
    "SELECT * FROM PEPARTNERS_DB.CORE.CUSTOMERS_GOLDEN LIMIT 10;\n\n"
    "-- UK customers only (master records)\n"
    "SELECT * FROM PEPARTNERS_DB.CORE.CUSTOMERS_UK;\n\n"
    "-- Ireland customers (materialized for fast access)\n"
    "SELECT * FROM PEPARTNERS_DB.CORE.CUSTOMERS_IRELAND;"
)

# Section 6: Why This Matters
pdf.section_title("6. Why This Matters")
pdf.add_image_full("05_takeaways")
pdf.ln(3)
pdf.bullet("Notebooks as pipeline steps \u2014 testable, readable, self-documenting")
pdf.bullet("Dependent tasks \u2014 guaranteed execution order, no race conditions")
pdf.bullet("Built-in lineage \u2014 full audit trail without external tools")
pdf.bullet("Golden source pattern \u2014 deduplicate once, serve many views downstream")
pdf.bullet("Materialized views \u2014 pre-computed for fast dashboard queries")
pdf.ln(5)
pdf.quote_text(
    "This pattern scales to any number of downstream consumers. Add a new country? "
    "Add a notebook and a task \u2014 the lineage tracks it automatically."
)

# Quick Reference
pdf.add_page()
pdf.section_title("Quick Reference")
pdf.set_font("Arial", "", 9)
pdf.set_fill_color(245, 245, 250)
header = f"{'Object':<35} {'Type':<20} {'Purpose'}"
pdf.cell(0, 5, f"  {header}", new_x="LMARGIN", new_y="NEXT", fill=True)
pdf.cell(0, 5, f"  {'-'*80}", new_x="LMARGIN", new_y="NEXT", fill=True)
rows = [
    ("CUSTOMERS", "Table", "Raw source data"),
    ("CUSTOMERS_GOLDEN", "Table", "Deduplicated with GOLDEN_ID"),
    ("CUSTOMERS_UK", "View", "UK master records"),
    ("CUSTOMERS_IRELAND", "Materialized View", "Ireland master records"),
    ("PIPELINE_LINEAGE", "Table", "Execution lineage log"),
    ("TASK_DEDUPLICATE_CUSTOMERS", "Task (root)", "Runs notebook 1 daily"),
    ("TASK_CUSTOMERS_UK_VIEW", "Task (child)", "Runs notebook 2 after root"),
    ("TASK_CUSTOMERS_IRELAND_MATVIEW", "Task (child)", "Runs notebook 3 after UK"),
]
for obj, typ, purpose in rows:
    pdf.cell(0, 5, f"  {obj:<35} {typ:<20} {purpose}", new_x="LMARGIN", new_y="NEXT", fill=True)

# Cleanup
pdf.ln(10)
pdf.subsection_title("Cleanup")
pdf.code_block(
    "ALTER TASK PEPARTNERS_DB.CORE.TASK_DEDUPLICATE_CUSTOMERS SUSPEND;\n"
    "DROP TASK IF EXISTS PEPARTNERS_DB.CORE.TASK_CUSTOMERS_IRELAND_MATVIEW;\n"
    "DROP TASK IF EXISTS PEPARTNERS_DB.CORE.TASK_CUSTOMERS_UK_VIEW;\n"
    "DROP TASK IF EXISTS PEPARTNERS_DB.CORE.TASK_DEDUPLICATE_CUSTOMERS;\n"
    "DROP MATERIALIZED VIEW IF EXISTS PEPARTNERS_DB.CORE.CUSTOMERS_IRELAND;\n"
    "DROP VIEW IF EXISTS PEPARTNERS_DB.CORE.CUSTOMERS_UK;\n"
    "DROP TABLE IF EXISTS PEPARTNERS_DB.CORE.CUSTOMERS_GOLDEN;\n"
    "DROP TABLE IF EXISTS PEPARTNERS_DB.CORE.PIPELINE_LINEAGE;"
)

pdf.output(OUTPUT)
print(f"PDF generated: {OUTPUT}")

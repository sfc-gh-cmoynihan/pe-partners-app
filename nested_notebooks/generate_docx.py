#!/usr/bin/env python3
"""Generate Word document comparing dbt vs Nested Notebooks."""
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Styles
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

# Title
title = doc.add_heading('dbt vs Nested Notebooks', level=0)
title.runs[0].font.color.rgb = RGBColor(26, 26, 46)

doc.add_paragraph(
    'A comparison of dbt and Snowflake Nested Notebooks for data pipeline orchestration, '
    'in the context of the PE Partners customer deduplication pipeline.'
)

# Comparison Table
doc.add_heading('Feature Comparison', level=1)

headers = ['Dimension', 'dbt', 'Nested Notebooks']
rows = [
    ['DAG resolution', 'Automatic from ref() \u2014 dbt infers the entire dependency graph from SQL references', 'Manual \u2014 you wire AFTER clauses in task definitions yourself'],
    ['Lineage', 'Built-in. Column-level lineage, auto-generated docs site', 'Custom (PIPELINE_LINEAGE table). More control, more work'],
    ['Testing', 'Declarative: unique, not_null, accepted_values, relationships as YAML', 'SQL assertions in notebook cells or a separate test notebook'],
    ['Incremental logic', 'is_incremental() macro + merge/insert strategies built in', 'Code the MERGE yourself \u2014 full flexibility but no guardrails'],
    ['Environment promotion', '--target dev/prod swaps databases. Same code, different env', 'Notebooks run against whatever context they\'re in \u2014 manage env switching yourself'],
    ['Materializations', 'table, view, incremental, ephemeral, materialized_view \u2014 one config line', 'Write the DDL explicitly (CTAS, CREATE VIEW, CREATE MATERIALIZED VIEW)'],
    ['Version control', 'SQL files in git, clean diffs, PR reviews', '.ipynb files in git \u2014 JSON diffs are noisy, harder to review'],
    ['Collaboration', 'SQL-only, anyone can contribute a model', 'Python + SQL + markdown \u2014 more expressive, higher skill floor'],
    ['Scheduling', 'External (Snowflake Tasks, Airflow, dbt Cloud) \u2014 dbt doesn\'t schedule itself', 'Built-in via Snowflake Tasks \u2014 orchestration is native'],
    ['Flexibility', 'SQL-only (Jinja for logic). Python models are second-class', 'Full Python + SQL. ML, API calls, complex logic all in one place'],
    ['Documentation', 'Auto-generated from schema YAML + descriptions', 'Markdown cells live alongside code \u2014 more narrative, less structured'],
]

table = doc.add_table(rows=1, cols=3)
table.style = 'Medium Shading 1 Accent 1'
table.alignment = WD_TABLE_ALIGNMENT.CENTER

# Header row
for i, h in enumerate(headers):
    cell = table.rows[0].cells[i]
    cell.text = h
    cell.paragraphs[0].runs[0].bold = True

# Data rows
for row_data in rows:
    row = table.add_row()
    for i, val in enumerate(row_data):
        row.cells[i].text = val

# Set column widths
for row in table.rows:
    row.cells[0].width = Cm(3.5)
    row.cells[1].width = Cm(7)
    row.cells[2].width = Cm(7)

# dbt advantages
doc.add_heading('What dbt Gives You That Notebooks Don\'t', level=1)

advantages_dbt = [
    ('ref() \u2014 implicit dependency management', 
     'You never manually wire DAG edges. If model B selects from {{ ref(\'model_a\') }}, '
     'dbt knows B depends on A. In notebooks, you manually create tasks with AFTER clauses.'),
    ('Schema tests as first-class citizens', 
     'A one-line YAML entry like tests: [unique, not_null] runs assertions every build. '
     'In notebooks, you write verification SQL and decide what to do when it fails.'),
    ('Idempotent incremental builds', 
     'dbt run only rebuilds what changed (with --select and state comparison). '
     'Notebooks re-execute everything top to bottom.'),
    ('Standardised project structure', 
     'models/, tests/, macros/, seeds/ \u2014 any dbt developer knows where to look. '
     'Notebooks are free-form.'),
]

for title_text, desc in advantages_dbt:
    p = doc.add_paragraph()
    run = p.add_run(f'{title_text}. ')
    run.bold = True
    p.add_run(desc)

# Notebook advantages
doc.add_heading('What Notebooks Give You That dbt Doesn\'t', level=1)

advantages_nb = [
    ('Mixed Python + SQL in one flow', 
     'Deduplication could use fuzzy matching (Levenshtein, ML models) that would be painful in Jinja SQL.'),
    ('Visual output inline', 
     'Charts, data previews, profiling \u2014 all visible as you develop. dbt is headless.'),
    ('Lower ceremony for simple pipelines', 
     'Three notebooks + one task graph was ~50 lines of SQL total. The equivalent dbt project needs '
     'dbt_project.yml, profiles.yml, schema.yml, model files, and a separate scheduling layer.'),
    ('Native Snowflake execution', 
     'EXECUTE NOTEBOOK runs inside Snowflake with no external runner. '
     'dbt needs dbt Core/Cloud or snow dbt deploy.'),
]

for title_text, desc in advantages_nb:
    p = doc.add_paragraph()
    run = p.add_run(f'{title_text}. ')
    run.bold = True
    p.add_run(desc)

# When to use which
doc.add_heading('When to Use Which', level=1)

doc.add_heading('Use dbt when:', level=2)
dbt_items = [
    '10+ models with complex dependencies',
    'Team of analysts who need to collaborate',
    'Testing, documentation, and CI/CD are required',
    'SQL-heavy transformations',
    'Established data engineering practice',
]
for item in dbt_items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_heading('Use Nested Notebooks when:', level=2)
nb_items = [
    'Small pipelines (< 10 steps)',
    'Mixed Python/SQL logic',
    'Rapid prototyping and demos',
    'ML-adjacent workflows',
    'Single-developer ownership',
    'Visual exploration is important',
]
for item in nb_items:
    doc.add_paragraph(item, style='List Bullet')

# Summary
doc.add_heading('Summary', level=1)
doc.add_paragraph(
    'For the PE Partners customer deduplication pipeline (3 steps, straightforward SQL, '
    'demo context), notebooks are the right call. If this grew to 30 models with multiple '
    'contributors and a CI/CD requirement, dbt would earn its overhead.'
)

output_path = '/Users/cmoynihan/Documents/code/lansdownepartners/nested_notebooks/dbt_vs_notebooks.docx'
doc.save(output_path)
print(f'Word document saved: {output_path}')

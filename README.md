# Material Handling Platform Trolley - Technical Assessment

This repository provides a semi-automated engineering workflow that converts trolley requirements into calculation, CAD, drawing, costing, and timeline outputs.

## Overview

Pipeline outputs generated from one input specification:

- Engineering calculations
- Parametric CAD model (OpenSCAD)
- 2D fabrication drawing views (DXF and PDF)
- BOM and costing sheet (CSV)
- Manufacturing timeline estimate

The assessment implementation timeline is fixed at 72 hours and is recorded in the generated summary.

## Input Schema

Accepted fields in JSON input:

- load_capacity_kg
- platform_length_mm
- platform_width_mm
- desired_material: Mild Steel or Stainless Steel
- number_of_wheels: 2 or 4
- operating_environment: Indoor or Outdoor

Validation constraints:

- load_capacity_kg must be greater than 0
- platform_length_mm must be at least 400
- platform_width_mm must be at least 300

Example input files available in this repository:

- examples/sample_input_4.json
- examples/sample_input_5.json

## Outputs

For a run folder such as outputs/run_001, the workflow generates:

- outputs/run_001/summary.json
- outputs/run_001/cad/trolley.scad
- outputs/run_001/drawings/trolley_views.dxf
- outputs/run_001/drawings/trolley_views.pdf
- outputs/run_001/costing/costing_sheet.csv

If matplotlib is unavailable, PDF generation falls back to a text file in the drawings directory.

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies.

~~~bash
pip install -r requirements.txt
~~~

Dependencies listed in this project:

- matplotlib
- streamlit

## Run The Workflow (CLI)

Run from JSON input:

~~~bash
python src/main.py --input examples/sample_input_4.json --out outputs/run_sample_input_4
~~~

Or run using direct CLI fields:

~~~bash
python src/main.py --use-cli-input --load-capacity-kg 500 --platform-length-mm 1200 --platform-width-mm 800 --desired-material "Mild Steel" --number-of-wheels 4 --operating-environment Indoor --out outputs/run_cli_001
~~~

## Run The Frontend

The Streamlit app is available at frontend/app.py.

~~~bash
streamlit run frontend/app.py
~~~

Frontend run outputs are stored under frontend/runs.

## Automation Coverage

Automated workflow stages:

- Requirement parsing and validation
- Engineering calculations
- CAD generation (OpenSCAD script)
- Drawing generation (DXF plus PDF/text fallback)
- BOM and cost estimation
- Manufacturing timeline estimation

## Assumptions And Limitations

- Structural sizing is first-pass and conservative, and is not a substitute for FEA.
- CAD output is emitted as OpenSCAD script for reliability in a free toolchain.
- PDF drawing output depends on matplotlib.

## Timeline Clarification

- Assessment implementation timeline: 72 hours
- Manufacturing timeline: estimated fabrication and assembly effort for the generated design

Both values are captured in summary.json.

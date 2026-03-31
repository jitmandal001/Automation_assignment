# Material Handling Platform Trolley - Technical Assessment

This project implements a semi-automated engineering workflow that converts client requirements into:

- Engineering calculations
- Parametric CAD model script
- 2D fabrication drawings
- BOM and cost estimation
- Manufacturing timeline

Project timeline for this assessment is fixed at 72 hours.

## 1. Inputs

Accepted input fields (JSON):

- load_capacity_kg
- platform_length_mm
- platform_width_mm
- desired_material (Mild Steel or Stainless Steel)
- number_of_wheels (2 or 4)
- operating_environment (Indoor or Outdoor)

Example: examples/sample_input.json

## 2. Outputs

Running the workflow creates:

- outputs/.../summary.json
- outputs/.../cad/trolley.scad
- outputs/.../drawings/trolley_views.dxf
- outputs/.../drawings/trolley_views.pdf (or .txt fallback if matplotlib unavailable)
- outputs/.../costing/costing_sheet.csv

## 3. Run Instructions

1. Install dependencies:

   pip install -r requirements.txt

2. Run:

   python src/main.py --input examples/sample_input.json --out outputs/run_001

## 4. Automation Coverage

This workflow automates at least 3 required steps:

- Requirement parsing (JSON input + validation)
- Engineering calculations
- CAD generation (OpenSCAD parametric script)
- Drawing generation (DXF + PDF)
- BOM and costing

## 5. Engineering Assumptions

See docs/submission_documentation.md (Section 3: Key Assumptions).

## 6. Limitations

- Structural sizing is first-pass and conservative, not FEA.
- CAD output is OpenSCAD script by default for reliability in a free toolchain.
- PDF drawing output uses matplotlib if available; otherwise text fallback is generated.

## 7. Timeline Clarification

- Project/assignment timeline: 72 hours (captured in summary output as `project_timeline.assignment_timeline_hours`).
- Manufacturing timeline: estimated fabrication and assembly hours for the designed trolley (captured as `manufacturing_timeline`).

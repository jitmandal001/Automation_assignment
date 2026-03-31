from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from bom_costing import build_bom, estimate_costs, export_costing_csv
from cad_generator import generate_openscad_model
from calculations import calculate
from drawing_generator import generate_drawings
from models import InputSpec
from timeline import estimate_manufacturing_timeline


def _load_input(path: str) -> InputSpec:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    spec = InputSpec(
        load_capacity_kg=float(data["load_capacity_kg"]),
        platform_length_mm=float(data["platform_length_mm"]),
        platform_width_mm=float(data["platform_width_mm"]),
        desired_material=str(data["desired_material"]),
        number_of_wheels=int(data["number_of_wheels"]),
        operating_environment=str(data["operating_environment"]),
    )
    spec.validate()
    return spec


def _load_input_from_args(args: argparse.Namespace) -> InputSpec:
    spec = InputSpec(
        load_capacity_kg=float(args.load_capacity_kg),
        platform_length_mm=float(args.platform_length_mm),
        platform_width_mm=float(args.platform_width_mm),
        desired_material=str(args.desired_material),
        number_of_wheels=int(args.number_of_wheels),
        operating_environment=str(args.operating_environment),
    )
    spec.validate()
    return spec


def run_workflow(output_dir: str, input_json: str | None = None, cli_args: argparse.Namespace | None = None) -> dict:
    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    if input_json:
        spec = _load_input(input_json)
    elif cli_args:
        spec = _load_input_from_args(cli_args)
    else:
        raise ValueError("Provide either input_json or cli_args")

    calc = calculate(spec)

    cad_path = generate_openscad_model(spec, calc, str(out_root / "cad" / "trolley.scad"))
    drawings = generate_drawings(spec, calc, str(out_root / "drawings"))

    bom = build_bom(spec, calc)
    costs = estimate_costs(spec, calc)
    timeline = estimate_manufacturing_timeline(spec, calc)

    costing_csv = out_root / "costing" / "costing_sheet.csv"
    costing_csv.parent.mkdir(parents=True, exist_ok=True)
    export_costing_csv(str(costing_csv), spec, calc, costs, bom)

    summary = {
        "input": asdict(spec),
        "project_timeline": {
            "assignment_timeline_hours": 72,
            "note": "This is the total allowed implementation window for the assessment.",
        },
        "engineering_calculations": asdict(calc),
        "drawings": drawings,
        "cad_model": cad_path,
        "bom": bom,
        "cost_estimation": costs,
        "manufacturing_timeline": timeline,
    }

    summary_path = out_root / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Material Handling Trolley semi-automated workflow")
    parser.add_argument("--input", default="examples/sample_input.json", help="Path to JSON input")
    parser.add_argument("--use-cli-input", action="store_true", help="Use CLI fields instead of JSON input")
    parser.add_argument("--load-capacity-kg", type=float, default=500)
    parser.add_argument("--platform-length-mm", type=float, default=1200)
    parser.add_argument("--platform-width-mm", type=float, default=800)
    parser.add_argument("--desired-material", type=str, default="Mild Steel")
    parser.add_argument("--number-of-wheels", type=int, default=4)
    parser.add_argument("--operating-environment", type=str, default="Indoor")
    parser.add_argument("--out", default="outputs/run_001", help="Output directory")
    args = parser.parse_args()

    if args.use_cli_input:
        summary = run_workflow(args.out, cli_args=args)
    else:
        summary = run_workflow(args.out, input_json=args.input)

    print("Workflow completed.")
    print(f"Summary: {Path(args.out) / 'summary.json'}")
    print(f"CAD model: {summary['cad_model']}")
    print(f"Drawings: {summary['drawings']}")


if __name__ == "__main__":
    main()

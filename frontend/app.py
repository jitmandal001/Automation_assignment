from __future__ import annotations

import base64
import gzip
import io
import json
import sys
import time
import zipfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import streamlit as st

# Allow frontend app to import existing backend modules.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bom_costing import build_bom, estimate_costs, export_costing_csv
from cad_generator import generate_openscad_model
from calculations import calculate
from drawing_generator import generate_drawings
from models import InputSpec
from timeline import estimate_manufacturing_timeline


def _inject_styles() -> None:
    st.markdown(
        """
<style>
.main {
    background:
        radial-gradient(circle at 10% 10%, #dcffe8 0%, #f7fbff 32%, transparent 58%),
        radial-gradient(circle at 90% 20%, #e8f9ff 0%, transparent 46%),
        linear-gradient(145deg, #f3fff8 0%, #f8fbff 48%, #fffef7 100%);
}
.block-container {
    max-width: 100% !important;
    width: 100%;
    padding-top: 0.9rem;
    padding-left: 1rem;
    padding-right: 1rem;
}
.hero {
    border-radius: 20px;
    padding: 24px 26px;
  color: #0a2a1a;
    background: linear-gradient(120deg, #d5ffea 0%, #effff8 35%, #e8f4ff 78%, #fff7db 100%);
    border: 1px solid #b6efcd;
    box-shadow: 0 12px 32px rgba(7, 104, 57, 0.12);
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: "";
    position: absolute;
    inset: -40%;
    background: conic-gradient(from 180deg, transparent 0deg, rgba(36, 226, 131, 0.16) 70deg, transparent 150deg, rgba(44, 171, 255, 0.14) 210deg, transparent 280deg, rgba(245, 203, 84, 0.12) 320deg, transparent 360deg);
    animation: aurora 7s linear infinite;
    pointer-events: none;
}
@keyframes aurora {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
.hero h1 {
  margin: 0;
  font-size: 2rem;
    position: relative;
    z-index: 1;
}
.hero p {
  margin: 8px 0 0;
  color: #24543d;
    position: relative;
    z-index: 1;
}
.panel {
    border-radius: 16px;
    background: linear-gradient(180deg, #ffffffed 0%, #fbfffd 100%);
    border: 1px solid #cae8d3;
    padding: 16px;
    box-shadow: 0 10px 28px rgba(25, 95, 62, 0.08);
}
.node-wrap {
    display: grid;
    grid-template-columns: repeat(2, minmax(180px, 1fr));
    align-items: stretch;
    gap: 10px;
    margin-top: 6px;
    width: 100%;
}
.node {
  text-align: center;
  font-size: 0.82rem;
    font-weight: 600;
    line-height: 1.24;
    padding: 11px 8px;
    border-radius: 12px;
    border: 1px solid #bedec9;
    background: linear-gradient(180deg, #f7fffa 0%, #eefaf2 100%);
  color: #1c4733;
    min-height: 78px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}
.node::after {
    content: "";
    position: absolute;
    left: 10px;
    right: 10px;
    bottom: 8px;
    height: 4px;
    border-radius: 999px;
    background: #d9e9df;
}
.node.done {
    background: linear-gradient(180deg, #dbffe8 0%, #c7f8db 100%);
    border-color: #27b866;
    color: #0f4d2d;
    box-shadow: 0 0 0 1px rgba(39, 184, 102, 0.25) inset;
}
.node.done::after {
    background: linear-gradient(90deg, #23b563, #65da9d);
}
.node.active {
    background: linear-gradient(130deg, #dffff0 0%, #ebfff4 48%, #ddf3ff 100%);
    border-color: #00b956;
    box-shadow: 0 0 0 2px rgba(0, 185, 86, 0.22) inset, 0 0 24px rgba(0, 185, 86, 0.18);
    animation: pulseNode 1.2s ease-in-out infinite;
}
.node.active::after {
    background: linear-gradient(90deg, #0da84f, #b7ffd3, #0da84f);
    background-size: 220% 100%;
    animation: flow 0.8s linear infinite;
}
@keyframes pulseNode {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-2px); }
    100% { transform: translateY(0px); }
}
@keyframes flow {
  0% { background-position: 0% 0%; }
    100% { background-position: 240% 0%; }
}
.small-note {
    color: #2c4f3b;
  font-size: 0.86rem;
}

.downloads-title {
    margin-top: 10px;
    margin-bottom: 10px;
    padding: 8px 12px;
    border-radius: 10px;
    display: inline-block;
    font-weight: 700;
    color: #0f4b2f;
    background: linear-gradient(120deg, #ddffea, #ecfff4);
    border: 1px solid #b8eecf;
}

.outputs-shell {
    margin-top: 14px;
    padding: 14px;
    border-radius: 16px;
    border: 1px solid #bfe7cf;
    background: linear-gradient(180deg, #fffffff0 0%, #f8fffb 100%);
    box-shadow: 0 10px 28px rgba(25, 95, 62, 0.08);
}

.outputs-note {
    margin: 0;
    color: #24543d;
    font-size: 0.9rem;
}

.stDownloadButton > button {
    border-radius: 12px !important;
    border: 1px solid #b9e5c8 !important;
    background: linear-gradient(180deg, #ffffff 0%, #f3fff8 100%) !important;
    color: #144e33 !important;
    font-weight: 600 !important;
    box-shadow: 0 6px 18px rgba(35, 142, 87, 0.10);
}

.stDownloadButton > button:hover {
    border-color: #60c98e !important;
    background: linear-gradient(180deg, #effff6 0%, #ddffea 100%) !important;
    color: #0e432b !important;
}

.stLinkButton > a {
    border-radius: 12px !important;
    border: 1px solid #9fc1ff !important;
    background: linear-gradient(180deg, #ffffff 0%, #eef4ff 100%) !important;
    color: #1c3f8c !important;
    font-weight: 600 !important;
    box-shadow: 0 6px 18px rgba(40, 90, 180, 0.10);
}

.stLinkButton > a:hover {
    border-color: #6a95ef !important;
    background: linear-gradient(180deg, #eef4ff 0%, #dfe9ff 100%) !important;
    color: #173573 !important;
}

@media (max-width: 980px) {
    .node-wrap {
        grid-template-columns: repeat(2, minmax(150px, 1fr));
    }
    .node {
        min-height: 76px;
    }
}

@media (max-width: 640px) {
    .block-container {
        padding-left: 0.6rem;
        padding-right: 0.6rem;
    }
    .node {
        font-size: 0.78rem;
    }
    .node-wrap {
        grid-template-columns: 1fr;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _pipeline_html(stage: int, labels: list[str]) -> str:
    parts = ["<div class='panel'><div class='node-wrap'>"]
    for i, label in enumerate(labels):
        cls = "node"
        if i < stage:
            cls += " done"
        elif i == stage:
            cls += " active"
        safe_label = label.replace("\n", "<br/>")
        parts.append(f"<div class='{cls}'>{safe_label}</div>")
    parts.append("</div></div>")
    return "".join(parts)


def _build_zip(file_paths: list[Path]) -> bytes:
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in file_paths:
            if p.exists():
                zf.write(p, arcname=p.name)
    mem.seek(0)
    return mem.read()


def _openscad_playground_url(scad_text: str) -> str:
    payload = gzip.compress(scad_text.encode("utf-8"))
    encoded = base64.b64encode(payload).decode("ascii")
    return f"https://ochafik.com/openscad2/#{encoded}"


def _render_pdf_preview(pdf_path: Path) -> None:
    encoded = base64.b64encode(pdf_path.read_bytes()).decode("ascii")
    st.markdown(
        (
            "<iframe "
            f"src='data:application/pdf;base64,{encoded}' "
            "width='100%' height='620' type='application/pdf'></iframe>"
        ),
        unsafe_allow_html=True,
    )


def _render_preview(preview_kind: str, summary: dict, summary_path: Path, cad_path: Path, dxf_path: Path, pdf_path: Path, csv_path: Path) -> None:
    if preview_kind == "summary":
        st.json(summary)
        return

    if preview_kind == "scad":
        st.code(cad_path.read_text(encoding="utf-8"), language="scad")
        return

    if preview_kind == "dxf":
        st.code(dxf_path.read_text(encoding="utf-8"), language="plaintext")
        return

    if preview_kind == "pdf":
        _render_pdf_preview(pdf_path)
        return

    if preview_kind == "csv":
        st.code(csv_path.read_text(encoding="utf-8"), language="csv")
        return

    st.code(summary_path.read_text(encoding="utf-8"), language="json")


def _next_frontend_run_dir() -> Path:
    runs_root = ROOT / "frontend" / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    max_idx = 0
    for child in runs_root.iterdir():
        if not child.is_dir():
            continue
        name = child.name
        if not name.startswith("run_"):
            continue
        suffix = name[4:]
        if suffix.isdigit():
            max_idx = max(max_idx, int(suffix))

    return runs_root / f"run_{max_idx + 1:03d}"


def _run_pipeline(spec: InputSpec, output_dir: Path) -> tuple[dict, list[Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = output_dir.name

    calc = calculate(spec)

    cad_file = Path(generate_openscad_model(spec, calc, str(output_dir / "trolley.scad")))
    drawings = generate_drawings(spec, calc, str(output_dir))

    bom = build_bom(spec, calc)
    costs = estimate_costs(spec, calc)
    timeline = estimate_manufacturing_timeline(spec, calc)

    costing_csv = output_dir / "costing_sheet.csv"
    export_costing_csv(str(costing_csv), spec, calc, costs, bom)

    summary = {
        "run_metadata": {
            "run_id": run_id,
            "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        },
        "input": asdict(spec),
        "project_timeline": {
            "assignment_timeline_hours": 72,
            "note": "Total assessment execution window.",
        },
        "engineering_calculations": asdict(calc),
        "drawings": drawings,
        "cad_model": str(cad_file),
        "bom": bom,
        "cost_estimation": costs,
        "manufacturing_timeline": timeline,
    }

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    generated = [
        summary_path,
        cad_file,
        Path(drawings["dxf"]),
        Path(drawings["pdf"]),
        costing_csv,
    ]

    return summary, generated


def main() -> None:
    st.set_page_config(page_title="Trolley Design Studio", page_icon="🛠️", layout="wide")
    _inject_styles()

    st.markdown(
        """
<div class='hero'>
  <h1>Material Handling Trolley - Design Studio</h1>
  <p>Enter requirements, watch the pipeline animate through engineering stages, and download all generated outputs.</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.0, 1.35], gap="large")

    labels = [
        "Requirements\nParsing",
        "Requirements\nParsed",
        "Calculating\nValues",
        "Values\nCalculated",
        "Generating\nCAD",
        "Generating\n2D Drawings",
        "Building BOM\n& Cost",
        "Packaging\nOutputs",
    ]

    with left:
        st.subheader("Input Requirements")
        with st.form("input_form", border=True):
            load_capacity = st.number_input(
                "Load Capacity (kg)",
                min_value=50.0,
                max_value=3000.0,
                value=650.0,
                step=10.0,
                key="load_capacity_input",
            )
            length = st.number_input(
                "Platform Length (mm)",
                min_value=500.0,
                max_value=3000.0,
                value=1300.0,
                step=10.0,
                key="platform_length_input",
            )
            width = st.number_input(
                "Platform Width (mm)",
                min_value=350.0,
                max_value=1800.0,
                value=850.0,
                step=10.0,
                key="platform_width_input",
            )
            material = st.selectbox(
                "Material",
                ["Mild Steel", "Stainless Steel"],
                index=0,
                key="material_input",
            )
            wheels = st.radio("Number of Wheels", [2, 4], horizontal=True, key="wheels_input")
            environment = st.selectbox(
                "Operating Environment",
                ["Indoor", "Outdoor"],
                index=1,
                key="environment_input",
            )

            run_btn = st.form_submit_button("Generate Design Outputs", type="primary", use_container_width=True)

        st.caption("Tip: Use 4 wheels for higher loads and safer load-per-wheel distribution.")

    with right:
        st.subheader("Pipeline Status")
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        live_note = st.empty()

    output_area = st.container()

    if "frontend_result" in st.session_state:
        status_placeholder.markdown(_pipeline_html(len(labels), labels), unsafe_allow_html=True)
        progress_placeholder.progress(1.0, text="Completed. Outputs are ready for download.")
        live_note.markdown("<p class='small-note'>Last run is available in the full-width outputs section below.</p>", unsafe_allow_html=True)

    if run_btn:
        # Force a new fresh result on each generate click.
        st.session_state.pop("frontend_result", None)

        spec = InputSpec(
            load_capacity_kg=float(load_capacity),
            platform_length_mm=float(length),
            platform_width_mm=float(width),
            desired_material=str(material),
            number_of_wheels=int(wheels),
            operating_environment=str(environment),
        )

        try:
            spec.validate()
        except Exception as exc:
            st.error(f"Input validation failed: {exc}")
            return

        out_dir = _next_frontend_run_dir()

        stage_messages = [
            "Parsing requirements...",
            "Requirements parsed successfully.",
            "Running engineering calculations...",
            "Calculated frame, mass, wheel load, and stability.",
            "Generating parametric 3D CAD model...",
            "Generating 2D fabrication drawings...",
            "Compiling BOM, costing, and timeline...",
            "Packaging all outputs for download...",
        ]

        for idx, msg in enumerate(stage_messages):
            status_placeholder.markdown(_pipeline_html(idx, labels), unsafe_allow_html=True)
            progress_placeholder.progress((idx + 1) / len(stage_messages), text=msg)
            live_note.markdown(f"<p class='small-note'>{msg}</p>", unsafe_allow_html=True)
            time.sleep(0.6)

        summary, files = _run_pipeline(spec, out_dir)

        summary_path = out_dir / "summary.json"
        cad_path = out_dir / "trolley.scad"
        dxf_path = out_dir / "trolley_views.dxf"
        pdf_path = out_dir / "trolley_views.pdf"
        csv_path = out_dir / "costing_sheet.csv"
        zip_blob = _build_zip([summary_path, cad_path, dxf_path, pdf_path, csv_path])

        st.session_state["frontend_result"] = {
            "summary": summary,
            "run_id": out_dir.name,
            "summary_path": str(summary_path),
            "cad_path": str(cad_path),
            "dxf_path": str(dxf_path),
            "pdf_path": str(pdf_path),
            "csv_path": str(csv_path),
            "zip_blob": zip_blob,
            "zip_name": f"{out_dir.name}_outputs.zip",
            "openscad_url": _openscad_playground_url(cad_path.read_text(encoding="utf-8")),
        }
        st.session_state["frontend_preview_kind"] = "summary"

        # Final state: all nodes done.
        status_placeholder.markdown(_pipeline_html(len(labels), labels), unsafe_allow_html=True)
        progress_placeholder.progress(1.0, text="Completed. Outputs are ready for download.")
        live_note.markdown("<p class='small-note'>Generation completed successfully.</p>", unsafe_allow_html=True)

    frontend_result = st.session_state.get("frontend_result")

    if frontend_result:
        summary = frontend_result["summary"]
        run_id = frontend_result["run_id"]
        summary_path = Path(frontend_result["summary_path"])
        cad_path = Path(frontend_result["cad_path"])
        dxf_path = Path(frontend_result["dxf_path"])
        pdf_path = Path(frontend_result["pdf_path"])
        csv_path = Path(frontend_result["csv_path"])

        with output_area:
            st.markdown("<div class='outputs-shell'>", unsafe_allow_html=True)
            st.success("Workflow completed successfully.")
            st.caption(f"Fresh run created: {run_id}")

            used_input = summary.get("input", {})
            st.caption(
                "Input used -> "
                f"Load: {used_input.get('load_capacity_kg')} kg | "
                f"LxW: {used_input.get('platform_length_mm')} x {used_input.get('platform_width_mm')} mm | "
                f"Material: {used_input.get('desired_material')} | "
                f"Wheels: {used_input.get('number_of_wheels')} | "
                f"Environment: {used_input.get('operating_environment')}"
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Cost (INR)", f"{summary['cost_estimation']['total_estimated_cost_inr']:,}")
            c2.metric("Total Loaded Mass (kg)", summary["engineering_calculations"]["total_loaded_mass_kg"])
            c3.metric("Manufacturing Hours", summary["manufacturing_timeline"]["total_hours"])

            st.markdown("<div class='downloads-title'>View Outputs</div>", unsafe_allow_html=True)
            st.markdown("<p class='outputs-note'>Choose any output below to view it directly in-app.</p>", unsafe_allow_html=True)
            d1, d2, d3, d4, d5, d6 = st.columns(6, gap="small")
            if d1.button("Summary", key=f"view_summary_{run_id}", use_container_width=True):
                st.session_state["frontend_preview_kind"] = "summary"
            if d2.button("CAD SCAD", key=f"view_scad_{run_id}", use_container_width=True):
                st.session_state["frontend_preview_kind"] = "scad"
            d3.link_button("CAD Web", frontend_result["openscad_url"], use_container_width=True)
            if d4.button("Drawing DXF", key=f"view_dxf_{run_id}", use_container_width=True):
                st.session_state["frontend_preview_kind"] = "dxf"
            if d5.button("Drawing PDF", key=f"view_pdf_{run_id}", use_container_width=True):
                st.session_state["frontend_preview_kind"] = "pdf"
            if d6.button("Costing CSV", key=f"view_csv_{run_id}", use_container_width=True):
                st.session_state["frontend_preview_kind"] = "csv"

            preview_kind = st.session_state.get("frontend_preview_kind", "summary")
            preview_title = {
                "summary": "Summary JSON",
                "scad": "CAD SCAD",
                "dxf": "Drawing DXF",
                "pdf": "Drawing PDF",
                "csv": "Costing CSV",
            }.get(preview_kind, "Summary JSON")

            st.markdown(f"<div class='downloads-title'>Preview: {preview_title}</div>", unsafe_allow_html=True)
            _render_preview(preview_kind, summary, summary_path, cad_path, dxf_path, pdf_path, csv_path)

            st.download_button(
                "Download Complete Output Bundle (.zip)",
                data=frontend_result["zip_blob"],
                file_name=frontend_result["zip_name"],
                mime="application/zip",
                use_container_width=True,
                on_click="ignore",
            )
            st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()

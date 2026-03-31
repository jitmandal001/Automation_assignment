from __future__ import annotations

from models import CalcResult, InputSpec


def estimate_manufacturing_timeline(spec: InputSpec, calc: CalcResult) -> dict:
    # Baseline estimates in hours.
    base_fabrication = 5.0
    base_assembly = 2.0

    load_factor = 1.0 + (spec.load_capacity_kg / 1000.0) * 0.4
    size_factor = 1.0 + ((spec.platform_length_mm * spec.platform_width_mm) / 1_000_000.0) * 0.2

    mass_factor = 1.0 + (calc.total_loaded_mass_kg / 1000.0) * 0.06
    wheels_factor = 1.0 if spec.number_of_wheels == 2 else 1.18
    axle_stations = 1 if spec.number_of_wheels == 2 else 2
    material_factor = 1.0 if spec.desired_material == "Mild Steel" else 1.12
    environment_factor = 1.0 if spec.operating_environment == "Indoor" else 1.08

    fabrication_hours = (
        base_fabrication * load_factor * size_factor * mass_factor * material_factor * environment_factor
        + 0.45 * axle_stations
    )
    assembly_hours = base_assembly * load_factor * wheels_factor * environment_factor + 0.35 * axle_stations

    return {
        "fabrication_hours": round(fabrication_hours, 2),
        "assembly_hours": round(assembly_hours, 2),
        "total_hours": round(fabrication_hours + assembly_hours, 2),
        "notes": [
            "Fabrication includes cutting, welding, and surface prep.",
            "Assembly includes wheel mounting and final checks.",
            "Timeline includes wheel-count, environment, material, and loaded-mass factors.",
        ],
    }

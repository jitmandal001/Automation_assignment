from __future__ import annotations

from dataclasses import asdict

from models import CalcResult, InputSpec


def build_bom(spec: InputSpec, calc: CalcResult) -> list[dict]:
    length_m = spec.platform_length_mm / 1000.0
    width_m = spec.platform_width_mm / 1000.0
    perimeter_m = 2 * (length_m + width_m)
    axle_count = 1 if spec.number_of_wheels == 2 else 2
    axle_length_m = round(max(width_m - 0.04, 0.1), 3)

    # Approximate split for frame members.
    bom = [
        {
            "item": "Square tube frame",
            "qty": round(perimeter_m + 2 * width_m, 2),
            "unit": "m",
            "spec": f"{calc.recommended_tube_mm} mm",
        },
        {
            "item": "Platform sheet",
            "qty": round(length_m * width_m, 3),
            "unit": "m2",
            "spec": f"{spec.desired_material} {calc.platform_thickness_mm} mm",
        },
        {
            "item": "Wheels",
            "qty": spec.number_of_wheels,
            "unit": "nos",
            "spec": "Industrial caster",
        },
        {
            "item": "Axle rod",
            "qty": axle_count,
            "unit": "nos",
            "spec": f"Solid round bar, 14 mm dia x {axle_length_m} m",
        },
        {
            "item": "Axle hanger brackets",
            "qty": axle_count * 2,
            "unit": "nos",
            "spec": "Welded hanger/clamp set (approx)",
        },
        {
            "item": "Fasteners set",
            "qty": 1,
            "unit": "set",
            "spec": "M10 bolts/nuts/washers (approx)",
        },
    ]
    return bom


def estimate_costs(spec: InputSpec, calc: CalcResult) -> dict:
    # INR assumptions documented for assessment.
    material_cost_per_kg = 75.0 if spec.desired_material == "Mild Steel" else 210.0

    base_wheel_cost_each = 900.0 if spec.operating_environment == "Indoor" else 1400.0
    if calc.load_per_wheel_n > 2500:
        wheel_rating_factor = 1.45
    elif calc.load_per_wheel_n > 1800:
        wheel_rating_factor = 1.25
    elif calc.load_per_wheel_n > 1200:
        wheel_rating_factor = 1.10
    else:
        wheel_rating_factor = 1.0

    wheel_cost_each = base_wheel_cost_each * wheel_rating_factor
    fastener_lump_sum = 650.0
    axle_count = 1 if spec.number_of_wheels == 2 else 2
    hanger_cost_each = 280.0

    structural_mass = calc.frame_mass_kg + calc.deck_mass_kg + calc.axle_set_mass_kg
    material_cost = structural_mass * material_cost_per_kg
    wheel_cost = spec.number_of_wheels * wheel_cost_each
    hanger_cost = axle_count * 2 * hanger_cost_each

    # Fabrication/assembly factors for better sensitivity.
    material_difficulty = 1.0 if spec.desired_material == "Mild Steel" else 1.15
    environment_factor = 1.0 if spec.operating_environment == "Indoor" else 1.08
    wheels_factor = 1.0 if spec.number_of_wheels == 2 else 1.18

    # Fabrication cost model: cutting + welding + finishing.
    fabrication_cost = ((0.26 * material_cost) + 2200.0 + axle_count * 250.0) * material_difficulty * environment_factor
    assembly_cost = ((0.08 * material_cost) + 900.0) * wheels_factor * environment_factor

    total = material_cost + wheel_cost + hanger_cost + fastener_lump_sum + fabrication_cost + assembly_cost

    return {
        "material_cost_inr": round(material_cost, 2),
        "wheel_cost_inr": round(wheel_cost, 2),
        "hanger_cost_inr": round(hanger_cost, 2),
        "fastener_cost_inr": round(fastener_lump_sum, 2),
        "fabrication_cost_inr": round(fabrication_cost, 2),
        "assembly_cost_inr": round(assembly_cost, 2),
        "total_estimated_cost_inr": round(total, 2),
    }


def export_costing_csv(path: str, spec: InputSpec, calc: CalcResult, costs: dict, bom: list[dict]) -> None:
    import csv

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Section", "Field", "Value"])

        writer.writerow(["Input", "load_capacity_kg", spec.load_capacity_kg])
        writer.writerow(["Input", "platform_length_mm", spec.platform_length_mm])
        writer.writerow(["Input", "platform_width_mm", spec.platform_width_mm])
        writer.writerow(["Input", "desired_material", spec.desired_material])
        writer.writerow(["Input", "number_of_wheels", spec.number_of_wheels])
        writer.writerow(["Input", "operating_environment", spec.operating_environment])

        for k, v in asdict(calc).items():
            writer.writerow(["Calculation", k, v])

        for k, v in costs.items():
            writer.writerow(["Cost", k, v])

        writer.writerow(["BOM", "item", "qty", "unit", "spec"])
        for row in bom:
            writer.writerow(["BOM", row["item"], row["qty"], row["unit"], row["spec"]])

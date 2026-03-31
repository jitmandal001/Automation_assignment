from __future__ import annotations

import math

from models import CalcResult, InputSpec


MATERIAL_DENSITY_KG_M3 = {
    "Mild Steel": 7850.0,
    "Stainless Steel": 8000.0,
}

MATERIAL_YIELD_STRENGTH_MPA = {
    "Mild Steel": 250.0,
    "Stainless Steel": 215.0,
}

AXLE_DENSITY_KG_M3 = 7850.0
AXLE_DIAMETER_M = 0.014
RAIL_WIDTH_M = 0.04


def _tube_selection(load_kg: float) -> str:
    if load_kg <= 300:
        return "40x40x2.5"
    if load_kg <= 700:
        return "50x50x3.0"
    return "60x60x4.0"


def _platform_thickness_mm(load_kg: float, material: str) -> float:
    base = 3.0 if material == "Mild Steel" else 2.5
    if load_kg > 800:
        return base + 2.0
    if load_kg > 500:
        return base + 1.0
    return base


def _frame_mass_estimate(length_m: float, width_m: float, density: float, tube: str) -> float:
    # Tube mass estimate for perimeter + two cross members.
    side, _, thick = tube.partition("x")
    side_mm = float(side)
    thickness_mm = float(tube.split("x")[-1])

    outer = side_mm / 1000.0
    inner = (side_mm - 2 * thickness_mm) / 1000.0
    area_m2 = max(outer * outer - inner * inner, 1e-6)

    total_tube_length_m = 2.0 * (length_m + width_m) + 2.0 * width_m
    return density * area_m2 * total_tube_length_m


def calculate(spec: InputSpec) -> CalcResult:
    spec.validate()

    length_m = spec.platform_length_mm / 1000.0
    width_m = spec.platform_width_mm / 1000.0

    density = MATERIAL_DENSITY_KG_M3[spec.desired_material]
    yield_strength = MATERIAL_YIELD_STRENGTH_MPA[spec.desired_material]
    safety_factor = 2.5

    tube = _tube_selection(spec.load_capacity_kg)
    thickness_mm = _platform_thickness_mm(spec.load_capacity_kg, spec.desired_material)

    frame_mass = _frame_mass_estimate(length_m, width_m, density, tube)
    deck_mass = length_m * width_m * (thickness_mm / 1000.0) * density

    axle_count = 1 if spec.number_of_wheels == 2 else 2
    axle_length_m = max(width_m - RAIL_WIDTH_M, 0.1)
    axle_area_m2 = math.pi * (AXLE_DIAMETER_M / 2.0) ** 2
    axle_set_mass = AXLE_DENSITY_KG_M3 * axle_area_m2 * axle_length_m * axle_count

    wheel_unit_mass = 4.5 if spec.operating_environment == "Indoor" else 6.5
    wheel_set_mass = wheel_unit_mass * spec.number_of_wheels

    payload = spec.load_capacity_kg
    total_loaded_mass = frame_mass + deck_mass + axle_set_mass + wheel_set_mass + payload

    load_per_wheel_n = (total_loaded_mass * 9.81) / spec.number_of_wheels

    rr_coeff = 0.015 if spec.operating_environment == "Indoor" else 0.03
    rolling_force = total_loaded_mass * 9.81 * rr_coeff

    h_frame = 300.0
    h_load = 650.0
    cg = ((frame_mass + deck_mass) * h_frame + payload * h_load) / max(total_loaded_mass, 1e-6)
    tipping_angle = math.degrees(math.atan((spec.platform_width_mm / 2.0) / max(cg, 1e-6)))

    allowable_stress = yield_strength / safety_factor

    return CalcResult(
        recommended_tube_mm=tube,
        platform_thickness_mm=round(thickness_mm, 2),
        frame_mass_kg=round(frame_mass, 2),
        deck_mass_kg=round(deck_mass, 2),
        axle_set_mass_kg=round(axle_set_mass, 2),
        wheel_set_mass_kg=round(wheel_set_mass, 2),
        payload_kg=round(payload, 2),
        total_loaded_mass_kg=round(total_loaded_mass, 2),
        load_per_wheel_n=round(load_per_wheel_n, 2),
        rolling_force_n=round(rolling_force, 2),
        cg_height_mm=round(cg, 2),
        tipping_angle_deg=round(tipping_angle, 2),
        yield_strength_mpa=yield_strength,
        safety_factor=safety_factor,
        estimated_allowable_stress_mpa=round(allowable_stress, 2),
    )

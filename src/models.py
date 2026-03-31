from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InputSpec:
    load_capacity_kg: float
    platform_length_mm: float
    platform_width_mm: float
    desired_material: str
    number_of_wheels: int
    operating_environment: str

    def validate(self) -> None:
        if self.load_capacity_kg <= 0:
            raise ValueError("load_capacity_kg must be > 0")
        if self.platform_length_mm < 400 or self.platform_width_mm < 300:
            raise ValueError("platform dimensions are too small for an industrial trolley")
        if self.desired_material not in {"Mild Steel", "Stainless Steel"}:
            raise ValueError("desired_material must be 'Mild Steel' or 'Stainless Steel'")
        if self.number_of_wheels not in {2, 4}:
            raise ValueError("number_of_wheels must be 2 or 4")
        if self.operating_environment not in {"Indoor", "Outdoor"}:
            raise ValueError("operating_environment must be 'Indoor' or 'Outdoor'")


@dataclass
class CalcResult:
    recommended_tube_mm: str
    platform_thickness_mm: float
    frame_mass_kg: float
    deck_mass_kg: float
    axle_set_mass_kg: float
    wheel_set_mass_kg: float
    payload_kg: float
    total_loaded_mass_kg: float
    load_per_wheel_n: float
    rolling_force_n: float
    cg_height_mm: float
    tipping_angle_deg: float
    yield_strength_mpa: float
    safety_factor: float
    estimated_allowable_stress_mpa: float

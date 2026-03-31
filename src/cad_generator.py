from __future__ import annotations

from pathlib import Path

from models import CalcResult, InputSpec


def generate_openscad_model(spec: InputSpec, calc: CalcResult, out_path: str) -> str:
    """Generate a parametric OpenSCAD model script.

    This keeps CAD generation automated even if FreeCAD is not yet installed.
    """
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    l = spec.platform_length_mm
    w = spec.platform_width_mm
    h = 180
    plate_t = calc.platform_thickness_mm
    wheel_d = 125 if spec.operating_environment == "Indoor" else 160
    wheel_w = 40
    two_wheel_axle_x = l / 4

    # Compute pull-rod placement in Python to avoid OpenSCAD block-scope assignment surprises.
    pull_rod_len = l * (2.0 / 3.0)
    pull_anchor_x = 0.0
    pull_dir = -1.0
    if spec.number_of_wheels == 2:
      pull_rod_len = l * (2.0 / 3.0)
      if two_wheel_axle_x <= l / 2:
        pull_anchor_x = l
        pull_dir = 1.0

    scad = f"""
$fn = 64;

length = {l};
width = {w};
frame_h = {h};
plate_t = {plate_t};
wheel_d = {wheel_d};
wheel_w = {wheel_w};

rail = 40;
post = 30;

// Raise frame above wheel center so wheel mounts are physically meaningful.
base_z = wheel_d + 20;
top_frame_z = base_z + frame_h - rail;
deck_z = base_z + frame_h;

module bottom_frame() {{
  // Perimeter rails
  translate([0, 0, base_z]) cube([length, rail, rail]);
  translate([0, width - rail, base_z]) cube([length, rail, rail]);
  translate([0, 0, base_z]) cube([rail, width, rail]);
  translate([length - rail, 0, base_z]) cube([rail, width, rail]);

  // Bottom cross members
  translate([length/3, rail, base_z]) cube([rail, width - 2*rail, rail]);
  translate([2*length/3, rail, base_z]) cube([rail, width - 2*rail, rail]);
}}

module support_posts() {{
  post_z = top_frame_z - (base_z + rail);

  // Corner posts
  translate([rail, rail, base_z + rail]) cube([post, post, post_z]);
  translate([length - rail - post, rail, base_z + rail]) cube([post, post, post_z]);
  translate([rail, width - rail - post, base_z + rail]) cube([post, post, post_z]);
  translate([length - rail - post, width - rail - post, base_z + rail]) cube([post, post, post_z]);

  // Mid posts for top deck support
  translate([length/3, width/2 - post/2, base_z + rail]) cube([post, post, post_z]);
  translate([2*length/3, width/2 - post/2, base_z + rail]) cube([post, post, post_z]);
}}

module top_frame() {{
  // Secondary frame directly below top plate.
  translate([0, 0, top_frame_z]) cube([length, rail, rail]);
  translate([0, width - rail, top_frame_z]) cube([length, rail, rail]);
  translate([0, 0, top_frame_z]) cube([rail, width, rail]);
  translate([length - rail, 0, top_frame_z]) cube([rail, width, rail]);

  // Top cross members
  translate([length/3, rail, top_frame_z]) cube([rail, width - 2*rail, rail]);
  translate([2*length/3, rail, top_frame_z]) cube([rail, width - 2*rail, rail]);
}}

module deck_plate() {{
  translate([0, 0, deck_z]) cube([length, width, plate_t]);
}}

module pull_rod(anchor_x, pull_rod_len, pull_dir) {{
  // Drawbar centered on trolley width; anchor and direction are configured by wheel layout.
  pull_rod_d = 22;
  bearing_id = pull_rod_d + 2;
  bearing_od = 44;
  bearing_w = 20;
  lock_od = 34;
  lock_w = 6;
  lock_gap = 1;
  grip_w = 160;
  anchor_y = width/2;
  anchor_z = base_z + rail/2;
  handle_x = anchor_x + pull_dir * pull_rod_len;
  rod_x = min(anchor_x, handle_x);
  housing_w = 14;
  housing_x = anchor_x - housing_w/2;
  housing_y = anchor_y - 24;
  housing_z = anchor_z - 24;

  // Main pull rod from anchor point to handle end.
  translate([rod_x, anchor_y, anchor_z])
    rotate([0, 90, 0])
      cylinder(h=abs(pull_rod_len), d=pull_rod_d);

  // Grip bar at pull end.
  translate([handle_x, anchor_y, anchor_z])
    rotate([90, 0, 0])
      cylinder(h=grip_w, d=pull_rod_d * 0.65, center=true);

  // Bearing ring at rod-to-frame joint (kept proud of housing so it is visible).
  translate([anchor_x, anchor_y, anchor_z])
    rotate([0, 90, 0])
      difference() {{
        cylinder(h=bearing_w, d=bearing_od, center=true);
        cylinder(h=bearing_w + 2, d=bearing_id, center=true);
      }}

  // Lock collars on both sides of bearing.
  for (x_off = [-(bearing_w/2 + lock_gap + lock_w/2), (bearing_w/2 + lock_gap + lock_w/2)]) {{
    translate([anchor_x + x_off, anchor_y, anchor_z])
      rotate([0, 90, 0])
        difference() {{
          cylinder(h=lock_w, d=lock_od, center=true);
          cylinder(h=lock_w + 2, d=bearing_id, center=true);
        }}
  }}

  // Bearing housing block connected to frame with bearing seat hole.
  difference() {{
    translate([housing_x, housing_y, housing_z])
      cube([housing_w, 48, 48]);
    translate([anchor_x, anchor_y, anchor_z])
      rotate([0, 90, 0])
        cylinder(h=housing_w + 2, d=bearing_od - 2, center=true);
  }}
}}

module wheel_disc(x, y) {{
  axle_z = wheel_d/2;

  // Wheel body
  translate([x, y, axle_z])
    rotate([90, 0, 0])
      cylinder(h=wheel_w, d=wheel_d, center=true);
}}

module axle_station(x_pos) {{
  axle_z = wheel_d/2;
  axle_d = 14;
  axle_span = width - rail;
  // Support rods are placed at L/6 from each wheel end along the axle span.
  support_inset = axle_span/6;
  support_y_a = rail_center_left + support_inset;
  support_y_b = rail_center_right - support_inset;
  hanger_w = 24;
  hanger_d = 30;
  clamp_w = 30;
  clamp_d = 34;
  clamp_h = 16;

  // Cross axle rod passing through both wheel centers.
  translate([x_pos, width/2, axle_z])
    rotate([90, 0, 0])
      cylinder(h=axle_span, d=axle_d, center=true);

  // Left and right wheels on same axle.
  wheel_disc(x_pos, rail_center_left);
  wheel_disc(x_pos, rail_center_right);

  // Wheel hubs clamp to axle at wheel locations.
  for (y_wheel = [rail_center_left, rail_center_right]) {{
    translate([x_pos, y_wheel, axle_z])
      rotate([90, 0, 0])
        cylinder(h=wheel_w + 6, d=20, center=true);
  }}

  // Frame hangers connect to axle via clamp blocks (industrial style).
  for (y_support = [support_y_a, support_y_b]) {{
    // Clamp block around axle at support locations.
    translate([x_pos - clamp_w/2, y_support - clamp_d/2, axle_z - clamp_h/2])
      cube([clamp_w, clamp_d, clamp_h]);

    // Vertical hanger from frame underside to axle clamp top.
    translate([x_pos - hanger_w/2, y_support - hanger_d/2, axle_z + clamp_h/2])
      cube([hanger_w, hanger_d, base_z - (axle_z + clamp_h/2)]);
  }}
}}

wheel_offset_x = 90;
rail_center_left = rail/2;
rail_center_right = width - rail/2;
two_wheel_axle_x = length/4;
pull_rod_len = {pull_rod_len};
pull_anchor_x = {pull_anchor_x};
pull_dir = {pull_dir};

bottom_frame();
support_posts();
top_frame();
deck_plate();
pull_rod(pull_anchor_x, pull_rod_len, pull_dir);

if ({spec.number_of_wheels} == 4) {{
  axle_station(wheel_offset_x);
  axle_station(length - wheel_offset_x);
}} else {{
  // Two-wheel trolley: both wheels share one axle located at L/4 from front.
  axle_station(two_wheel_axle_x);
}}
""".strip()

    path.write_text(scad, encoding="utf-8")
    return str(path)

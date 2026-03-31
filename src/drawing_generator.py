from __future__ import annotations

from pathlib import Path

from models import CalcResult, InputSpec


def _write_simple_dxf(spec: InputSpec, calc: CalcResult, out_file: Path) -> None:
    """Write an ASCII DXF containing top and side views with wheels and supports."""
    l = spec.platform_length_mm
    w = spec.platform_width_mm
    frame_h = 180
    rail = 40
    post = 30
    plate_t = calc.platform_thickness_mm
    wheel_d = 125 if spec.operating_environment == "Indoor" else 160

    # Keep drawing constants aligned with the OpenSCAD generator.
    base_z = wheel_d + 20
    top_frame_z = base_z + frame_h - rail
    deck_z = base_z + frame_h
    wheel_offset_x = 90
    two_wheel_axle_x = l / 4
    hanger_w = 24
    clamp_h = 16
    rail_center_left = rail / 2
    rail_center_right = w - rail / 2
    axle_span = w - rail
    support_inset = axle_span / 6
    support_y_a = rail_center_left + support_inset
    support_y_b = rail_center_right - support_inset
    pull_rod_len = l * (2.0 / 3.0)
    pull_anchor_x = 0.0
    pull_dir = -1.0
    if spec.number_of_wheels == 2:
        pull_rod_len = l * (2.0 / 3.0)
        if two_wheel_axle_x <= l / 2:
            pull_anchor_x = l
            pull_dir = 1.0
    pull_handle_x = pull_anchor_x + pull_dir * pull_rod_len
    pull_grip_w = 160.0
    pull_anchor_z = base_z + rail / 2
    bearing_w = 32.0
    bearing_h = 48.0
    bearing_side_h = 44.0
    rod_pair_dx = 14
    side_hanger_w = 10

    if spec.number_of_wheels == 4:
        axle_xs = [wheel_offset_x, l - wheel_offset_x]
    else:
        axle_xs = [two_wheel_axle_x]

    # Two views: top view at origin, side view shifted below.
    top = [(0, 0), (l, 0), (l, w), (0, w), (0, 0)]
    y_shift = -(w + 650)

    bottom_frame = [
        (0, y_shift + base_z),
        (l, y_shift + base_z),
        (l, y_shift + base_z + rail),
        (0, y_shift + base_z + rail),
        (0, y_shift + base_z),
    ]
    top_frame = [
        (0, y_shift + top_frame_z),
        (l, y_shift + top_frame_z),
        (l, y_shift + top_frame_z + rail),
        (0, y_shift + top_frame_z + rail),
        (0, y_shift + top_frame_z),
    ]
    deck = [
        (0, y_shift + deck_z),
        (l, y_shift + deck_z),
        (l, y_shift + deck_z + plate_t),
        (0, y_shift + deck_z + plate_t),
        (0, y_shift + deck_z),
    ]

    post_bottom = y_shift + base_z + rail
    post_height = top_frame_z - (base_z + rail)

    post_xs = [
        rail,
        l - rail - post,
        l / 3,
        2 * l / 3,
    ]

    def polyline(points: list[tuple[float, float]]) -> str:
        out = ""
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            out += (
                "0\nLINE\n8\n0\n"
                f"10\n{x1}\n20\n{y1}\n30\n0.0\n"
                f"11\n{x2}\n21\n{y2}\n31\n0.0\n"
            )
        return out

    def circle(cx: float, cy: float, r: float) -> str:
        return (
            "0\nCIRCLE\n8\n0\n"
            f"10\n{cx}\n20\n{cy}\n30\n0.0\n"
            f"40\n{r}\n"
        )

    content = "0\nSECTION\n2\nENTITIES\n"
    content += polyline(top)

    # Top-view pull rod and grip.
    content += polyline([(pull_anchor_x, w / 2), (pull_handle_x, w / 2)])
    content += polyline([(pull_handle_x, w / 2 - pull_grip_w / 2), (pull_handle_x, w / 2 + pull_grip_w / 2)])
    bearing_top = [
        (pull_anchor_x - bearing_w / 2, w / 2 - bearing_h / 2),
        (pull_anchor_x + bearing_w / 2, w / 2 - bearing_h / 2),
        (pull_anchor_x + bearing_w / 2, w / 2 + bearing_h / 2),
        (pull_anchor_x - bearing_w / 2, w / 2 + bearing_h / 2),
        (pull_anchor_x - bearing_w / 2, w / 2 - bearing_h / 2),
    ]
    content += polyline(bearing_top)

    # Top-view axle lines and support-rod footprints.
    for x_axle in axle_xs:
        content += polyline([(x_axle, rail_center_left), (x_axle, rail_center_right)])

        for y_support in [support_y_a, support_y_b]:
            top_support = [
                (x_axle - 9, y_support - 13),
                (x_axle + 9, y_support - 13),
                (x_axle + 9, y_support + 13),
                (x_axle - 9, y_support + 13),
                (x_axle - 9, y_support - 13),
            ]
            content += polyline(top_support)

    content += polyline(bottom_frame)
    content += polyline(top_frame)
    content += polyline(deck)

    # Side-view pull rod profile.
    content += polyline([(pull_anchor_x, y_shift + pull_anchor_z), (pull_handle_x, y_shift + pull_anchor_z)])
    bearing_side = [
        (pull_anchor_x - bearing_w / 2, y_shift + pull_anchor_z - bearing_side_h / 2),
        (pull_anchor_x + bearing_w / 2, y_shift + pull_anchor_z - bearing_side_h / 2),
        (pull_anchor_x + bearing_w / 2, y_shift + pull_anchor_z + bearing_side_h / 2),
        (pull_anchor_x - bearing_w / 2, y_shift + pull_anchor_z + bearing_side_h / 2),
        (pull_anchor_x - bearing_w / 2, y_shift + pull_anchor_z - bearing_side_h / 2),
    ]
    content += polyline(bearing_side)

    # Side view support posts.
    for x in post_xs:
        post_rect = [
            (x, post_bottom),
            (x + post, post_bottom),
            (x + post, post_bottom + post_height),
            (x, post_bottom + post_height),
            (x, post_bottom),
        ]
        content += polyline(post_rect)

    # Side view wheels and supports.
    wheel_center_y = y_shift + wheel_d / 2

    # Side view hangers and clamps at axle stations (drawn as twin supports).
    for x_axle in axle_xs:
        for x_support in [x_axle - rod_pair_dx / 2, x_axle + rod_pair_dx / 2]:
            clamp_rect = [
                (x_support - side_hanger_w / 2, y_shift + wheel_d / 2 - clamp_h / 2),
                (x_support + side_hanger_w / 2, y_shift + wheel_d / 2 - clamp_h / 2),
                (x_support + side_hanger_w / 2, y_shift + wheel_d / 2 + clamp_h / 2),
                (x_support - side_hanger_w / 2, y_shift + wheel_d / 2 + clamp_h / 2),
                (x_support - side_hanger_w / 2, y_shift + wheel_d / 2 - clamp_h / 2),
            ]
            hanger_rect = [
                (x_support - side_hanger_w / 2, y_shift + wheel_d / 2 + clamp_h / 2),
                (x_support + side_hanger_w / 2, y_shift + wheel_d / 2 + clamp_h / 2),
                (x_support + side_hanger_w / 2, y_shift + base_z),
                (x_support - side_hanger_w / 2, y_shift + base_z),
                (x_support - side_hanger_w / 2, y_shift + wheel_d / 2 + clamp_h / 2),
            ]
            content += polyline(clamp_rect)
            content += polyline(hanger_rect)

    if spec.number_of_wheels == 4:
        content += circle(wheel_offset_x, wheel_center_y, wheel_d / 2)
        content += circle(l - wheel_offset_x, wheel_center_y, wheel_d / 2)
    else:
        # Two-wheel trolley shows one wheel profile in side projection at L/4.
        content += circle(two_wheel_axle_x, wheel_center_y, wheel_d / 2)

    content += "0\nENDSEC\n0\nEOF\n"

    out_file.write_text(content, encoding="utf-8")


def _write_simple_pdf(spec: InputSpec, calc: CalcResult, out_file: Path) -> None:
    """Generate a lightweight PDF report-like drawing sheet.

    Uses matplotlib if available, otherwise writes a text fallback next to PDF path.
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle, Rectangle
    except Exception:
        fallback = out_file.with_suffix(".txt")
        fallback.write_text(
            "PDF generation skipped (matplotlib not installed).\n"
            "Top and side view dimensions:\n"
            f"Top: {spec.platform_length_mm} x {spec.platform_width_mm} mm\n"
            "Side height: 180 mm\n"
            f"Tube: {calc.recommended_tube_mm} mm\n",
            encoding="utf-8",
        )
        return

    frame_h = 180
    rail = 40
    post = 30
    wheel_d = 125 if spec.operating_environment == "Indoor" else 160
    base_z = wheel_d + 20
    top_frame_z = base_z + frame_h - rail
    deck_z = base_z + frame_h
    wheel_offset_x = 90
    two_wheel_axle_x = spec.platform_length_mm / 4
    hanger_w = 24
    clamp_h = 16
    rail_center_left = rail / 2
    rail_center_right = spec.platform_width_mm - rail / 2
    axle_span = spec.platform_width_mm - rail
    support_inset = axle_span / 6
    support_y_a = rail_center_left + support_inset
    support_y_b = rail_center_right - support_inset
    pull_rod_len = spec.platform_length_mm * (2.0 / 3.0)
    pull_anchor_x = 0.0
    pull_dir = -1.0
    if spec.number_of_wheels == 2:
        pull_rod_len = spec.platform_length_mm * (2.0 / 3.0)
        if two_wheel_axle_x <= spec.platform_length_mm / 2:
            pull_anchor_x = spec.platform_length_mm
            pull_dir = 1.0
    pull_handle_x = pull_anchor_x + pull_dir * pull_rod_len
    pull_grip_w = 160.0
    pull_anchor_z = base_z + rail / 2
    bearing_w = 32.0
    bearing_h = 48.0
    bearing_side_h = 44.0
    rod_pair_dx = 14
    side_hanger_w = 10

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    # Top view
    ax = axes[0]
    ax.add_patch(Rectangle((0, 0), spec.platform_length_mm, spec.platform_width_mm, fill=False, linewidth=2))
    ax.plot([pull_anchor_x, pull_handle_x], [spec.platform_width_mm / 2, spec.platform_width_mm / 2], linewidth=1.8)
    ax.plot(
        [pull_handle_x, pull_handle_x],
        [spec.platform_width_mm / 2 - pull_grip_w / 2, spec.platform_width_mm / 2 + pull_grip_w / 2],
        linewidth=1.8,
    )
    ax.add_patch(
        Rectangle(
            (pull_anchor_x - bearing_w / 2, spec.platform_width_mm / 2 - bearing_h / 2),
            bearing_w,
            bearing_h,
            fill=False,
            linewidth=1.6,
        )
    )

    if spec.number_of_wheels == 4:
        axle_xs = [wheel_offset_x, spec.platform_length_mm - wheel_offset_x]
    else:
        axle_xs = [two_wheel_axle_x]

    for x_axle in axle_xs:
        ax.plot([x_axle, x_axle], [rail_center_left, rail_center_right], linewidth=1.8)
        for y_support in [support_y_a, support_y_b]:
            ax.add_patch(Rectangle((x_axle - 9, y_support - 13), 18, 26, fill=False, linewidth=1.3))

    ax.set_title("Top View")
    ax.set_xlabel("Length (mm)")
    ax.set_ylabel("Width (mm)")
    x_min = min(0.0, pull_handle_x) - 100
    x_max = max(spec.platform_length_mm, pull_handle_x) + 100
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(-100, spec.platform_width_mm + 100)
    ax.set_aspect("equal", adjustable="box")

    # Side view with wheels and frame supports.
    ax2 = axes[1]
    ax2.add_patch(Rectangle((0, base_z), spec.platform_length_mm, rail, fill=False, linewidth=2))
    ax2.add_patch(Rectangle((0, top_frame_z), spec.platform_length_mm, rail, fill=False, linewidth=2))
    ax2.add_patch(Rectangle((0, deck_z), spec.platform_length_mm, calc.platform_thickness_mm, fill=False, linewidth=2))
    ax2.plot([pull_anchor_x, pull_handle_x], [pull_anchor_z, pull_anchor_z], linewidth=1.8)
    ax2.add_patch(
        Rectangle(
            (pull_anchor_x - bearing_w / 2, pull_anchor_z - bearing_side_h / 2),
            bearing_w,
            bearing_side_h,
            fill=False,
            linewidth=1.6,
        )
    )

    post_bottom = base_z + rail
    post_height = top_frame_z - (base_z + rail)
    post_xs = [rail, spec.platform_length_mm - rail - post, spec.platform_length_mm / 3, 2 * spec.platform_length_mm / 3]
    for x in post_xs:
        ax2.add_patch(Rectangle((x, post_bottom), post, post_height, fill=False, linewidth=1.5))

    wheel_centers = axle_xs

    for cx in wheel_centers:
        for x_support in [cx - rod_pair_dx / 2, cx + rod_pair_dx / 2]:
            ax2.add_patch(
                Rectangle(
                    (x_support - side_hanger_w / 2, wheel_d / 2 - clamp_h / 2),
                    side_hanger_w,
                    clamp_h,
                    fill=False,
                    linewidth=1.5,
                )
            )
            ax2.add_patch(
                Rectangle(
                    (x_support - side_hanger_w / 2, wheel_d / 2 + clamp_h / 2),
                    side_hanger_w,
                    base_z - (wheel_d / 2 + clamp_h / 2),
                    fill=False,
                    linewidth=1.5,
                )
            )

    for cx in wheel_centers:
        ax2.add_patch(Circle((cx, wheel_d / 2), wheel_d / 2, fill=False, linewidth=2))

    ax2.set_title("Side View")
    ax2.set_xlabel("Length (mm)")
    ax2.set_ylabel("Height (mm)")
    ax2.set_xlim(x_min, x_max)
    ax2.set_ylim(-20, deck_z + calc.platform_thickness_mm + 80)
    ax2.set_aspect("equal", adjustable="box")

    fig.suptitle(
        f"Trolley Drawing | Tube {calc.recommended_tube_mm} | Plate {calc.platform_thickness_mm} mm",
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(out_file, format="pdf")
    plt.close(fig)


def generate_drawings(spec: InputSpec, calc: CalcResult, output_dir: str) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    dxf_path = out / "trolley_views.dxf"
    pdf_path = out / "trolley_views.pdf"

    _write_simple_dxf(spec, calc, dxf_path)
    _write_simple_pdf(spec, calc, pdf_path)

    return {
        "dxf": str(dxf_path),
        "pdf": str(pdf_path),
    }

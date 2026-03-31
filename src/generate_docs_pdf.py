from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def md_like_to_pdf(input_md: Path, output_pdf: Path) -> None:
    text = input_md.read_text(encoding="utf-8")
    lines = text.splitlines()

    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    h1_style = styles["Heading1"]
    h2_style = styles["Heading2"]
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        leading=16,
        spaceAfter=6,
    )

    story = []
    for raw in lines:
        line = raw.rstrip()
        if not line:
            story.append(Spacer(1, 6))
            continue

        esc = (
            line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        if esc.startswith("# "):
            story.append(Paragraph(esc[2:].strip(), title_style))
            story.append(Spacer(1, 8))
        elif esc.startswith("## "):
            story.append(Paragraph(esc[3:].strip(), h1_style))
            story.append(Spacer(1, 4))
        elif esc.startswith("### "):
            story.append(Paragraph(esc[4:].strip(), h2_style))
            story.append(Spacer(1, 2))
        elif esc.startswith("- "):
            story.append(Paragraph(f"• {esc[2:].strip()}", body_style))
        elif esc[0].isdigit() and ". " in esc[:4]:
            story.append(Paragraph(esc, body_style))
        else:
            story.append(Paragraph(esc, body_style))

    doc.build(story)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert markdown-like text file to PDF")
    parser.add_argument("--input", default="docs/submission_documentation.md", help="Input markdown file path")
    parser.add_argument("--output", default="docs/submission_documentation.pdf", help="Output PDF file path")
    args = parser.parse_args()

    md_path = Path(args.input)
    pdf_path = Path(args.output)
    md_like_to_pdf(md_path, pdf_path)
    print(f"Generated: {pdf_path}")


if __name__ == "__main__":
    main()

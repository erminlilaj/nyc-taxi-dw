"""Create the submission-ready PDF report from the implemented project facts."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output" / "pdf" / "nyc_taxi_dw_final_report.pdf"


def paragraph(text, style):
    return Paragraph(text, style)


def image(path, max_width, max_height):
    asset = Image(str(path))
    scale = min(max_width / asset.imageWidth, max_height / asset.imageHeight)
    asset.drawWidth = asset.imageWidth * scale
    asset.drawHeight = asset.imageHeight * scale
    asset.hAlign = "CENTER"
    return asset


def section_title(text, style):
    return [Spacer(1, 0.2 * cm), Paragraph(text, style), Spacer(1, 0.12 * cm)]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(doc.leftMargin, 1.35 * cm, A4[0] - doc.rightMargin, 1.35 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#526172"))
    canvas.drawString(doc.leftMargin, 0.9 * cm, "NYC Taxi Data Warehouse and Graph Analysis")
    canvas.drawRightString(A4[0] - doc.rightMargin, 0.9 * cm, f"Page {doc.page}")
    canvas.restoreState()


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=32,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#172033"),
        spaceAfter=12,
    )
    subtitle = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["BodyText"],
        fontSize=13,
        leading=19,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#526172"),
    )
    h1 = ParagraphStyle(
        "Section",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=21,
        textColor=colors.HexColor("#172033"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#243145"),
        spaceAfter=8,
    )
    caption = ParagraphStyle(
        "Caption",
        parent=body,
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#526172"),
        spaceBefore=4,
        spaceAfter=8,
    )

    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        topMargin=1.55 * cm,
        bottomMargin=1.75 * cm,
        title="NYC Taxi Data Warehouse and Graph Analysis",
        author="DM2526 Project Team",
    )

    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172033")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEADING", (0, 0), (-1, -1), 12),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )

    story = []
    story.extend([Spacer(1, 3.8 * cm), Paragraph("NYC Taxi<br/>Data Warehouse", title)])
    story.append(Paragraph("PostgreSQL OLAP and Neo4j Graph Analysis", subtitle))
    story.append(Spacer(1, 1.2 * cm))
    story.append(
        Table(
            [
                ["Course", "DM2526 - Data Management 2025/2026"],
                ["Dataset", "NYC TLC Yellow Taxi Trip Records"],
                ["Period", "January-March 2024"],
                ["Stack", "PostgreSQL 16, Python, Neo4j 5"],
            ],
            colWidths=[4.2 * cm, 11.3 * cm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#D9F5EF")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9FB3C8")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            ),
        )
    )
    story.append(Spacer(1, 1.25 * cm))
    story.append(
        paragraph(
            "PostgreSQL is the authoritative dimensional warehouse. Neo4j is a "
            "derived aggregate layer used to inspect taxi corridors, pickup hubs, "
            "payment preferences, vendor trends, and peak-demand hours.",
            subtitle,
        )
    )
    story.append(PageBreak())

    story += section_title("1. Objective and Dataset", h1)
    story.append(
        paragraph(
            "The objective is to support analytical questions about demand, revenue, "
            "payment behaviour, trip duration, and geographic movement. The source "
            "dataset contains Yellow Taxi trip records published by NYC TLC.",
            body,
        )
    )
    story.append(
        Table(
            [["Stage", "Trip records"], ["Raw TLC records", "9,554,778"], ["Cleaned and loaded facts", "8,448,046"], ["Removed by validation", "1,106,732"]],
            colWidths=[9 * cm, 6.5 * cm],
            style=table_style,
        )
    )
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        paragraph(
            "Rows with missing timestamps or locations, out-of-period pickups, "
            "invalid fares or distances, invalid passenger counts, and implausible "
            "durations are removed. Missing tip amounts are retained as zero. The "
            "pipeline preserves 88.4% of the original records.",
            body,
        )
    )

    story += section_title("2. Warehouse Design", h1)
    story.append(
        paragraph(
            "The fact-table grain is one cleaned taxi trip. The measures are fare, "
            "tip, total amount, trip distance, passenger count, and trip duration. "
            "The dimensions implement the proposed time, pickup, dropoff, payment, "
            "and service hierarchies.",
            body,
        )
    )
    story.append(image(ROOT / "diagrams" / "dfm.png", 16.5 * cm, 10.5 * cm))
    story.append(paragraph("Figure 1. Logical Dimensional Fact Model.", caption))
    story.append(image(ROOT / "diagrams" / "er.png", 16.5 * cm, 10.8 * cm))
    story.append(paragraph("Figure 2. Physical PostgreSQL star schema.", caption))
    story.append(PageBreak())

    story += section_title("3. ETL and OLAP", h1)
    story.append(
        paragraph(
            "The ETL pipeline downloads source files, cleans the records, and loads "
            "the five dimensions before bulk-loading fact rows in 100,000-row batches. "
            "The loaded warehouse contains 2,183 time rows, 265 pickup zones, 265 "
            "dropoff zones, six payment types, two services, and 8,448,046 facts.",
            body,
        )
    )
    story.append(
        paragraph(
            "Twelve reproducible SQL queries implement roll-up, drill-down, slice, "
            "dice, ranking, and window analyses. They examine revenue by time, demand "
            "by geography and hour, duration, payment preferences, tipping, and vendor "
            "performance.",
            body,
        )
    )
    story += section_title("4. Neo4j Graph Layer", h1)
    story.append(
        paragraph(
            "Neo4j receives aggregates exported from PostgreSQL rather than individual "
            "trip nodes. The loaded graph contains 565 nodes and 39,590 relationships, "
            "including 33,304 directed TRIPS_TO relationships. This makes route structure "
            "and hub behaviour easy to inspect while retaining a reproducible source in "
            "the warehouse.",
            body,
        )
    )
    story.append(image(ROOT / "docs" / "figures" / "neo4j_jfk_manhattan.png", 16.5 * cm, 12 * cm))
    story.append(paragraph("Figure 3. Top JFK Airport to Manhattan corridors from Neo4j G1.", caption))
    story.append(PageBreak())

    story += section_title("5. Results and Interpretation", h1)
    results = [
        ["Finding", "Evidence"],
        ["Busiest corridor", "Upper East Side South to Upper East Side North: 61,421 trips and $958,770.89 revenue."],
        ["Largest pickup hub", "Midtown Center: 417,379 trips. JFK Airport: 400,263 trips and $32.88 million revenue."],
        ["Payment behaviour", "Credit card is the preferred payment type at the busiest pickup zones."],
        ["Vendor trend", "Both vendors record their highest revenue in March; VeriFone leads all three months."],
        ["Peak demand", "Midtown Center peaks at 18:00 with 38,697 trips."],
    ]
    story.append(Table(results, colWidths=[4.5 * cm, 11 * cm], style=table_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        paragraph(
            "The star schema provides complete, auditable dimensional results. The graph "
            "layer adds an intuitive view of directional movement and network-like hub "
            "patterns. Together they satisfy the data-warehouse objective and make the "
            "analysis easy to demonstrate.",
            body,
        )
    )
    story += section_title("6. Reproducibility", h1)
    story.append(
        paragraph(
            "Run the warehouse ETL, execute sql/olap_queries.sql, then run "
            "etl/export_neo4j_graph.py followed by neo4j/load_graph.cypher. The README "
            "contains the exact commands, while docs/validation.md and "
            "docs/graph_analysis.md record verified counts and query results.",
            body,
        )
    )
    story += section_title("7. Conclusion", h1)
    story.append(
        paragraph(
            "The project implements the proposed warehouse workflow end to end: source "
            "data acquisition, cleaning, dimensional loading, OLAP analysis, data-model "
            "documentation, and visual relationship exploration. Neo4j extends the "
            "PostgreSQL warehouse without replacing it, giving the final submission both "
            "dimensional and graph perspectives on NYC taxi travel.",
            body,
        )
    )

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()

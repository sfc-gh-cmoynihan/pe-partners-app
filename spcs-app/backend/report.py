import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
)

from backend.db import query

POSITIVE = "#16a34a"
NEGATIVE = "#dc2626"
ACCENT = "#1d4ed8"


def get_report_data(fund_id):
    funds = query("SELECT * FROM FUNDS_IT ORDER BY TOTAL_AUM_GBP DESC")
    performance = query("""
        SELECT fp.*, f.FUND_NAME
        FROM FUND_PERFORMANCE_IT fp
        JOIN FUNDS_IT f ON fp.FUND_ID = f.FUND_ID
        ORDER BY fp.REPORTING_DATE DESC
    """)
    investments = query("SELECT * FROM INVESTMENTS_IT ORDER BY MARKET_VALUE_GBP DESC")
    customers = query("SELECT * FROM CUSTOMERS_IT")

    total_commitments = sum(c.get("AUM_COMMITMENT_GBP") or 0 for c in customers)

    if fund_id:
        fund_id = int(fund_id)
        fund = next((f for f in funds if f["FUND_ID"] == fund_id), None)
        fund_performance = [p for p in performance if p["FUND_ID"] == fund_id]
        fund_positions = [i for i in investments if i["FUND_ID"] == fund_id]
        scope_funds = [fund] if fund else []
    else:
        fund = None
        fund_performance = performance
        fund_positions = investments
        scope_funds = funds

    latest_by_fund = {}
    for p in performance:
        fid = p["FUND_ID"]
        if fid not in latest_by_fund or p["REPORTING_DATE"] > latest_by_fund[fid]["REPORTING_DATE"]:
            latest_by_fund[fid] = p

    return {
        "fund": fund,
        "funds": funds,
        "scope_funds": scope_funds,
        "performance": fund_performance,
        "positions": fund_positions[:15],
        "latest_by_fund": latest_by_fund,
        "total_commitments": total_commitments,
        "investor_count": len(customers),
    }


def _bar_colors(values):
    return [POSITIVE if v is not None and v >= 0 else NEGATIVE for v in values]


def build_returns_chart(data):
    fig, ax = plt.subplots(figsize=(6.2, 2.6), dpi=150)
    if data["fund"]:
        rows = sorted(data["performance"], key=lambda r: r["REPORTING_DATE"])[-12:]
        labels = [r["REPORTING_DATE"].strftime("%b-%y") for r in rows]
        values = [float(r["MONTHLY_RETURN_PCT"] or 0) for r in rows]
        title = f"Monthly Returns — {data['fund']['FUND_NAME']}"
    else:
        rows = sorted(data["latest_by_fund"].values(), key=lambda r: r["FUND_NAME"])
        labels = [r["FUND_NAME"] for r in rows]
        values = [float(r["YTD_RETURN_PCT"] or 0) for r in rows]
        title = "YTD Returns by Fund"

    ax.bar(labels, values, color=_bar_colors(values))
    ax.set_title(title, fontsize=10, color="#0f172a")
    ax.axhline(0, color="#94a3b8", linewidth=0.6)
    ax.tick_params(axis="x", labelrotation=35, labelsize=7)
    ax.tick_params(axis="y", labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf


def build_roic_chart(data):
    fig, ax = plt.subplots(figsize=(6.2, 2.6), dpi=150)
    rows = sorted(data["latest_by_fund"].values(), key=lambda r: r["FUND_NAME"])
    labels = [r["FUND_NAME"] for r in rows]
    values = [float(r["YTD_RETURN_PCT"] or 0) for r in rows]
    colors_ = []
    for r, v in zip(rows, values):
        if data["fund"] and r["FUND_ID"] == data["fund"]["FUND_ID"]:
            colors_.append(ACCENT)
        else:
            colors_.append(POSITIVE if v >= 0 else NEGATIVE)

    ax.bar(labels, values, color=colors_)
    ax.set_title("ROIC (YTD Return) by Fund", fontsize=10, color="#0f172a")
    ax.axhline(0, color="#94a3b8", linewidth=0.6)
    ax.tick_params(axis="x", labelrotation=35, labelsize=7)
    ax.tick_params(axis="y", labelsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf


def _gbp(v):
    if v is None:
        return "-"
    v = float(v)
    if abs(v) >= 1e9:
        return f"GBP {v / 1e9:.2f}bn"
    if abs(v) >= 1e6:
        return f"GBP {v / 1e6:.1f}m"
    if abs(v) >= 1e3:
        return f"GBP {v / 1e3:.0f}k"
    return f"GBP {v:.0f}"


def _pct(v):
    return "-" if v is None else f"{float(v):.2f}%"


def _cell(text, style):
    return Paragraph(str(text) if text is not None else "-", style)


def generate_pdf(fund_id):
    data = get_report_data(fund_id)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=18, textColor=colors.HexColor("#0f172a"))
    h2_style = ParagraphStyle("h2", parent=styles["Heading2"], textColor=colors.HexColor("#1d4ed8"), spaceBefore=14)
    body_style = ParagraphStyle("body", parent=styles["BodyText"], textColor=colors.HexColor("#334155"), fontSize=9)
    footer_style = ParagraphStyle("footer", parent=styles["BodyText"], textColor=colors.HexColor("#94a3b8"), fontSize=7)
    cell_style = ParagraphStyle("cell", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#334155"))
    cell_style_sm = ParagraphStyle("cell_sm", parent=styles["BodyText"], fontSize=7.5, leading=9, textColor=colors.HexColor("#334155"))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm, bottomMargin=16 * mm, leftMargin=18 * mm, rightMargin=18 * mm)
    elements = []

    scope_name = data["fund"]["FUND_NAME"] if data["fund"] else "All Funds"
    elements.append(Paragraph("PE Partners &mdash; LP Report", title_style))
    elements.append(Paragraph(f"{scope_name} &nbsp;&bull;&nbsp; Generated {datetime.now().strftime('%d %b %Y %H:%M')}", body_style))
    elements.append(Spacer(1, 10))

    # Fund overview section
    elements.append(Paragraph("Fund Overview", h2_style))
    overview_rows = [["Fund", "Strategy", "AUM", "Mgmt Fee", "Perf Fee", "Min Investment"]]
    for f in data["scope_funds"]:
        overview_rows.append([
            _cell(f["FUND_NAME"], cell_style), _cell(f["STRATEGY"], cell_style), _gbp(f["TOTAL_AUM_GBP"]),
            _pct(f["MANAGEMENT_FEE_PCT"]), _pct(f["PERFORMANCE_FEE_PCT"]), _gbp(f["MINIMUM_INVESTMENT_GBP"]),
        ])
    overview_table = Table(overview_rows, hAlign="LEFT", colWidths=[95, 95, 65, 55, 55, 80])
    overview_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#64748b")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 14))

    # Charts
    elements.append(Paragraph("Returns", h2_style))
    elements.append(Image(build_returns_chart(data), width=480, height=200))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("ROIC", h2_style))
    elements.append(Image(build_roic_chart(data), width=480, height=200))
    elements.append(Paragraph(
        "ROIC is presented as YTD return based on available fund performance data "
        "(the data model does not track capital calls/distributions).", footer_style))
    elements.append(Spacer(1, 10))

    # Performance table
    elements.append(Paragraph("Performance History", h2_style))
    perf_rows = [["Fund", "Date", "Monthly", "YTD", "Sharpe", "Max DD", "Vol"]]
    for p in sorted(data["performance"], key=lambda r: r["REPORTING_DATE"], reverse=True)[:20]:
        perf_rows.append([
            _cell(p["FUND_NAME"], cell_style_sm), p["REPORTING_DATE"].strftime("%Y-%m-%d"), _pct(p["MONTHLY_RETURN_PCT"]),
            _pct(p["YTD_RETURN_PCT"]), f"{float(p['SHARPE_RATIO'] or 0):.2f}", _pct(p["MAX_DRAWDOWN_PCT"]), _pct(p["VOLATILITY_PCT"]),
        ])
    perf_table = Table(perf_rows, hAlign="LEFT", colWidths=[95, 60, 50, 50, 45, 55, 50])
    perf_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#64748b")),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(perf_table)
    elements.append(Spacer(1, 14))

    # Positions table
    elements.append(Paragraph("Portfolio Positions", h2_style))
    pos_rows = [["Security", "Ticker", "Sector", "Type", "Market Value", "Weight"]]
    for i in data["positions"]:
        pos_rows.append([
            _cell(i["SECURITY_NAME"], cell_style_sm), i["TICKER"], _cell(i["SECTOR"], cell_style_sm), i["POSITION_TYPE"],
            _gbp(i["MARKET_VALUE_GBP"]), _pct(i["WEIGHT_PCT"]),
        ])
    pos_table = Table(pos_rows, hAlign="LEFT", colWidths=[120, 50, 90, 45, 75, 45])
    pos_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#64748b")),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(pos_table)
    elements.append(Spacer(1, 14))

    # Investor summary
    elements.append(Paragraph("Investor Base (Firm-Wide)", h2_style))
    elements.append(Paragraph(
        f"Total investor commitments across the firm: {_gbp(data['total_commitments'])} "
        f"across {data['investor_count']} investors. Investor commitments are not attributed "
        f"to individual funds in the current data model.", body_style))
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Confidential &mdash; for the intended recipient only.", footer_style))

    doc.build(elements)
    buf.seek(0)
    return buf.read()

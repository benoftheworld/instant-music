"""
PDF generation service for game results.
Uses ReportLab to produce a single-page (or multi-page) results PDF.
"""

import io
from typing import List, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

# ─── PDF colour palette (centralized) ───────────────────────────────
COLOR_PRIMARY = colors.HexColor("#6366f1")
COLOR_BORDER = colors.HexColor("#d1d5db")
COLOR_ROW_ALT = colors.HexColor("#f9fafb")
COLOR_HEADER_LIGHT = colors.HexColor("#e0e7ff")
COLOR_HR = colors.HexColor("#e5e7eb")
COLOR_CORRECT = "#10b981"


def _medal(rank: int) -> str:
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}.")


def generate_results_pdf(
    game_data: Dict[str, Any],
    rankings: List[Dict[str, Any]],
    rounds: List[Dict[str, Any]],
) -> bytes:
    """Return a PDF (bytes) containing the full game results."""
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=15 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        title="InstantMusic — Résultats",
        author="InstantMusic",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title2",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=6,
        textColor=COLOR_PRIMARY,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle2",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.grey,
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        "Section2",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=14,
        spaceAfter=6,
        textColor=COLOR_PRIMARY,
    )

    elements: list = []

    # ── Header ──────────────────────────────────────────────────────
    elements.append(
        Paragraph("InstantMusic — Résultats de la partie", title_style)
    )
    room_code = game_data.get("room_code", "?")
    mode_display = game_data.get("mode_display", game_data.get("mode", "?"))
    answer_mode_display = game_data.get("answer_mode_display", "")
    guess_target_display = game_data.get("guess_target_display", "")
    num_rounds = game_data.get("num_rounds", "?")
    
    config_parts = [f"Mode : <b>{mode_display}</b>"]
    if answer_mode_display:
        config_parts.append(f"Type : <b>{answer_mode_display}</b>")
    if guess_target_display and game_data.get("mode") in ["classique", "rapide"]:
        config_parts.append(f"Cible : <b>{guess_target_display}</b>")
    config_parts.append(f"Rounds : <b>{num_rounds}</b>")
    
    elements.append(
        Paragraph(
            f"Partie <b>{room_code}</b> &nbsp;|&nbsp; " + " &nbsp;|&nbsp; ".join(config_parts),
            subtitle_style,
        )
    )
    elements.append(
        HRFlowable(width="100%", thickness=1, color=COLOR_HR)
    )
    elements.append(Spacer(1, 6))

    # ── Classement ──────────────────────────────────────────────────
    elements.append(Paragraph("Classement", section_style))

    ranking_data = [["#", "Joueur", "Score"]]
    for p in rankings:
        rank = p.get("rank", "—")
        username = p.get("username", "?")
        score = p.get("score", 0)
        ranking_data.append(
            [
                _medal(rank) if isinstance(rank, int) else str(rank),
                username,
                str(score),
            ]
        )

    rank_table = Table(ranking_data, colWidths=[30, 300, 80])
    rank_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, COLOR_ROW_ALT],
                ),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(rank_table)
    elements.append(Spacer(1, 10))

    # ── Détail par round ────────────────────────────────────────────
    elements.append(Paragraph("Détail par round", section_style))

    for rd in rounds:
        rnum = rd.get("round_number", "?")
        track = rd.get("track_name", "?")
        artist = rd.get("artist_name", "?")
        correct = rd.get("correct_answer", "?")

        elements.append(
            Paragraph(
                f"<b>Round {rnum}</b> — {track} ({artist}) &nbsp; "
                f"<font color='{COLOR_CORRECT}'>Réponse : {correct}</font>",
                styles["Normal"],
            )
        )

        answers = rd.get("answers", [])
        if answers:
            ans_data = [["Joueur", "Réponse", "Pts", "Temps"]]
            for a in answers:
                icon = "✓" if a.get("is_correct") else "✗"
                ans_data.append(
                    [
                        a.get("username", "?"),
                        f"{icon} {a.get('answer', '')}",
                        str(a.get("points_earned", 0)),
                        f"{a.get('response_time', 0)}s",
                    ]
                )

            ans_table = Table(ans_data, colWidths=[120, 200, 40, 50])
            ans_table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            COLOR_HEADER_LIGHT,
                        ),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.4,
                            COLOR_BORDER,
                        ),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            elements.append(ans_table)
        else:
            elements.append(
                Paragraph("<i>Aucune réponse</i>", styles["Normal"])
            )

        elements.append(Spacer(1, 6))

    # ── Footer ──────────────────────────────────────────────────────
    elements.append(
        HRFlowable(
            width="100%", thickness=0.5, color=COLOR_BORDER
        )
    )
    elements.append(Spacer(1, 4))
    elements.append(
        Paragraph(
            "Généré par InstantMusic • instantmusic.app",
            ParagraphStyle(
                "footer",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.grey,
            ),
        )
    )

    doc.build(elements)
    return buf.getvalue()

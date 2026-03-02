"""
PDF generation service for game results.
Uses ReportLab to produce a single-page (or multi-page) results PDF.
"""

import io
from typing import List, Dict, Any
from datetime import datetime

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

from .services import (
    SCORE_BASE_POINTS,
    SCORE_TIME_PENALTY_PER_SEC,
    SCORE_MIN_CORRECT,
    SCORE_MIN_FINAL,
    RANK_BONUS,
)

# ─── PDF colour palette (centralized) — adapted to project charte ───
# Provided brand colours mapped from CSS RGB values
# Main background: rgb(249,239,231) → #F9EFE7
# Navigation background (dark): rgb(34,34,34) → #222222
# Borders: rgb(220,56,66) → #DC3842
COLOR_BG_MAIN = colors.HexColor("#F9EFE7")
COLOR_NAV_BG = colors.HexColor("#222222")
COLOR_BORDER = colors.HexColor("#DC3842")
# Row alternate background uses main background
COLOR_ROW_ALT = COLOR_BG_MAIN
# Header light (subtle) — keep a pale tint for table headers
COLOR_HEADER_LIGHT = colors.HexColor("#FFF3EE")
# Horizontal rule
COLOR_HR = colors.HexColor("#EDE0DB")
# Correct answer highlight (keep green)
COLOR_CORRECT = "#10b981"
# Primary accent used for headings and top-bars: use navigation background
COLOR_PRIMARY = COLOR_NAV_BG
MEDAL_COLORS = {
    1: colors.HexColor("#D4AF37"),
    2: colors.HexColor("#C0C0C0"),
    3: colors.HexColor("#CD7F32"),
}


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
    game_name = game_data.get("name")
    mode_display = game_data.get("mode_display", game_data.get("mode", "?"))
    answer_mode_display = game_data.get("answer_mode_display", "")
    guess_target_display = game_data.get("guess_target_display", "")
    num_rounds = game_data.get("num_rounds", "?")
    
    config_parts = [f"Mode : <b>{mode_display}</b>"]
    # Add optional fields (name, date)
    if game_name:
        config_parts.insert(0, f"Partie : <b>{game_name}</b>")
    # date/time (try finished_at, then started_at)
    date_val = game_data.get("finished_at") or game_data.get("started_at")
    if date_val:
        if isinstance(date_val, str):
            try:
                dt = datetime.fromisoformat(date_val)
            except Exception:
                dt = None
        elif isinstance(date_val, datetime):
            dt = date_val
        else:
            dt = None

        if dt:
            date_display = dt.strftime("%d/%m/%Y %H:%M")
            config_parts.append(f"Date : <b>{date_display}</b>")
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

    # Ranking with teams and medal colours
    ranking_data = [["#", "Pseudonyme", "Équipe", "Points"]]
    for p in rankings:
        rank = p.get("rank", "—")
        username = p.get("username", "?")
        team = p.get("team_name") or "—"
        score = p.get("score", 0)
        ranking_data.append([
            _medal(rank) if isinstance(rank, int) else str(rank),
            username,
            team,
            str(score),
        ])

    rank_table = Table(ranking_data, colWidths=[40, 200, 140, 70])
    # Base styles
    table_style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_ROW_ALT]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
    ]

    # Medal row backgrounds for top3
    for idx, p in enumerate(rankings, start=1):
        r = idx  # table row index (header is row 0)
        rank = p.get("rank")
        if isinstance(rank, int) and rank in MEDAL_COLORS:
            color = MEDAL_COLORS[rank]
            table_style_cmds.append(("BACKGROUND", (0, r), (-1, r), color))
            # ensure readable text on medal rows
            table_style_cmds.append(("TEXTCOLOR", (0, r), (-1, r), colors.black))

    rank_table.setStyle(TableStyle(table_style_cmds))
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
                f"<b>Round {rnum}</b> — {track} ({artist}) &nbsp; ",
                styles["Normal"],
            )
        )

        answers = rd.get("answers", [])
        if answers:
            # small adaptive paragraph style for long answers
            ans_style_small = ParagraphStyle(
                "ans_small",
                parent=styles["Normal"],
                fontSize=8,
            )

            # Add a little vertical space between the round header and its table
            elements.append(Spacer(1, 4))

            # Determine fastest response_time for this round
            try:
                min_time = min(float(a.get("response_time", 9999)) for a in answers)
            except Exception:
                min_time = None

            ans_data = [["Joueur", "Réponse", "Pts", "Temps", "Série"]]
            fastest_rows: list[int] = []
            for i, a in enumerate(answers):
                icon = "✓" if a.get("is_correct") else "✗"
                answer_text = f"{icon} {a.get('answer', '')}"
                # choose style based on length to avoid overflow
                cell_answer = (
                    Paragraph(answer_text, ans_style_small)
                    if len(answer_text) > 60
                    else Paragraph(answer_text, styles["Normal"]) 
                )
                streak_len = a.get("consecutive_correct")
                streak_bonus = a.get("streak_bonus", 0)
                streak_text = (
                    f"×{streak_len} +{streak_bonus} pts" if streak_len and streak_len > 1 else "-"
                )

                is_fastest = (min_time is not None and float(a.get("response_time", 9999)) == min_time)
                if is_fastest:
                    fastest_rows.append(i + 1)  # +1 because header occupies row 0

                username_cell = Paragraph(f"{a.get('username', '?')}", styles["Normal"]) if not is_fastest else Paragraph(f"⚡ <b>{a.get('username', '?')}</b>", styles["Normal"])

                ans_data.append([
                    username_cell,
                    cell_answer,
                    str(a.get("points_earned", 0)),
                    f"{a.get('response_time', 0)}s",
                    streak_text,
                ])

            # slightly adjusted widths to accommodate new column and wrapping
            ans_table = Table(ans_data, colWidths=[100, 220, 40, 40, 60])

            # Base style
            base_cmds = [
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_LIGHT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (2, 0), (-2, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]

            # Highlight fastest rows
            for r in fastest_rows:
                base_cmds.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#FFF7ED")))
                base_cmds.append(("TEXTCOLOR", (0, r), (-1, r), colors.HexColor("#B45309")))
                base_cmds.append(("FONTNAME", (0, r), (0, r), "Helvetica-Bold"))

            ans_table.setStyle(TableStyle(base_cmds))
            elements.append(ans_table)
        else:
            elements.append(
                Paragraph("<i>Aucune réponse</i>", styles["Normal"])
            )

        elements.append(Spacer(1, 6))

    # ── Calcul des points ─────────────────────────────────
    elements.append(Paragraph("Calcul des points", section_style))
    # Use scoring constants to show formula and a numeric example

    elements.append(Paragraph(
        "Le score de chaque réponse est calculé en fonction du temps de réponse et de la précision (exactitude) de la réponse. "
        "Un bonus de rang est ajouté pour les meilleurs joueurs. De plus, une série de réponses correctes peut générer des "
        "points bonus supplémentaires.<br/><br/>",
        styles["Normal"]
    ))

    formula = (
        f"points_base = max({SCORE_MIN_CORRECT}, {SCORE_BASE_POINTS} - (response_time * {SCORE_TIME_PENALTY_PER_SEC}))<br/>"
        f"points_finaux = max({SCORE_MIN_FINAL}, (points_base * accuracy_factor)) + bonus_rang + bonus_série"
    )
    # Example values
    example_resp_time = 7
    example_accuracy = 1.0
    raw = max(SCORE_MIN_CORRECT, SCORE_BASE_POINTS - int(example_resp_time * SCORE_TIME_PENALTY_PER_SEC))
    final = max(SCORE_MIN_FINAL, int(raw * example_accuracy))
    # top-first bonus example
    first_bonus = RANK_BONUS.get(0, 0)
    final_with_bonus = final + first_bonus
    win_streak = 3

    example_text = (
        f"Voici un exemple de calcul pour une réponse donnée :<br/><br/>"
        f"<i>{formula}</i><br/><br/>"
        f"Supposons une réponse avec un temps de <b>{example_resp_time}s</b> et une précision de <b>{example_accuracy * 100:.0f}%</b>.<br/>"
        f"Le score de base serait : <b>{raw} pts</b> (calculé comme max({SCORE_MIN_CORRECT}, {SCORE_BASE_POINTS} - ({example_resp_time} * {SCORE_TIME_PENALTY_PER_SEC})))<br/>"
        f"Le score final serait : <b>{final} pts</b> (calculé comme max({SCORE_MIN_FINAL}, {raw} * {example_accuracy}))<br/>"
        f"Si ce joueur est le plus rapide, il recevrait un bonus de rang de <b>{first_bonus} pts</b>, portant son total à <b>{final_with_bonus} pts</b>.<br/>"
        f"De plus, s'il a une série de <b>{win_streak} réponses correctes</b>, il pourrait recevoir un bonus de série supplémentaire, augmentant encore son score final."
    )
    elements.append(Paragraph(example_text, styles["Normal"]))

    # ── Footer ──────────────────────────────────────────────────────
    elements.append(
        HRFlowable(
            width="100%", thickness=0.5, color=COLOR_BORDER
        )
    )
    elements.append(Spacer(1, 4))
    elements.append(
        Paragraph(
            "Généré par InstantMusic — © 2024",
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

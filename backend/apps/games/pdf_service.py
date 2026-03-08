"""PDF generation service for game results.
Uses ReportLab to produce a polished multi-page results document.

Layout:
  • Every page: dark header band (brand) + slim footer with page number
  • Section 1 – Info card (metadata on two columns)
  • Section 2 – Podium (top-3 visual boxes)
  • Section 3 – Full ranking (alpha-sorted, top-scorer highlighted in gold)
  • Section 4 – Round-by-round detail (one card per round, sorted by score)
  • Section 5 – Score system (compact)
"""

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .services import (
    RANK_BONUS,
    SCORE_BASE_POINTS,
    SCORE_MIN_CORRECT,
    SCORE_TIME_PENALTY_PER_SEC,
)

# ── Libellés courts des bonus boutique (police standard, sans emoji) ─────────
_BONUS_LABELS: dict[str, str] = {
    "double_points": "Points x2",
    "max_points": "Points max",
    "time_bonus": "+15 s",
    "fifty_fifty": "50/50",
    "steal": "Vol de pts",
    "shield": "Bouclier",
    "fog": "Brouillard",
    "joker": "Joker",
}

# ── Palette ──────────────────────────────────────────────────────────────────
C_DARK = colors.HexColor("#222222")  # brand dark  — header band
C_ACCENT = colors.HexColor("#DC3842")  # brand red   — accent bars
C_GOLD = colors.HexColor("#D4AF37")  # gold        — 1st / top scorer
C_SILVER = colors.HexColor("#A8A9AD")  # silver      — 2nd
C_BRONZE = colors.HexColor("#CD7F32")  # bronze      — 3rd
C_WHITE = colors.white
C_LIGHT_BG = colors.HexColor("#F9EFE7")  # brand cream — section bg
C_ROW_ALT = colors.HexColor("#FDFBF9")  # alternating row
C_CORRECT = colors.HexColor("#D1FAE5")  # soft green  — correct answer
C_WRONG = colors.HexColor("#FEE2E2")  # soft red    — wrong answer
C_FASTEST = colors.HexColor("#FEF3C7")  # amber       — fastest player
C_RULE = colors.HexColor("#EDE3DA")  # brand cream rule
C_GREY_TEXT = colors.HexColor("#6B7280")
C_DARK_TEXT = colors.HexColor("#111827")

PAGE_W, PAGE_H = A4
MARGIN = 14 * mm
HEADER_H = 18 * mm
FOOTER_H = 10 * mm

MEDAL_LABEL = {1: "1er", 2: "2e", 3: "3e"}


# ── Canvas callbacks ─────────────────────────────────────────────────────────


def _draw_page(canvas, doc, room_code: str, game_name: str) -> None:
    """Header band + footer rule drawn on every page."""
    canvas.saveState()

    # ── Header band ──
    canvas.setFillColor(C_DARK)
    canvas.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)
    # Left accent stripe
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, PAGE_H - HEADER_H, 4, HEADER_H, fill=1, stroke=0)
    # "InstantMusic" label
    canvas.setFont("Helvetica-Bold", 13)
    canvas.setFillColor(C_WHITE)
    canvas.drawString(MARGIN, PAGE_H - HEADER_H + 6.5 * mm, "InstantMusic")
    # Sub-label (game name or room code)
    label = game_name if game_name else f"Partie {room_code}"
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(colors.HexColor("#F9EFE7"))
    canvas.drawString(MARGIN, PAGE_H - HEADER_H + 2.8 * mm, label)
    # Right: "Résultats de partie"
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.setFillColor(C_WHITE)
    canvas.drawRightString(
        PAGE_W - MARGIN, PAGE_H - HEADER_H + 5 * mm, "Résultats de partie"
    )

    # ── Footer ──
    canvas.setStrokeColor(C_RULE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, FOOTER_H - 1 * mm, PAGE_W - MARGIN, FOOTER_H - 1 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_GREY_TEXT)
    canvas.drawString(MARGIN, FOOTER_H - 4 * mm, "Généré par InstantMusic")
    canvas.drawCentredString(PAGE_W / 2, FOOTER_H - 4 * mm, f"Page {doc.page}")
    canvas.drawRightString(PAGE_W - MARGIN, FOOTER_H - 4 * mm, f"Salle {room_code}")

    canvas.restoreState()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _sty_factory(base_styles):
    """Return a quick ParagraphStyle builder."""

    def _make(name, **kw):
        return ParagraphStyle(name, parent=base_styles["Normal"], **kw)

    return _make


def _section_header(text: str, sec_sty) -> Table:
    """Full-width section title bar."""
    t = Table(
        [[Paragraph(f"<b>{text}</b>", sec_sty)]],
        colWidths=[PAGE_W - 2 * MARGIN],
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT_BG),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, -1), 2, C_ACCENT),
            ]
        )
    )
    return t


def _medal(rank: int) -> str:
    return MEDAL_LABEL.get(rank, f"{rank}.")


# ── Main generator ────────────────────────────────────────────────────────────


def generate_results_pdf(
    game_data: dict[str, Any],
    rankings: list[dict[str, Any]],
    rounds: list[dict[str, Any]],
) -> bytes:
    """Return a polished PDF (bytes) containing the full game results."""
    room_code = game_data.get("room_code", "?")
    game_name = game_data.get("name") or ""
    mode_display = game_data.get("mode_display", game_data.get("mode", "?"))
    answer_mode = game_data.get("answer_mode_display", "")
    guess_target = game_data.get("guess_target_display", "")
    num_rounds = game_data.get("num_rounds", "?")
    game_mode = game_data.get("mode", "")

    date_display = ""
    date_val = game_data.get("finished_at") or game_data.get("started_at")
    if date_val:
        try:
            dt = (
                datetime.fromisoformat(date_val)
                if isinstance(date_val, str)
                else date_val
            )
            date_display = dt.strftime("%d/%m/%Y à %H:%M")
        except Exception:
            pass

    # ── Document setup ──────────────────────────────────────────────────────
    buf = io.BytesIO()
    COL_W = PAGE_W - 2 * MARGIN

    content_y0 = FOOTER_H + 4 * mm
    content_top = PAGE_H - HEADER_H - 5 * mm
    frame = Frame(
        MARGIN,
        content_y0,
        COL_W,
        content_top - content_y0,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )

    def on_page(c, d):
        _draw_page(c, d, room_code, game_name)

    template = PageTemplate(id="main", frames=[frame], onPage=on_page)
    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        pageTemplates=[template],
        title="InstantMusic — Résultats",
        author="InstantMusic",
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=HEADER_H + 5 * mm,
        bottomMargin=FOOTER_H + 4 * mm,
    )

    # ── Styles ──────────────────────────────────────────────────────────────
    base = getSampleStyleSheet()
    _s = _sty_factory(base)

    S = {
        "sec": _s("sec", fontSize=11, textColor=C_DARK, fontName="Helvetica-Bold"),
        "title": _s(
            "title",
            fontSize=20,
            textColor=C_DARK,
            fontName="Helvetica-Bold",
            spaceAfter=2,
        ),
        "sub": _s("sub", fontSize=10, textColor=C_GREY_TEXT, spaceAfter=8),
        "body": _s("body", fontSize=9, textColor=C_DARK_TEXT),
        "body_sm": _s("bsm", fontSize=8, textColor=C_DARK_TEXT),
        "bold": _s(
            "bold",
            fontSize=9,
            textColor=C_DARK_TEXT,
            fontName="Helvetica-Bold",
        ),
        "bold_sm": _s(
            "boldsm",
            fontSize=8,
            textColor=C_DARK_TEXT,
            fontName="Helvetica-Bold",
        ),
        "grey": _s("grey", fontSize=8, textColor=C_GREY_TEXT),
        "ok": _s("ok", fontSize=8, textColor=colors.HexColor("#065F46")),
        "ko": _s("ko", fontSize=8, textColor=colors.HexColor("#991B1B")),
        "white": _s("wh", fontSize=9, textColor=C_WHITE),
        "white_sm": _s("whsm", fontSize=8, textColor=C_WHITE),
        "lilac": _s("lilac", fontSize=8, textColor=colors.HexColor("#F9EFE7")),
        "green_sm": _s("grsm", fontSize=8, textColor=colors.HexColor("#DC3842")),
        "center": _s("ctr", fontSize=9, textColor=C_DARK_TEXT, alignment=1),
        "center_w": _s(
            "ctrw",
            fontSize=9,
            textColor=C_WHITE,
            alignment=1,
            fontName="Helvetica-Bold",
        ),
        "center_g": _s("ctrg", fontSize=8, textColor=C_GREY_TEXT, alignment=1),
    }

    elements: list = []

    # ════════════════════════════════════════════════════════════════════════
    # 1 — TITRE + FICHE INFO
    # ════════════════════════════════════════════════════════════════════════
    title_label = game_name if game_name else f"Partie {room_code}<br/><br/>"
    elements.append(Paragraph(title_label, S["title"]))
    sub_parts = [f"Salle <b>{room_code}</b>"]
    if date_display:
        sub_parts.append(date_display)
    elements.append(Paragraph("  ·  ".join(sub_parts), S["sub"]))

    # Info grid (2 columns)
    meta_pairs: list[tuple[str, str]] = [
        ("Mode", mode_display),
        ("Rounds", str(num_rounds)),
    ]
    if answer_mode:
        meta_pairs.append(("Réponses", answer_mode))
    if guess_target and game_mode in ("classique", "rapide"):
        meta_pairs.append(("Cible", guess_target))
    meta_pairs.append(("Joueurs", str(len(rankings))))
    if date_display:
        meta_pairs.append(("Date", date_display))

    meta_rows = []
    for i in range(0, len(meta_pairs), 2):
        row: list = []
        for k, v in meta_pairs[i : i + 2]:
            row.append(Paragraph(f"<font color='#6B7280'>{k}</font>", S["body_sm"]))
            row.append(Paragraph(f"<b>{v}</b>", S["bold_sm"]))
        while len(row) < 4:
            row.append("")
        meta_rows.append(row)

    if meta_rows:
        mt = Table(
            meta_rows,
            colWidths=[COL_W * 0.16, COL_W * 0.34, COL_W * 0.16, COL_W * 0.34],
        )
        mt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT_BG),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, -1), (-1, -1), 1.5, C_ACCENT),
                ]
            )
        )
        elements.append(mt)

    elements.append(Spacer(1, 10))

    # ════════════════════════════════════════════════════════════════════════
    # 2 — PODIUM
    # ════════════════════════════════════════════════════════════════════════
    top3_by_rank = {p.get("rank"): p for p in rankings if p.get("rank", 99) <= 3}

    if top3_by_rank:
        elements.append(_section_header("Podium", S["sec"]))
        elements.append(Spacer(1, 6))

        podium_order = [2, 1, 3]
        podium_colors = [C_SILVER, C_GOLD, C_BRONZE]
        bar_heights = [20, 30, 16]  # mm
        cells = []

        for col_idx, rank in enumerate(podium_order):
            player = top3_by_rank.get(rank)
            col_color = podium_colors[col_idx]
            if not player:
                cells.append("")
                continue
            uname = player.get("username", "?")
            score = player.get("score", 0)

            slot = Table(
                [
                    [
                        Paragraph(
                            f"<b>{_medal(rank)}</b>",
                            _s(
                                f"pm_r{rank}",
                                fontSize=11,
                                fontName="Helvetica-Bold",
                                textColor=col_color,
                                alignment=1,
                            ),
                        )
                    ],
                    [
                        Paragraph(
                            f"<b>{uname}</b>",
                            _s(
                                f"pm_u{rank}",
                                fontSize=9,
                                fontName="Helvetica-Bold",
                                textColor=C_DARK_TEXT,
                                alignment=1,
                            ),
                        )
                    ],
                    [
                        Paragraph(
                            f"{score} pts",
                            _s(
                                f"pm_s{rank}",
                                fontSize=10,
                                fontName="Helvetica-Bold",
                                textColor=C_WHITE,
                                alignment=1,
                            ),
                        )
                    ],
                ],
                colWidths=[COL_W / 3 - 4],
                rowHeights=[14, 13, bar_heights[col_idx] * mm / 25.4 * 72],
            )
            slot.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (0, 1),
                            colors.HexColor("#FDFBF9"),
                        ),
                        ("BACKGROUND", (0, 2), (0, 2), col_color),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LINEABOVE", (0, 0), (0, 0), 3, col_color),
                        ("BOX", (0, 0), (-1, -1), 0.5, C_RULE),
                    ]
                )
            )
            cells.append(slot)

        pt = Table([cells], colWidths=[COL_W / 3] * 3)
        pt.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(pt)
        elements.append(Spacer(1, 10))

    # ════════════════════════════════════════════════════════════════════════
    # 3 — CLASSEMENT COMPLET (trié par score desc, podium 1/2/3 coloré)
    # ════════════════════════════════════════════════════════════════════════
    if rankings:
        elements.append(_section_header("Classement complet", S["sec"]))
        elements.append(Spacer(1, 4))

        # Sort by score descending, then username alphabetically as tiebreaker
        sorted_list = sorted(
            rankings,
            key=lambda p: (-p.get("score", 0), p.get("username", "").lower()),
        )

        # Per-rank display config: (bg_color, border_color, medal_text_color)
        RANK_STYLE = {
            1: (colors.HexColor("#FEF9C3"), C_GOLD, C_GOLD),
            2: (colors.HexColor("#F1F5F9"), C_SILVER, C_SILVER),
            3: (colors.HexColor("#FFF7ED"), C_BRONZE, C_BRONZE),
        }

        rk_header = [
            Paragraph("<b>Rang</b>", S["white_sm"]),
            Paragraph("<b>Joueur</b>", S["white_sm"]),
            Paragraph("<b>Points</b>", S["white_sm"]),
            Paragraph("<b>Équipe</b>", S["white_sm"]),
        ]
        rk_rows: list = [rk_header]
        podium_rows: dict[int, int] = {}  # row_index → rank (1/2/3)

        for i, p in enumerate(sorted_list, start=1):
            rank = p.get("rank", "—")
            uname = p.get("username", "?")
            score = p.get("score", 0)
            team = p.get("team_name") or "—"

            rank_int = rank if isinstance(rank, int) else None
            in_podium = rank_int in RANK_STYLE
            _, _, medal_color = RANK_STYLE.get(rank_int, (None, None, C_GREY_TEXT))  # type: ignore[arg-type]

            medal_sty = _s(
                f"rk_medal_{i}",
                fontSize=9,
                fontName="Helvetica-Bold" if in_podium else "Helvetica",
                textColor=medal_color,
            )
            txt_sty = S["bold"] if in_podium else S["body"]
            grey_sty = S["bold"] if in_podium else S["grey"]

            rk_rows.append(
                [
                    Paragraph(_medal(rank_int) if rank_int else str(rank), medal_sty),
                    Paragraph(uname, txt_sty),
                    Paragraph(f"{score} pts", txt_sty),
                    Paragraph(team, grey_sty),
                ]
            )
            if in_podium:
                podium_rows[i] = rank_int  # type: ignore[assignment]

        rk_table = Table(
            rk_rows,
            colWidths=[COL_W * 0.12, COL_W * 0.40, COL_W * 0.24, COL_W * 0.24],
        )
        rk_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), C_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_ROW_ALT]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.35, C_RULE),
        ]
        for row_idx, rank_val in podium_rows.items():
            bg, border, _ = RANK_STYLE[rank_val]
            rk_cmds += [
                ("BACKGROUND", (0, row_idx), (-1, row_idx), bg),
                ("LINEABOVE", (0, row_idx), (-1, row_idx), 1.5, border),
                ("LINEBELOW", (0, row_idx), (-1, row_idx), 1.5, border),
            ]
        rk_table.setStyle(TableStyle(rk_cmds))
        elements.append(rk_table)
        elements.append(Spacer(1, 3))
        elements.append(Spacer(1, 12))

    # ════════════════════════════════════════════════════════════════════════
    # 4 — DÉTAIL PAR ROUND
    # ════════════════════════════════════════════════════════════════════════
    if rounds:
        elements.append(_section_header("Détail par manche", S["sec"]))
        elements.append(Spacer(1, 6))

        RW = [COL_W * w for w in (0.06, 0.25, 0.37, 0.14, 0.10, 0.08)]

        for rd in rounds:
            rnum = rd.get("round_number", "?")
            track = rd.get("track_name", "?")
            artist = rd.get("artist_name", "?")
            correct = rd.get("correct_answer", "?")
            answers = rd.get("answers", [])

            sorted_ans = sorted(
                answers,
                key=lambda a: (
                    -a.get("points_earned", 0),
                    a.get("response_time", 9999),
                ),
            )
            try:
                min_time = (
                    min(float(a.get("response_time", 9999)) for a in sorted_ans)
                    if sorted_ans
                    else None
                )
            except Exception:
                min_time = None

            # Round card header
            hdr = Table(
                [
                    [
                        Paragraph(
                            f"<b>Manche {rnum}</b>  ·  {track}",
                            _s(
                                f"rh{rnum}a",
                                fontSize=9,
                                fontName="Helvetica-Bold",
                                textColor=C_WHITE,
                            ),
                        ),
                        Paragraph(
                            artist,
                            _s(
                                f"rh{rnum}b",
                                fontSize=8,
                                textColor=colors.HexColor("#F9EFE7"),
                            ),
                        ),
                        Paragraph(
                            f"Bonne réponse : <b>{correct}</b>",
                            _s(
                                f"rh{rnum}c",
                                fontSize=8,
                                textColor=colors.HexColor("#DC3842"),
                            ),
                        ),
                    ]
                ],
                colWidths=[COL_W * 0.38, COL_W * 0.30, COL_W * 0.32],
            )
            hdr.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), C_DARK),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LINEBELOW", (0, 0), (-1, -1), 2, C_ACCENT),
                    ]
                )
            )

            block = [hdr]

            # Bonus utilisés ce round
            round_bonuses = rd.get("bonuses", [])
            if round_bonuses:
                bonus_parts = [
                    f"{b.get('username', '?')} — {_BONUS_LABELS.get(b.get('bonus_type', ''), b.get('bonus_type', ''))}"
                    for b in round_bonuses
                ]
                bonus_tbl = Table(
                    [
                        [
                            Paragraph("<b>Bonus :</b>", S["bold_sm"]),
                            Paragraph("  |  ".join(bonus_parts), S["body_sm"]),
                        ]
                    ],
                    colWidths=[COL_W * 0.12, COL_W * 0.88],
                )
                bonus_tbl.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9EFE7")),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#EDE3DA")),
                        ]
                    )
                )
                block.append(bonus_tbl)

            if sorted_ans:
                col_hdr_sty = _s(
                    "ahdr",
                    fontSize=8,
                    fontName="Helvetica-Bold",
                    textColor=C_DARK_TEXT,
                )
                ans_rows_data = [
                    [
                        Paragraph("<b>#</b>", col_hdr_sty),
                        Paragraph("<b>Joueur</b>", col_hdr_sty),
                        Paragraph("<b>Réponse</b>", col_hdr_sty),
                        Paragraph("<b>Points</b>", col_hdr_sty),
                        Paragraph("<b>Temps</b>", col_hdr_sty),
                        Paragraph("<b>Série</b>", col_hdr_sty),
                    ]
                ]
                row_bg_cmds: list = []

                for row_i, a in enumerate(sorted_ans, start=1):
                    is_ok = a.get("is_correct", False)
                    is_fastest = (
                        min_time is not None
                        and float(a.get("response_time", 9999)) == min_time
                    )
                    streak_n = a.get("consecutive_correct") or 0
                    streak_b = a.get("streak_bonus", 0)

                    icon = "✓" if is_ok else "✗"
                    ans_text = f"{icon} {a.get('answer', '')}"
                    time_str = f"{a.get('response_time', 0):.1f}s"
                    streak_s = f"x{streak_n}" if streak_n > 1 else "-"

                    txt_sty = S["ok"] if is_ok else S["ko"]
                    # Truncate very long answers
                    if len(ans_text) > 55:
                        ans_text = ans_text[:52] + "…"

                    ans_rows_data.append(
                        [
                            Paragraph(str(row_i), S["grey"]),
                            Paragraph(
                                (
                                    f"<b>{a.get('username', '?')}</b>"
                                    if is_fastest
                                    else a.get("username", "?")
                                ),
                                S["bold_sm"] if is_fastest else S["body_sm"],
                            ),
                            Paragraph(ans_text, txt_sty),
                            Paragraph(
                                f"+{a.get('points_earned', 0)}",
                                S["bold_sm"] if is_ok else S["grey"],
                            ),
                            Paragraph(time_str, S["grey"]),
                            Paragraph(streak_s, S["grey"]),
                        ]
                    )

                    if is_fastest:
                        row_bg_cmds.append(
                            ("BACKGROUND", (0, row_i), (-1, row_i), C_FASTEST)
                        )
                    elif is_ok:
                        row_bg_cmds.append(
                            ("BACKGROUND", (0, row_i), (-1, row_i), C_CORRECT)
                        )
                    else:
                        row_bg_cmds.append(
                            ("BACKGROUND", (0, row_i), (-1, row_i), C_WRONG)
                        )

                ans_tbl = Table(ans_rows_data, colWidths=RW)
                ans_tbl.setStyle(
                    TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (-1, 0),
                                colors.HexColor("#F9EFE7"),
                            ),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("LINEBELOW", (0, 0), (-1, -1), 0.3, C_RULE),
                        ]
                        + row_bg_cmds
                    )
                )
                block.append(ans_tbl)
            else:
                empty_tbl = Table(
                    [[Paragraph("<i>Aucune réponse</i>", S["grey"])]],
                    colWidths=[COL_W],
                )
                empty_tbl.setStyle(
                    TableStyle(
                        [
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ]
                    )
                )
                block.append(empty_tbl)

            elements.append(KeepTogether(block))
            elements.append(Spacer(1, 8))

    # ════════════════════════════════════════════════════════════════════════
    # 5 — SYSTÈME DE SCORE (compact)
    # ════════════════════════════════════════════════════════════════════════
    elements.append(_section_header("Système de score", S["sec"]))
    elements.append(Spacer(1, 4))

    first_bonus = RANK_BONUS.get(0, 0)
    score_lines = [
        [
            Paragraph("<b>Base</b>", S["bold_sm"]),
            Paragraph(
                f"max({SCORE_MIN_CORRECT}, {SCORE_BASE_POINTS} − temps × {SCORE_TIME_PENALTY_PER_SEC})",
                S["body_sm"],
            ),
        ],
        [
            Paragraph("<b>Précision</b>", S["bold_sm"]),
            Paragraph(
                "× facteur d'exactitude (0.0 → 1.0 selon le mode)",
                S["body_sm"],
            ),
        ],
        [
            Paragraph("<b>Bonus rang</b>", S["bold_sm"]),
            Paragraph(
                f"+{first_bonus} pts pour le 1er joueur à répondre correctement, 5 pts pour le 2e, 3 pts pour le 3e",
                S["body_sm"],
            ),
        ],
        [
            Paragraph("<b>Bonus série</b>", S["bold_sm"]),
            Paragraph(
                "Points croissants selon le nombre de bonnes réponses consécutives",
                S["body_sm"],
            ),
        ],
        [
            Paragraph("<b>Bonus boutique</b>", S["bold_sm"]),
            Paragraph(
                "Points x2 (double les points de la prochaine manche correcte)  |  "
                "Points max (garantit au moins 100 pts de base)  |  "
                "Vol de pts (−100 pts au leader, si non protégé)  |  "
                "Joker (mauvaise réponse comptabilisée comme correcte)",
                S["body_sm"],
            ),
        ],
    ]
    st = Table(score_lines, colWidths=[COL_W * 0.22, COL_W * 0.78])
    st.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), C_LIGHT_BG),
                ("LINEBELOW", (0, 0), (-1, -1), 0.3, C_RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(st)

    doc.build(elements)
    return buf.getvalue()

"""KDA theme: one dark, data-dense esports palette expressed as a Qt palette.

Mirrors a Dota 2 client + HLTV analytics look: deep slate surfaces, gold
brand accent, teal secondary, explicit win/loss colors and monospaced numerals.
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

C = {
    "bg": "#0b0d12",
    "panel": "#101319",
    "panel2": "#141822",
    "panel3": "#1a1f2b",
    "line": "#222a38",
    "line2": "#2d3749",
    "ink": "#e8ebf1",
    "ink2": "#b3bccd",
    "muted": "#79839a",
    "faint": "#59637a",
    "gold": "#e2b04c",
    "gold_dim": "#a4823a",
    "teal": "#35b8a8",
    "win": "#4bbf73",
    "loss": "#d1565c",
}

RADIUS = 10
RADIUS_SM = 7

STYLE = f"""
QWidget {{ background: {C['bg']}; color: {C['ink']}; font-size: 13px; }}
/* Labels must be transparent so panel/card colours show through. */
QLabel {{ background: transparent; }}

/* ---------- panels ---------- */
QFrame[role="panel"] {{
    background: {C['panel']};
    border: 1px solid {C['line']};
    border-radius: {RADIUS}px;
}}
QFrame[role="head"] {{ background: transparent; border: none; }}
QFrame[role="panel2"] {{
    background: {C['panel2']};
    border: 1px solid {C['line']};
    border-radius: 8px;
}}

/* ---------- text roles ---------- */
QLabel[kicker] {{
    color: {C['faint']};
    font-size: 11px;
    letter-spacing: 2px;
}}
QLabel[title] {{
    color: {C['ink']};
    font-size: 22px;
    font-weight: 700;
}}
QLabel[subtitle] {{ color: {C['muted']}; font-size: 13px; }}
QLabel[panelTitle] {{ color: {C['ink']}; font-size: 13px; font-weight: 700; }}
QLabel[panelNote] {{ color: {C['faint']}; font-family: monospace; }}
QLabel[handle] {{ color: {C['faint']}; font-family: monospace; font-size: 12px; }}
QLabel[muted] {{ color: {C['muted']}; }}
QLabel[faint] {{ color: {C['faint']}; }}
QLabel[value] {{
    color: {C['ink']};
    font-family: monospace;
    font-size: 26px;
    font-weight: 700;
}}
QLabel[statLabel] {{
    color: {C['muted']};
    font-size: 11px;
    letter-spacing: 1.4px;
}}
QLabel[statSub] {{ color: {C['faint']}; font-size: 11px; }}
QLabel[badgeWin] {{
    color: {C['win']};
    background: rgba(75, 191, 115, 26);
    border: 1px solid rgba(75, 191, 115, 76);
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 700;
}}
QLabel[badgeLoss] {{
    color: {C['loss']};
    background: rgba(209, 86, 92, 26);
    border: 1px solid rgba(209, 86, 92, 76);
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 700;
}}
QLabel[rank] {{
    background: {C['panel3']};
    border: 1px solid {C['line2']};
    border-radius: 12px;
    padding: 5px 12px;
    color: {C['ink']};
}}
QLabel[heroName] {{ color: {C['ink']}; }}
QLabel[heroIcon] {{ background: {C['panel3']}; border: 1px solid {C['line2']}; border-radius: 6px; }}
QLabel[avatar] {{ background: {C['panel3']}; border: 1px solid {C['line2']}; border-radius: 12px; }}
QFrame[itemIcon] {{ background: {C['panel3']}; border: 1px solid {C['line2']}; border-radius: 5px; }}
QLabel[linkLabel] {{ color: {C['teal']}; font-size: 12px; }}
QLabel[sectionLabel] {{
    color: {C['ink']};
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel[teamRadiant] {{ color: {C['win']}; font-size: 12px; font-weight: 700; letter-spacing: 1px; }}
QLabel[teamDire] {{ color: {C['loss']}; font-size: 12px; font-weight: 700; letter-spacing: 1px; }}
QLabel[mono] {{ font-family: monospace; color: {C['ink2']}; }}
QLabel[chip] {{
    background: {C['panel']};
    border: 1px solid {C['line']};
    border-radius: 14px;
    padding: 5px 11px;
    color: {C['ink2']};
    font-size: 12px;
}}
QLabel[chipAccent] {{
    background: {C['panel2']};
    border: 1px solid {C['gold_dim']};
    border-radius: 14px;
    padding: 5px 11px;
    color: {C['gold']};
    font-size: 12px;
    font-weight: 700;
}}
QLabel[empty] {{ color: {C['muted']}; font-size: 14px; padding: 48px 24px; }}
QLabel[status] {{ color: {C['muted']}; font-size: 12px; }}
QLabel[statusBusy] {{ color: {C['gold']}; font-size: 12px; }}
QLabel[statusOk] {{ color: {C['win']}; font-size: 12px; }}
QLabel[statusErr] {{ color: {C['loss']}; font-size: 12px; }}

/* ---------- rail / brand ---------- */
QFrame[role="rail"] {{
    background: {C['panel']};
    border-right: 1px solid {C['line']};
}}
QLabel[brand] {{ color: {C['ink']}; font-family: monospace; font-size: 21px; font-weight: 700; }}
QLabel[brandSub] {{ color: {C['faint']}; font-size: 10px; letter-spacing: 2px; }}

/* ---------- buttons ---------- */
QPushButton {{
    background: transparent;
    color: {C['ink2']};
    border: 1px solid transparent;
    border-radius: {RADIUS_SM}px;
    padding: 8px 12px;
    text-align: left;
}}
QPushButton:hover {{ background: {C['panel2']}; color: {C['ink']}; }}
QPushButton:checked {{
    background: {C['panel3']};
    border: 1px solid {C['line2']};
    color: {C['ink']};
}}
QPushButton[nav] {{ padding: 9px 10px; font-size: 13px; }}
QPushButton[ghost] {{
    border: 1px solid {C['line']};
    color: {C['muted']};
    font-size: 12px;
    padding: 7px 10px;
}}
QPushButton[ghost]:hover {{ color: {C['ink']}; border-color: {C['line2']}; }}
QPushButton[primary] {{
    background: {C['gold']};
    color: #14100a;
    border: none;
    border-radius: {RADIUS_SM}px;
    font-weight: 700;
    padding: 8px 14px;
}}
QPushButton[primary]:hover {{ background: #f0c063; }}

/* ---------- inputs ---------- */
QLineEdit {{
    background: {C['panel']};
    border: 1px solid {C['line']};
    border-radius: {RADIUS_SM}px;
    padding: 8px 12px;
    color: {C['ink']};
    selection-background-color: {C['gold_dim']};
}}
QLineEdit:focus {{ border-color: {C['gold_dim']}; background: {C['panel2']}; }}
QLineEdit::placeholder {{ color: {C['faint']}; }}
QLineEdit[ghost] {{ border: none; background: transparent; padding: 4px; }}

/* ---------- tables ---------- */
QTableWidget {{
    background: {C['panel']};
    border: none;
    gridline-color: {C['line']};
    alternate-background-color: {C['panel2']};
    color: {C['ink2']};
}}
QTableWidget::item {{ padding: 6px; border: none; }}
QTableWidget::item:selected {{ background: {C['panel3']}; color: {C['ink']}; }}
QHeaderView::section {{
    background: {C['panel']};
    color: {C['faint']};
    border: none;
    border-bottom: 1px solid {C['line']};
    padding: 7px 16px 7px 8px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QTableCornerButton::section {{ background: {C['panel']}; border: none; }}

/* ---------- scrollbars ---------- */
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 2px; }}
QScrollBar::handle:vertical {{
    background: {C['line2']};
    min-height: 24px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['faint']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 2px; }}
QScrollBar::handle:horizontal {{
    background: {C['line2']};
    min-width: 24px;
    border-radius: 5px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: transparent; }}
QScrollArea {{ border: none; background: transparent; }}

QToolTip {{
    background: {C['panel3']};
    color: {C['ink']};
    border: 1px solid {C['line2']};
    padding: 5px 8px;
}}

/* ---------- home dashboard ---------- */
QWidget[heroCard] {{
    background: {C['panel2']};
    border: 1px solid {C['line']};
    border-radius: {RADIUS_SM}px;
}}
QWidget[heroCard]:hover {{ border-color: {C['gold_dim']}; }}
QProgressBar {{
    background: {C['panel3']};
    border: none;
    border-radius: 2px;
    height: 4px;
}}
QProgressBar::chunk {{ background: {C['gold']}; border-radius: 2px; }}
"""


def apply_theme(app: QApplication) -> None:
    """Install the KDA palette + stylesheet on the application."""
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(C["bg"]))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(C["ink"]))
    pal.setColor(QPalette.ColorRole.Base, QColor(C["panel"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(C["panel2"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(C["ink"]))
    pal.setColor(QPalette.ColorRole.Button, QColor(C["panel"]))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(C["ink"]))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(C["gold_dim"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#14100a"))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(C["panel3"]))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(C["ink"]))
    app.setPalette(pal)

    font = QFont("Sans Serif", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)
    app.setStyleSheet(STYLE)

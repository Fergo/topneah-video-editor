"""Theme palettes, typography and Qt styles for Topneah Video APP.

T is the shared active palette: update it in place so custom-painted widgets
always use the current colors. No QApplication is required to build styles.
"""
# ------------------------------------------------------------------ visual
# Neutral editing workspace; legacy amber keys share the blue accent palette.
T = dict(
    bg="#202020", panel="#292929", panel2="#343434", line="#454545", amber_line="#3D3D3D",
    text="#DEDEDE", muted="#A6A6A6", amber="#579BE8", amber2="#75ADF0", amber_dark="#3979BF",
    on_amber="#FFFFFF", danger="#D87575", track="#181818", tick="#626262",
    in_col="#DEDEDE", out_col="#D87575", hint_bg="#292929", hint_line="#454545",
    hint_text="#C4C4C4", sel_bg="#2D4055", warn="#D8B579",
    accent="#579BE8", switch_off="#484B50", switch_border="#62666D", switch_thumb="#DEDEDE",
)
DARK_THEME = T.copy()
WIN9X_THEME = dict(T, bg="#C0C0C0", panel="#C0C0C0", panel2="#C0C0C0",
    line="#808080", amber_line="#808080", text="#000000", muted="#505050",
    amber="#000080", amber2="#000080", amber_dark="#000080", on_amber="#FFFFFF",
    danger="#A00000", track="#FFFFFF", tick="#808080", in_col="#008000", out_col="#A00000",
    hint_bg="#FFFFE1", hint_line="#808080", hint_text="#000000", sel_bg="#000080",
    warn="#995000", accent="#000080", switch_off="#ADADAD",
    switch_border="#888888", switch_thumb="#F5F5F5")
WIN9X_FLAT_THEME = dict(WIN9X_THEME, panel="#C0C0C0", panel2="#D4D4D4", corner_radius=9)
XP_THEME = dict(WIN9X_FLAT_THEME, bg="#ECE9D8", panel="#ECE9D8", panel2="#F5F4EA",
    line="#ACA899", amber_line="#ACA899", text="#17233B", muted="#5D665A",
    amber="#245EDB", amber2="#75A5F4", amber_dark="#245EDB", accent="#245EDB",
    sel_bg="#245EDB", track="#FFFFFF", hint_bg="#FFFFE1", hint_line="#ACA899",
    hint_text="#17233B", warn="#975400", light=True, switch_off="#D7D3C0",
    switch_border="#ACA899", switch_thumb="#FFFFFF")
LIGHT_THEME = dict(DARK_THEME, bg="#F0F2F5", panel="#FFFFFF", panel2="#E8ECF1",
    line="#C8CFD8", amber_line="#D6DCE4", text="#252B33", muted="#626D7B",
    amber="#286EC5", amber2="#4084D6", amber_dark="#286EC5", accent="#286EC5",
    track="#E2E7EE", tick="#8C97A5", in_col="#34475B", out_col="#BA4545",
    danger="#BA4545", hint_bg="#EAF2FC", hint_line="#CAD9EC", hint_text="#34475B",
    sel_bg="#DCEBFC", warn="#946015", light=True, switch_off="#D6DDE6",
    switch_border="#AEB9C7", switch_thumb="#FFFFFF")
THEMES = {"dark": DARK_THEME, "light": LIGHT_THEME, "win9x": WIN9X_THEME,
          "win9x_flat": WIN9X_FLAT_THEME, "xp": XP_THEME}

DISPLAY = '"Segoe UI"'
BODY = '"Segoe UI"'



def build_base_style() -> str:
    t = T
    return f"""
QWidget#root {{ background: {t['bg']}; }}
* {{ font-family: {BODY}; }}
QWidget {{ background: transparent; color: {t['text']}; font-size: 13px; }}
QFrame#card {{ background: {t['panel']}; border: 1px solid {t['amber_line']}; border-radius: 3px; }}
QFrame#videoFrame {{ background: #000; border: 1px solid {t['amber_line']}; border-radius: 3px; }}
QLabel {{ background: transparent; }}
QLabel#sectionTitle {{ font-family: {DISPLAY}; font-size: 15px; font-weight: 600; letter-spacing: 0px; color: {t['text']}; }}
QLabel#num {{ background: {t['amber']}; color: {t['on_amber']}; border-radius: 3px;
             font-family: {DISPLAY}; font-size: 14px; }}
QLabel#title {{ font-family: {DISPLAY}; font-size: 22px; font-weight: 600; color: {t['text']}; letter-spacing: 0px; }}
QLabel#plate {{ background: transparent; color: {t['muted']}; border: none; border-radius: 3px;
               font-family: {DISPLAY}; font-size: 16px; letter-spacing: 0px; padding: 0px 12px; }}
QLabel#tagline {{ color: {t['muted']}; font-size: 12px; letter-spacing: 1px; }}
QLabel#hint {{ background: {t['hint_bg']}; border: 1px solid {t['hint_line']}; color: {t['hint_text']};
              border-radius: 3px; padding: 9px 14px; font-size: 14px; }}
QLabel#summary {{ background: #232323; border: 1px solid {t['amber_line']}; border-left: 3px solid {t['amber']};
                 border-radius: 3px; padding: 9px 12px; }}
QLabel#caption {{ color: {t['muted']}; font-size: 11px; }}
QLabel#value {{ font-size: 13px; font-weight: 600; }}
QLabel#dim {{ color: {t['muted']}; font-size: 13px; font-weight: 600; }}
QLabel#h {{ color: {t['amber']}; font-size: 10px; font-weight: 600; letter-spacing: 1px; }}
QLabel#presetTitle {{ font-size: 14px; font-weight: 600; }}
QLabel#presetDesc {{ color: {t['muted']}; font-size: 11px; }}
QLabel#dropTitle {{ font-family: {DISPLAY}; font-size: 23px; letter-spacing: 0px; }}
QLabel#dropSub {{ font-family: {DISPLAY}; font-size: 16px; letter-spacing: 0px; color: #A6A6A6; }}

QPushButton {{ background: {t['panel2']}; border: 1px solid {t['line']}; border-radius: 3px;
              padding: 9px 14px; font-weight: 600; }}
QPushButton:hover {{ border-color: {t['amber_dark']}; background: #414141; }}
QPushButton:disabled {{ color: #777777; background: #292929; border-color: #383838; }}
QPushButton#primary {{ background: {t['amber_dark']};
                      border: 1px solid {t['amber2']}; color: {t['on_amber']}; font-weight: 600; }}
QPushButton#primary:hover {{ background: {t['amber_dark']}; }}
QPushButton#primary:disabled {{ background: #292929; border: 1px solid #404040; color: #777777; }}
QPushButton#outline {{ background: transparent; border: 1px solid {t['amber_dark']}; color: {t['amber2']}; font-weight: 600; }}
QPushButton#outline:hover {{ background: #2D4055; border-color: {t['amber']}; }}
QPushButton#outline:disabled {{ border-color: #404040; color: #777777; }}
QPushButton#danger {{ background: transparent; border: 1px solid #6A2A22; color: #FF8B78; }}
QPushButton#danger:hover {{ background: #2A100C; border-color: {t['danger']}; }}
QPushButton#danger:disabled {{ border-color: #2A1D1B; color: #777777; }}
QPushButton#ghost {{ background: transparent; border: none; color: {t['muted']}; text-align: left;
                    padding: 4px 2px; font-weight: 600; }}
QPushButton#ghost:hover {{ color: {t['text']}; }}
QPushButton#iconbtn {{ padding: 0px; border-radius: 3px; }}
QPushButton#mode {{ background: {t['panel2']}; border: 1px solid {t['line']}; color: {t['text']}; font-weight: 600; }}
QPushButton#mode:checked {{ background: {t['amber_dark']};
                           border: 1px solid {t['amber2']}; color: {t['on_amber']}; }}
QPushButton#mode:disabled {{ color: #777777; background: #292929; border-color: #383838; }}
QPushButton#preset {{ background: #232323; border: 1px solid {t['line']}; border-radius: 3px; padding: 0; text-align: left; }}
QPushButton#preset:hover {{ border-color: {t['amber_dark']}; }}
QPushButton#preset:checked {{ border: 1px solid {t['amber']}; background: #2D4055; }}
QPushButton#start {{ font-family: {DISPLAY}; font-size: 14px; letter-spacing: 0px; padding: 8px 14px; }}

QListWidget {{ background: #232323; border: 1px solid {t['line']}; border-radius: 3px; outline: 0; }}
QListWidget::item {{ padding: 6px 8px; border-radius: 3px; }}
QListWidget::item:selected {{ background: {t['sel_bg']}; color: {t['text']}; border: 1px solid {t['amber_dark']}; }}
QComboBox {{ background: {t['panel2']}; border: 1px solid {t['line']}; border-radius: 3px;
            padding: 7px 10px; font-weight: 600; }}
QComboBox:hover {{ border-color: {t['amber_dark']}; }}
QComboBox:disabled {{ color: #777777; background: #292929; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{ image: none; width: 0px; height: 0px; }}
QComboBox QAbstractItemView {{ background: {t['panel2']}; color: {t['text']}; border: 1px solid {t['amber_dark']};
            selection-background-color: {t['amber']}; selection-color: {t['on_amber']}; outline: 0; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 17px; height: 17px; border: 2px solid #555; border-radius: 3px; background: #232323; }}
QCheckBox::indicator:checked {{ background: {t['amber']}; border-color: {t['amber']}; }}
QProgressBar {{ background: #232323; border: 1px solid {t['line']}; border-radius: 3px;
               text-align: center; height: 16px; font-size: 11px; font-weight: 600; }}
QProgressBar::chunk {{ background: {t['amber_dark']};
                      border-radius: 3px; }}
QSlider::groove:horizontal {{ height: 4px; background: #2B2B30; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {t['amber']}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: #fff; width: 14px; margin: -5px 0; border-radius: 3px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; }}
QScrollBar::handle:vertical {{ background: #3A3A40; border-radius: 3px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QPushButton:focus, QComboBox:focus {{ border: 1px solid {t['accent']}; }}
QFrame#titleBar {{ background: {t['bg']}; border-bottom: 1px solid {t['line']}; }}
QPushButton#windowControl, QPushButton#windowClose {{ background: transparent; border: none;
    border-radius: 0px; padding: 0px; font-size: 18px; font-weight: 400; color: {t['text']}; }}
QPushButton#windowControl:hover {{ background: #414141; }}
QPushButton#windowControl:pressed {{ background: #505050; }}
QPushButton#windowClose:hover {{ background: #C42B32; color: white; }}
QPushButton#windowClose:pressed {{ background: #A42329; }}
QToolTip {{ background: {t['panel2']}; color: {t['text']}; border: 1px solid {t['amber_dark']}; }}
"""


def _build_theme_style(theme="dark") -> str:
    style = build_base_style()
    if theme == "light":
        for old, new in {
            "#232323": "#F6F8FA", "#A6A6A6": "#626D7B", "#414141": "#DCE3ED",
            "#777777": "#919AA6", "#292929": "#EDF0F4", "#383838": "#D9DFE6",
            "#404040": "#D9DFE6", "#2D4055": "#DCEBFC", "#6A2A22": "#D6A3A3",
            "#FF8B78": "#BA4545", "#2A100C": "#FAE7E7", "#2A1D1B": "#DFCCCC",
            "#2B2B30": "#CDD5DF", "#3A3A40": "#ACB7C5", "#505050": "#C5CFDC",
        }.items():
            style = style.replace(old, new)
        return style + """
QComboBox#themeSelector { padding: 2px 8px; }
QPushButton#windowControl:hover { background: #DCE3ED; }
QPushButton#windowControl:pressed { background: #C5CFDC; }
QPushButton#windowClose:hover, QPushButton#windowClose:pressed { color: white; }
"""
    if theme in ("win9x_flat", "xp"):
        # Keep Dark's spacing, typography, radii and one-pixel borders.
        for old, new in {
            "#232323": "#FFFFFF", "#A6A6A6": "#505050", "#414141": "#DFDFDF",
            "#777777": "#808080", "#292929": "#C0C0C0", "#383838": "#A0A0A0",
            "#404040": "#A0A0A0", "#2D4055": "#D3DCEC", "#6A2A22": "#B06060",
            "#FF8B78": "#A00000", "#2A100C": "#E8CACA", "#2A1D1B": "#A0A0A0",
            "#2B2B30": "#A0A0A0", "#3A3A40": "#808080", "#505050": "#505050",
        }.items():
            style = style.replace(old, new)
        style += """
QFrame#titleBar { background: #000080; border-bottom: 1px solid #000080; }
QFrame#titleBar QLabel#caption { color: #FFFFFF; }
QPushButton#windowControl, QPushButton#windowClose { color: #FFFFFF; }
QPushButton#windowControl:hover { background: #28289C; }
QPushButton#windowControl:pressed { background: #4040AC; }
QComboBox#themeSelector { padding: 2px 8px; }
QListWidget::item:selected { color: #FFFFFF; }
QPushButton#outline:hover { color: #000080; }
"""
        if theme == "xp":
            style += """
QFrame#titleBar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
    stop:0 #4B98FF, stop:0.16 #2474EA, stop:0.85 #0054E3, stop:1 #003CB3);
    border-bottom: 1px solid #003CB3; }
QFrame#titleBar QLabel#caption { color: white; font-weight: bold; }
QFrame#card { background: #ECE9D8; border-color: #ACA899; border-radius: 5px; }
QLabel#sectionTitle, QLabel#h { color: #003C74; }
QLabel#num { background: #245EDB; color: white; }
QLabel#summary, QLabel#hint { background: #FFFFE1; border-color: #ACA899; color: #17233B; }
QPushButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FFFFFF, stop:1 #E2DFCF);
    border: 1px solid #7F9DB9; border-radius: 4px; }
QPushButton:hover { background: #FFF4CF; border-color: #E0A534; }
QPushButton#primary, QPushButton#mode:checked, QPushButton#start:enabled {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #7CC96B, stop:0.45 #399534, stop:1 #277B25);
    border: 1px solid #206B21; color: white; border-radius: 5px; }
QPushButton#primary:hover, QPushButton#mode:checked:hover, QPushButton#start:enabled:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #99DE84, stop:1 #378C2D); }
QPushButton#mode { border-color: #7F9DB9; }
QPushButton:disabled, QPushButton#primary:disabled, QPushButton#mode:disabled {
    background: #E6E3D5; color: #96958D; border-color: #C9C7BA; }
QComboBox { background: white; border-color: #7F9DB9; }
QComboBox::drop-down { background: #D6E5F8; border-left: 1px solid #7F9DB9; }
QComboBox#themeSelector { background: #EAF2FF; color: #17233B; border-color: #003CB3; }
QComboBox QAbstractItemView { background: white; }
QListWidget { border-color: #7F9DB9; }
QProgressBar { background: white; border-color: #7F9DB9; }
QProgressBar::chunk { background: #40AA37; }
QSlider::sub-page:horizontal { background: #40AA37; }
QScrollBar:vertical { background: #F1EFE2; }
QScrollBar::handle:vertical { background: #C4D9F4; border: 1px solid #7F9DB9; }
QPushButton#windowControl, QPushButton#windowClose { background: transparent;
    color: white; border: none; border-radius: 3px; font-size: 18px; }
QPushButton#windowControl:hover { background: #4388EB; }
QPushButton#windowControl:pressed { background: #0043B5; }
QPushButton#windowClose:hover { background: #D95235; }
QPushButton#windowClose:pressed { background: #B93520; }
QToolTip { background: #FFFFE1; color: #17233B; border-color: #ACA899; }
"""
        return style
    if theme != "win9x":
        return style
    return style + """
* { font-family: "Tahoma"; }
QWidget { color: #000000; }
QFrame#card { background: #C0C0C0; border: 2px solid;
    border-color: #FFFFFF #808080 #808080 #FFFFFF; border-radius: 0; }
QFrame#videoFrame { border: 2px solid; border-color: #808080 #FFFFFF #FFFFFF #808080; border-radius: 0; }
QLabel#sectionTitle { font-family: "Tahoma"; font-size: 13px; font-weight: bold; }
QLabel#num { border-radius: 0; background: #000080; color: white; }
QLabel#dropSub, QLabel#caption { color: #505050; }
QLabel#h { color: #000000; }
QLabel#summary, QLabel#hint { background: #FFFFE1; color: black; border: 1px solid #808080; border-radius: 0; }
QPushButton, QPushButton#primary, QPushButton#outline, QPushButton#danger,
QPushButton#mode, QPushButton#start, QPushButton#iconbtn {
    background: #C0C0C0; color: black; border: 2px solid;
    border-color: #FFFFFF #404040 #404040 #FFFFFF; border-radius: 0; padding: 9px 8px; font-weight: 400; }
QPushButton:hover, QPushButton#primary:hover, QPushButton#outline:hover,
QPushButton#danger:hover { background: #CACACA; color: black; }
QPushButton:pressed, QPushButton#primary:pressed, QPushButton#mode:checked {
    background: #B0B0B0; color: black; border: 2px solid;
    border-color: #404040 #FFFFFF #FFFFFF #404040; }
QPushButton:disabled, QPushButton#primary:disabled, QPushButton#outline:disabled,
QPushButton#danger:disabled, QPushButton#mode:disabled {
    background: #C0C0C0; color: #808080; border: 2px solid;
    border-color: #FFFFFF #808080 #808080 #FFFFFF; }
QPushButton#ghost { color: black; }
QPushButton#ghost:hover { color: #000080; }
QComboBox { font-weight: 400; }
QListWidget, QComboBox { background: white; color: black; border: 2px solid;
    border-color: #808080 #FFFFFF #FFFFFF #808080; border-radius: 0; }
QListWidget::item { border-radius: 0; }
QListWidget::item:selected { background: #000080; color: white; }
QComboBox:disabled { background: #C0C0C0; color: #808080; }
QComboBox::drop-down { background: #C0C0C0; border-left: 1px solid #808080; }
QComboBox QAbstractItemView { background: white; color: black;
    selection-background-color: #000080; selection-color: white; }
QCheckBox::indicator { background: white; border-radius: 0; border: 2px inset #808080; }
QCheckBox::indicator:checked { background: #000080; }
QProgressBar { background: white; color: black; border: 2px inset #808080; border-radius: 0; }
QProgressBar::chunk { background: #000080; border-radius: 0; }
QSlider::groove:horizontal { background: #808080; }
QSlider::handle:horizontal { background: #C0C0C0; border: 2px outset #FFFFFF; border-radius: 0; }
QScrollBar:vertical { background: #DFDFDF; width: 14px; }
QScrollBar::handle:vertical { background: #C0C0C0; border: 2px outset white; border-radius: 0; }
QFrame#titleBar { background: #000080; border: none; }
QFrame#titleBar QLabel#caption { color: white; font-weight: bold; }
QPushButton#windowControl, QPushButton#windowClose { background: #C0C0C0; color: black;
    border: 2px solid; border-color: #FFFFFF #404040 #404040 #FFFFFF; border-radius: 0; }
QPushButton#windowControl:hover, QPushButton#windowClose:hover { background: #D0D0D0; color: black; }
QPushButton#windowControl:pressed, QPushButton#windowClose:pressed {
    background: #B0B0B0; border-color: #404040 #FFFFFF #FFFFFF #404040; }
QComboBox#themeSelector { background: #C0C0C0; color: black; padding: 2px 8px; }
QToolTip { background: #FFFFE1; color: black; border: 1px solid black; }
"""


THEME_LABELS = {
    "dark": "Escuro",
    "light": "Claro",
    "win9x": "Win9x",
    "win9x_flat": "Win9x Flat",
    "xp": "Windows XP",
}


def activate_theme(theme: str) -> str:
    """Select a palette in place, falling back to Dark for unknown names."""
    theme = theme if theme in THEMES else "dark"
    T.clear()
    T.update(THEMES[theme])
    return theme


def build_style(theme="dark") -> str:
    """Apply compact sidebar typography consistently across every theme."""
    return _build_theme_style(theme) + """
QWidget#sidebar QWidget { font-size: 12px; }
QWidget#sidebar QLabel#sectionTitle { font-size: 13px; }
QWidget#sidebar QLabel#num { font-size: 12px; }
QWidget#sidebar QLabel#caption { font-size: 10px; }
QWidget#sidebar QLabel#h { font-size: 10px; }
QWidget#sidebar QPushButton { padding-top: 7px; padding-bottom: 7px; }
QWidget#sidebar QComboBox { padding-top: 5px; padding-bottom: 5px; }
QWidget#sidebar QLabel#summary { padding: 7px 10px; }
"""


def build_dialog_style(theme="dark") -> str:
    """Export result dialogs use the same palette and controls as the editor."""
    palette = THEMES.get(theme, DARK_THEME)
    radius = 0 if theme == "win9x" else 6
    return build_style(theme) + f"""
QDialog#resolutionDialog, QMessageBox {{ background: {palette['panel']}; border: 1px solid {palette['line']};
    border-radius: {radius}px; padding: 16px; }}
QMessageBox QLabel {{ background: transparent; color: {palette['text']}; }}
QMessageBox QLabel#qt_msgbox_label {{ font-size: 16px; font-weight: 600; }}
QMessageBox QLabel#qt_msgbox_informativelabel {{ font-size: 13px; }}
QMessageBox QPushButton {{ min-width: 90px; }}
QDialog#resolutionDialog QSpinBox {{ background: {palette['track']}; color: {palette['text']};
    border: 1px solid {palette['line']}; padding: 6px; min-width: 100px; }}
"""

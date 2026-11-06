"""Measures for the HR-Attrition story report (folder 6 Story). Loaded by build_pbip.py."""

LEAVER, TINT, STAYED, OFF, KEPT, MUTED = "#C8325B", "#E39AAE", "#9AA8B3", "#DCDED8", "#00829B", "#5D6B75"
HEAT = ["#E39AAE", "#D56B88", "#C44166", "#A12347", "#6E1431"]


def top_title(prefix, col, label_expr="Grp", fallback="Too few people in this selection to compare"):
    """'Highest attrition: <group>, 39.8%' for the group with the highest rate (20+ people)."""
    return f'''
VAR T =
    FILTER (
        ADDCOLUMNS ( VALUES ( Employees[{col}] ), "@R", [Attrition Rate], "@N", [Employees] ),
        [@N] >= 20
    )
VAR Top1 = TOPN ( 1, T, [@R], DESC )
VAR Grp = MAXX ( Top1, Employees[{col}] )
RETURN
    IF (
        ISEMPTY ( T ),
        "{fallback}",
        "{prefix}" & {label_expr} & ", " & FORMAT ( MAXX ( Top1, [@R] ), "0.0%" )
    )'''


# Bars: the highest bar in the chart carries full raspberry, every other bar steps back to the tint
SCOPES = [("JobRole", None), ("Age Band", "Age Band Order"), ("Tenure Band", "Tenure Band Order"),
          ("Job Satisfaction", "JobSatisfaction"), ("Work-Life Balance", "WorkLifeBalance"),
          ("BusinessTravel", None), ("Stock Options", "StockOptionLevel"), ("Income Band", "Income Band Order"),
          ("Department", None), ("Overtime Status", "Overtime Order"), ("Job Level", "JobLevel")]


def bar_color(measure):
    branches = ",\n    ".join(
        f"ISINSCOPE ( Employees[{c}] ), MAXX ( ALLSELECTED ( Employees[{c}]{', Employees[' + o + ']' if o else ''} ), {measure} )"
        for c, o in SCOPES)
    return f'''
VAR V = {measure}
VAR Mx =
    SWITCH (
        TRUE (),
    {branches}
    )
RETURN IF ( NOT ISBLANK ( V ) && V >= Mx, "{LEAVER}", "{TINT}" )'''


def rgb(hex_):
    """SVG colour without '#': Power BI re-encodes image URLs, which breaks %23 escapes."""
    h = hex_.lstrip("#")
    return "rgb(" + ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4)) + ")"


def runs(lo, hi):
    """Dots lo..hi-1 of a department block as one dashed segment per grid row (49 dots per row)."""
    return f"""
        VAR _S = {lo}
        VAR _E = {hi}
        RETURN
            IF (
                _E > _S,
                CONCATENATEX (
                    GENERATESERIES ( INT ( _S / 49 ), INT ( ( _E - 1 ) / 49 ) ),
                    VAR _R = [Value]
                    VAR _C1 = IF ( _R = INT ( _S / 49 ), MOD ( _S, 49 ), 0 )
                    VAR _C2 = IF ( _R = INT ( ( _E - 1 ) / 49 ), MOD ( _E - 1, 49 ), 48 )
                    RETURN "M" & ( 5 + _C1 * 10 ) & " " & ( _Y0 + _R * 10 ) & "h" & ( ( _C2 - _C1 ) * 10 + 0.01 ),
                    ""
                )
            )"""


def dept_runs(lo, hi):
    return f"""
    CONCATENATEX (
        _Depts,
        VAR _D = [D]
        VAR _Y0 = [LY] + 13
        VAR _A = CALCULATE ( [Leavers], KEEPFILTERS ( Employees[Department] = _D ) ) + 0
        VAR _B = CALCULATE ( [Active Employees], KEEPFILTERS ( Employees[Department] = _D ) ) + 0
        VAR _T = CALCULATE ( COUNTROWS ( Employees ), REMOVEFILTERS ( Employees ), Employees[Department] = _D ) + 0
        {runs(lo, hi)},
        ""
    )"""


STORY_MEASURES = [
    # ---------------------------------------------------------------- hero: one dot per employee
    ("Dot Grid SVG", "6 Story", None, f'''
// Every employee is a dot, in one block per department. Inside each block: people in the current filter
// who left (raspberry), then those who stayed (grey), then everyone outside the filter (faded).
// Each grid row of a run is one dashed stroke ('0 10' + round caps = a row of dots), which keeps the
// image URL short enough for Power BI (one path per dot was cut off).
VAR _Depts =
    SELECTCOLUMNS (
        CALCULATETABLE ( SUMMARIZE ( Employees, Employees[Department], Employees[Dot Label Y] ), REMOVEFILTERS () ),
        "D", Employees[Department] & "", "LY", Employees[Dot Label Y] + 0
    )
VAR _Left = {dept_runs("0", "_A")}
VAR _Stay = {dept_runs("_A", "_A + _B")}
VAR _Faded = {dept_runs("_A + _B", "_T")}
VAR _Labels =
    CONCATENATEX (
        _Depts,
        VAR _D = [D]
        VAR _N = CALCULATE ( [Employees], KEEPFILTERS ( Employees[Department] = _D ) )
        VAR _L = CALCULATE ( [Leavers], KEEPFILTERS ( Employees[Department] = _D ) )
        RETURN
            "<text x='3' y='" & [LY] & "'>" & SUBSTITUTE ( _D, "&", "&amp;" )
                & "<tspan fill='{rgb(MUTED)}' dx='8'>"
                & IF ( _N = 0, "not in this selection",
                    FORMAT ( _L, "#,0" ) & " of " & FORMAT ( _N, "#,0" ) & " left (" & FORMAT ( DIVIDE ( _L, _N ), "0.0%" ) & ")" )
                & "</tspan></text>",
        ""
    )
VAR _Path = "<path fill='none' stroke-linecap='round' stroke-width='7' stroke-dasharray='0 10' "
RETURN
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 490 410'>"
        & "<g font-family='Segoe UI' font-size='11' font-weight='600' fill='{rgb("#172026")}'>" & _Labels & "</g>"
        & _Path & "stroke='{rgb(OFF)}' d='" & _Faded & "'/>"
        & _Path & "stroke='{rgb(STAYED)}' d='" & _Stay & "'/>"
        & _Path & "stroke='{rgb(LEAVER)}' d='" & _Left & "'/>"
        & "</svg>"''', "One dot per employee as an SVG image; used by the hero on the Who leaves page."),
    ("Headline People", "6 Story", None, '''
IF (
    [Employees] = 0,
    "No one matches these filters",
    FORMAT ( [Leavers], "#,0" ) & " of " & FORMAT ( [Employees], "#,0" ) & " people left"
)''', None),
    ("Headline Note", "6 Story", None, '''
IF (
    [Employees] = 0,
    "Reset the filters to see everyone again.",
    FORMAT ( [Attrition Rate], "0.0%" ) & " attrition. Each dot is one person; click any bar to light up that group."
)''', None),

    # ---------------------------------------------------------------- titles that state the finding
    ("Title Role", "6 Story", None, top_title("Highest attrition: ", "JobRole"), None),
    ("Title Age", "6 Story", None, top_title("Highest attrition: ages ", "Age Band"), None),
    ("Title Tenure", "6 Story", None, top_title("Highest attrition: ", "Tenure Band", 'Grp & " at the company"'), None),
    ("Title Job Satisfaction", "6 Story", None, top_title("Highest attrition: ", "Job Satisfaction", 'Grp & " job satisfaction"'), None),
    ("Title Work-Life", "6 Story", None, top_title("Highest attrition: ", "Work-Life Balance", 'Grp & " work-life balance"'), None),
    ("Title Travel", "6 Story", None, top_title("Highest attrition: ", "BusinessTravel", 'LOWER ( Grp )'), None),
    ("Title Stock", "6 Story", None, top_title("Highest attrition: stock options ", "Stock Options", 'LOWER ( Grp )'), None),
    ("Title Matrix", "6 Story", None, '''
VAR T =
    FILTER (
        ADDCOLUMNS (
            SUMMARIZE ( Employees, Employees[Job Level], Employees[Overtime Status] ),
            "@R", [Attrition Rate], "@N", [Employees]
        ),
        [@N] >= 20
    )
VAR Top1 = TOPN ( 1, T, [@R], DESC )
RETURN
    IF (
        ISEMPTY ( T ),
        "Too few people in this selection to compare",
        "Highest attrition: " & MAXX ( Top1, Employees[Job Level] ) & ", " & LOWER ( MAXX ( Top1, Employees[Overtime Status] ) )
            & ", " & FORMAT ( MAXX ( Top1, [@R] ), "0.0%" ) & " leave"
    )''', None),
    ("Subtitle Metric", "6 Story", None, '''"Bars show " & LOWER ( SELECTEDVALUE ( 'Metric Selector'[Metric], "Attrition Rate" ) )''', None),
    ("Title Gender Pay", "6 Story", None, '''
VAR Gap = [Gender Pay Gap %]
RETURN
    SWITCH (
        TRUE (),
        ISBLANK ( [Avg Income (Male)] ) || ISBLANK ( [Avg Income (Female)] ), "Average monthly income by role",
        Gap < 0, "Women earn " & FORMAT ( -Gap, "0.0%" ) & " more than men on average",
        "Men earn " & FORMAT ( Gap, "0.0%" ) & " more than women on average"
    )''', None),
    ("Title Break-even", "6 Story", None, '''
VAR _Lv =
    ADDCOLUMNS ( VALUES ( Employees[Job Level] ), "@BE", [Break-even Leavers], "@L", [Leavers] )
VAR Pays = COUNTROWS ( FILTER ( _Lv, [@L] > 0 && [@BE] <= [@L] ) )
RETURN
    "At a " & FORMAT ( [Raise % Value], "0.0%" ) & " raise, " & FORMAT ( Pays + 0, "0" ) & " of "
        & COUNTROWS ( _Lv ) & " job levels can break even"''', None),

    # ---------------------------------------------------------------- what-if hero sentence
    ("Hero Raise", "6 Story", None, '''
VAR R = [Raise % Value]
VAR BE = [Break-even Leavers]
VAR L = [Leavers]
RETURN
    SWITCH (
        TRUE (),
        R = 0, "Move the raise slider to see what keeping people would cost.",
        L = 0, "No one left in this selection, so a raise has nothing to pay back.",
        "A " & FORMAT ( R, "0.0%" ) & " raise for the " & FORMAT ( [Active Employees], "#,0" ) & " people who stayed costs "
            & FORMAT ( [Raise Cost (Annual)] / 1e6, "0.0" ) & "M a year. "
            & IF (
                BE > L,
                "To pay for itself it would have to stop " & FORMAT ( BE, "#,0" ) & " departures, but only "
                    & FORMAT ( L, "#,0" ) & " people left.",
                "It pays for itself if it stops " & FORMAT ( BE, "#,0" ) & " of the " & FORMAT ( L, "#,0" )
                    & " departures (" & FORMAT ( DIVIDE ( BE, L ), "0%" ) & ")."
            )
    )''', "Plain-English payback of the selected raise, for the What it costs page."),

    # ---------------------------------------------------------------- colour as data (conditional formatting)
    ("Color Rate Bar", "6 Story", None, bar_color("[Attrition Rate]"), "Raspberry for the highest bar, tint for the rest."),
    ("Color Metric Bar", "6 Story", None, bar_color("[Selected Metric]"), "Same rule for the metric-switch charts."),
    ("Color Heat", "6 Story", None, f'''
VAR R = [Attrition Rate]
RETURN
    SWITCH ( TRUE (), ISBLANK ( R ), "#ECEDE8", R < 0.08, "{HEAT[0]}", R < 0.15, "{HEAT[1]}", R < 0.25, "{HEAT[2]}",
        R < 0.4, "{HEAT[3]}", "{HEAT[4]}" )''', "Sequential raspberry ramp, light to dark, for the job level x overtime matrix."),
    ("Color Heat Text", "6 Story", None, '''IF ( [Attrition Rate] >= 0.15, "#FFFFFF", "#172026" )''', None),

    # ---------------------------------------------------------------- tooltip page
    ("Tooltip Role", "6 Story", None, '''SELECTEDVALUE ( Employees[JobRole], "Several roles" )''', None),
    ("Tooltip Leavers", "6 Story", None, '''FORMAT ( [Leavers], "#,0" ) & " of " & FORMAT ( [Employees], "#,0" ) & " left"''', None),
    ("Overtime Share", "6 Story", "0%", '''DIVIDE ( CALCULATE ( [Employees], Employees[OverTime] = "Yes" ), [Employees] )''',
     "Share of people in the selection who work overtime."),
]

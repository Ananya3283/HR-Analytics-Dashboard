"""Generate HR-Attrition-Story: a second PBIR report on the shared HR-Analytics semantic model.

Design rules carried over from the web-ui skill, inside Power BI's limits:
- one hero per page (dot grid / heat matrix / what-if sentence), everything else quiet
- no card chrome: visuals sit on the paper background; no gridlines, recessive axes
- every control has rest / hover / press / selected states; tooltips are a custom page
- titles state the finding (DAX measures); the highest bar is raspberry, the rest tint
"""
import json, os, shutil, sys

REPO = sys.argv[1]
NAME = "HR-Attrition-Story"
RP, SM = f"{NAME}.Report", "HR-Analytics.SemanticModel"
SCH = "https://developer.microsoft.com/json-schemas/fabric/"
V_SCH = SCH + "item/report/definition/visualContainer/2.4.0/schema.json"

# Tokens (same palette as the web version, validated with the dataviz checker)
PAPER, SURFACE, TRACK, LINE, INK, SLATE, MUTED = "#F7F7F4", "#FFFFFF", "#ECEDE8", "#DCDED8", "#172026", "#46535D", "#5D6B75"
LEAVER, TINT, STAYED, KEPT, FEMALE, MALE = "#C8325B", "#E39AAE", "#9AA8B3", "#00829B", "#3D63C9", "#B26B00"
FONT, FONT_SEMI = "Segoe UI", "Segoe UI Semibold"
W, H, M, G = 1280, 720, 24, 16
LEFT_W = 560
RX = M + LEFT_W + 32          # right column x
RW = W - M - RX               # right column width
HALF = (RW - G) // 2

shutil.rmtree(os.path.join(REPO, RP, "definition"), ignore_errors=True)
shutil.rmtree(os.path.join(REPO, RP, "StaticResources"), ignore_errors=True)


def write(rel, content):
    p = os.path.join(REPO, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if not isinstance(content, str):
        content = json.dumps(content, indent=2, ensure_ascii=False)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.rstrip("\n") + "\n")


def lit(v):
    if isinstance(v, bool): s = "true" if v else "false"
    elif isinstance(v, int): s = f"{v}L"
    elif isinstance(v, float): s = f"{v}D"
    else: s = "'" + v.replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def measure(n):
    return {"expr": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": n}}}


def props(**kw):
    out = {}
    for k, v in kw.items():
        if isinstance(v, str) and v.startswith("#") and len(v) == 7:
            out[k] = {"solid": {"color": lit(v)}}
        elif isinstance(v, str) and v.startswith("M:"):          # measure-driven value (fx)
            out[k] = measure(v[2:])
        elif isinstance(v, str) and v.startswith("C:"):          # measure-driven colour (fx)
            out[k] = {"solid": {"color": measure(v[2:])}}
        elif isinstance(v, dict):
            out[k] = v
        else:
            out[k] = lit(v)
    return out


def obj(selector=None, **kw):
    o = {"properties": props(**kw)}
    if selector: o["selector"] = selector
    return [o]


def state(sid, **kw):
    return obj({"id": sid}, **kw)


ALL_POINTS = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}


def field_ref(f):
    """'M:Attrition Rate' = measure, 'Table.Column' or 'Column' (Employees) = column."""
    if f.startswith("M:"):
        n = f[2:]
        return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": n}}, f"_Measures.{n}", n
    t, c = ("Employees", f) if "." not in f else f.split(".", 1)
    return {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}, f"{t}.{c}", c


def projections(fields, names=None, active_first=False):
    out = []
    for i, f in enumerate(fields):
        ref, qref, native = field_ref(f)
        p = {"field": ref, "queryRef": qref, "nativeQueryRef": native}
        if names and names.get(f): p["displayName"] = names[f]
        if active_first and i == 0: p["active"] = True
        out.append(p)
    return {"projections": out}


def series_selector(column, value):
    return {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": field_ref(column)[0],
                                                  "Right": {"Literal": {"Value": f"'{value}'"}}}}}]}


class Page:
    def __init__(self, name, display, width=W, height=H):
        self.name, self.display, self.width, self.height, self.visuals = name, display, width, height, []

    def add(self, vname, vtype, x, y, w, h, roles=None, objects=None, vco=None, sort=None, names=None,
            alt=None, extra=None):
        visual = {"visualType": vtype}
        if roles:
            visual["query"] = {"queryState": {r: projections(fs, names, r == "Category") for r, fs in roles.items()}}
            if sort:
                f, direction = sort
                visual["query"]["sortDefinition"] = {"sort": [{"field": field_ref(f)[0], "direction": direction}],
                                                     "isDefaultSort": True}
        if objects: visual["objects"] = objects
        vco = dict(vco or {})
        vco.setdefault("background", obj(show=False))
        vco.setdefault("border", obj(show=False))
        vco.setdefault("dropShadow", obj(show=False))
        if alt: vco["general"] = obj(altText=alt)
        visual["visualContainerObjects"] = vco
        if roles and vtype in ("clusteredBarChart", "clusteredColumnChart", "scatterChart", "pivotTable"):
            visual["drillFilterOtherVisuals"] = True
        container = {"$schema": V_SCH, "name": vname,
                     "position": {"x": x, "y": y, "z": len(self.visuals) * 1000, "height": h, "width": w,
                                  "tabOrder": len(self.visuals) * 1000},
                     "visual": visual}
        if extra: container["visual"].update(extra)
        self.visuals.append(container)


def default_filter(entity, column, literal, single_value=False):
    """A slicer's saved selection, so the control shows the value the measures fall back to.
    Single-value sliders save an equals comparison; list and button slicers save an In filter."""
    col_ = {"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": column}}
    cond = ({"Comparison": {"ComparisonKind": 0, "Left": col_, "Right": {"Literal": {"Value": literal}}}} if single_value
            else {"In": {"Expressions": [col_], "Values": [[{"Literal": {"Value": literal}}]]}})
    return obj(filter={"filter": {"Version": 2, "From": [{"Name": "t", "Entity": entity, "Type": 0}],
                                  "Where": [{"Condition": cond}]}})


def chart_title(text_or_measure, subtitle=None):
    t = {"title": obj(show=True, text=text_or_measure, fontFamily=FONT_SEMI, fontSize=12.0, fontColor=INK,
                      alignment="left", titleWrap=True)}
    if subtitle:
        t["subTitle"] = obj(show=True, text=subtitle, fontFamily=FONT, fontSize=9.0, fontColor=MUTED, alignment="left")
    t["padding"] = obj(top=0.0, bottom=0.0, left=0.0, right=0.0)
    return t


def quiet():
    return {"title": obj(show=False), "visualHeader": obj(show=False), "padding": obj(top=0.0, bottom=0.0, left=0.0, right=0.0)}


PAGES = [("page_who", "Who leaves"), ("page_why", "Why they leave"), ("page_cost", "What it costs")]
TT_PAGE = "page_tt_role"


# ---------------------------------------------------------------- shared chrome
def header(p, note):
    p.add("h_title", "textbox", M, 16, 600, 40, objects={"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": p.display, "textStyle": {"fontFamily": FONT_SEMI, "fontSize": "20pt", "color": INK}},
                      {"value": "   " + note, "textStyle": {"fontFamily": FONT, "fontSize": "10pt", "color": MUTED}}]}]}}]},
          vco=quiet())
    # Tabs: a muted track with the current page as a raised white pill (shadcn Tabs, built from native parts)
    tw = 3 * 176 + 8
    tx = W - M - tw
    p.add("h_tab_track", "shape", tx, 16, tw, 40,
          objects={"shape": obj(tileShape="rectangleRoundedByPixel", rectangleRoundedCurve=10),
                   "fill": obj(show=True) + state("default", fillColor=TRACK, transparency=0.0),
                   "outline": obj(show=False) + state("default", show=False)},
          vco=quiet())
    p.add("h_tabs", "pageNavigator", tx + 4, 20, tw - 8, 32,
          objects={
              "pages": obj(showTooltipPages=False, showHiddenPages=False),
              "layout": obj(cellPadding=4, orientation=0),
              "shape": obj(tileShape="rectangleRoundedByPixel", rectangleRoundedCurve=8),
              "fill": obj(show=True) + state("default", fillColor=TRACK, transparency=0.0)
                      + state("hover", fillColor="#E2E4DE", transparency=0.0)
                      + state("selected", fillColor=SURFACE, transparency=0.0),
              "text": obj(show=True) + state("default", fontColor=MUTED, fontFamily=FONT_SEMI, fontSize=10.0)
                      + state("hover", fontColor=INK) + state("selected", fontColor=INK),
              "outline": obj(show=True) + state("default", lineColor=TRACK, weight=1.0, transparency=0.0)
                         + state("selected", lineColor=LINE, weight=1.0, transparency=0.0),
          },
          vco=quiet(), alt="Page tabs")


SLICER_W = 176


def dropdown(p, i, field, label, x=None):
    x = M + i * (SLICER_W + 12) if x is None else x
    p.add(f"f_{i}", "slicer", x, 72, SLICER_W, 52, roles={"Values": [field]},
          objects={"data": obj(mode="Dropdown"),
                   "header": obj(show=True, text=label, fontColor=MUTED, fontFamily=FONT, textSize=9.0),
                   "items": obj(fontColor=INK, fontFamily=FONT, textSize=10.0, background=SURFACE)},
          vco={**quiet(), "background": obj(show=True, color=SURFACE, transparency=0.0),
               "border": obj(show=True, color=LINE, radius=8.0, width=1.0),
               "padding": obj(top=4.0, bottom=4.0, left=10.0, right=10.0)},
          extra={"syncGroup": {"groupName": field, "fieldChanges": True, "filterChanges": True}}, alt=f"Filter: {label}")
    return x + SLICER_W


def reset_button(p, x):
    # Rest: outline only. Hover: track fill. Press: one step darker. Same as the web version's ghost button.
    p.add("f_reset", "actionButton", x, 80, 112, 36,
          objects={
              "icon": obj(show=False),
              "text": obj(show=True) + state("default", text="Reset filters", fontColor=SLATE, fontFamily=FONT_SEMI, fontSize=10.0)
                      + state("hover", fontColor=INK) + state("press", fontColor=INK),
              "fill": obj(show=True) + state("default", fillColor=PAPER, transparency=0.0)
                      + state("hover", fillColor=TRACK, transparency=0.0) + state("press", fillColor=LINE, transparency=0.0),
              "outline": obj(show=True) + state("default", lineColor=LINE, weight=1.0),
          },
          vco={**quiet(), "visualLink": obj(show=True, type="ClearAllSlicers")}, alt="Reset all filters")


def figure(p, vname, m, label, x, y, w=176, h=84, tone=INK, units=None, size=24.0):
    """A number with a small label: no box, left aligned (dataviz 'figure', not a KPI tile)."""
    value = dict(fontColor=tone, fontFamily=FONT_SEMI, fontSize=size, horizontalAlignment="left")
    if units: value.update(labelDisplayUnits=units, labelPrecision=1)
    p.add(vname, "cardVisual", x, y, w, h, roles={"Data": [m]}, names={m: label},
          objects={"value": state("default", **value),
                   "label": state("default", show=True, fontColor=MUTED, fontFamily=FONT, fontSize=10.0,
                                  position="aboveValue", horizontalAlignment="left"),
                   "layout": obj(alignment="left", backgroundShow=False),
                   "fillCustom": state("default", show=True, fillColor=PAPER, transparency=0.0),
                   "outline": state("default", show=False),
                   "accentBar": state("default", show=False)},
          vco=quiet(), alt=label)


def sentence(p, vname, m, x, y, w, h, size=10.0, tone=INK, font=FONT):
    """A DAX-written sentence on the paper (classic card: wraps text, takes measure values)."""
    p.add(vname, "card", x, y, w, h, roles={"Values": [m]},
          objects={"labels": obj(color=tone, fontSize=size, fontFamily=font), "categoryLabels": obj(show=False),
                   "wordWrap": obj(show=True)},
          vco=quiet())


def bars(p, vname, vtype, cat, val, x, y, w, h, title, subtitle=None, sort=None, color_measure="Color Rate Bar",
         tooltip=False, alt=None):
    objects = {
        "dataPoint": obj(ALL_POINTS, fill=f"C:{color_measure}"),
        "labels": obj(show=True, color=INK, fontFamily=FONT, fontSize=9.0),
        "valueAxis": obj(show=False, gridlineShow=False),
        "categoryAxis": obj(show=True, labelColor=SLATE, fontFamily=FONT, fontSize=9.0, showAxisTitle=False,
                            gridlineShow=False),
        "legend": obj(show=False),
        "layout": obj(clusteredGapSize=0),
    }
    vco = chart_title(title, subtitle)
    if tooltip:
        vco["visualTooltip"] = obj(show=True, type="Canvas", section=TT_PAGE)
    p.add(vname, vtype, x, y, w, h, roles={"Category": [cat], "Y": [val]},
          objects=objects, vco=vco, sort=sort, alt=alt)


# ================================================================ Page 1: Who leaves
p1 = Page(*PAGES[0])
header(p1, "1,470 employees, IBM HR sample data")
x = 0
for i, (f, lbl) in enumerate([("Department", "Department"), ("Gender", "Gender"), ("Job Level", "Job level"),
                              ("Age Band", "Age band"), ("Overtime Status", "Overtime")]):
    x = dropdown(p1, i, f, lbl)
reset_button(p1, x + 16)

sentence(p1, "hero_headline", "M:Headline People", M - 6, 140, LEFT_W, 44, size=22.0, font=FONT_SEMI)
sentence(p1, "hero_note", "M:Headline Note", M - 6, 182, LEFT_W, 28, size=10.0, tone=MUTED)
p1.add("hero_dots", "tableEx", M, 212, LEFT_W, 456, roles={"Values": ["M:Dot Grid SVG"]}, names={"M:Dot Grid SVG": " "},
       objects={"grid": obj(imageHeight=440, imageWidth=526, gridHorizontal=False, gridVertical=False, rowPadding=0,
                            outlineColor=PAPER, outlineWeight=0, textSize=1),
                "columnHeaders": obj(fontColor=PAPER, backColor=PAPER, fontSize=1.0, outlineStyle=0),
                "values": obj(backColorPrimary=PAPER, backColorSecondary=PAPER, outlineStyle=0),
                "total": obj(totals=False)},
       vco=quiet(), alt="Dot grid: one dot per employee, grouped by department. Raspberry dots left, grey dots stayed, "
                        "faded dots are outside the current filter.")
p1.add("hero_legend", "textbox", M - 6, 668, LEFT_W, 28, objects={"general": [{"properties": {"paragraphs": [
    {"textRuns": [{"value": "● ", "textStyle": {"fontSize": "12pt", "color": LEAVER}},
                  {"value": "Left      ", "textStyle": {"fontFamily": FONT, "fontSize": "9pt", "color": SLATE}},
                  {"value": "● ", "textStyle": {"fontSize": "12pt", "color": STAYED}},
                  {"value": "Stayed      ", "textStyle": {"fontFamily": FONT, "fontSize": "9pt", "color": SLATE}},
                  {"value": "● ", "textStyle": {"fontSize": "12pt", "color": LINE}},
                  {"value": "Outside the current filters", "textStyle": {"fontFamily": FONT, "fontSize": "9pt", "color": SLATE}}]}]}}]},
       vco=quiet())

bars(p1, "who_role", "clusteredBarChart", "JobRole", "M:Attrition Rate", RX, 140, RW, 264, "M:Title Role",
     "Attrition rate by job role. Hover a bar for the full picture.", sort=("M:Attrition Rate", "Descending"),
     tooltip=True, alt="Attrition rate by job role, highest first")
bars(p1, "who_age", "clusteredColumnChart", "Age Band", "M:Attrition Rate", RX, 424, HALF, 272, "M:Title Age",
     "Attrition rate by age", sort=("Age Band", "Ascending"), alt="Attrition rate by age band")
bars(p1, "who_tenure", "clusteredColumnChart", "Tenure Band", "M:Attrition Rate", RX + HALF + G, 424, HALF, 272,
     "M:Title Tenure", "Attrition rate by years at the company", sort=("Tenure Band", "Ascending"),
     alt="Attrition rate by years at the company")

# ================================================================ Page 2: Why they leave
p2 = Page(*PAGES[1])
header(p2, "Overtime, satisfaction, travel and stock options")
x = 0
for i, (f, lbl) in enumerate([("Department", "Department"), ("Gender", "Gender"), ("Age Band", "Age band")]):
    x = dropdown(p2, i, f, lbl)
reset_button(p2, x + 16)
# Metric switch: a segmented control (button slicer) with rest / hover / selected states
SEG_W = 372
p2.add("why_track", "shape", W - M - SEG_W, 72, SEG_W, 52,
       objects={"shape": obj(tileShape="rectangleRoundedByPixel", rectangleRoundedCurve=10),
                "fill": obj(show=True) + state("default", fillColor=TRACK, transparency=0.0),
                   "outline": obj(show=False) + state("default", show=False)},
       vco=quiet())
p2.add("why_metric", "advancedSlicerVisual", W - M - SEG_W + 4, 76, SEG_W - 8, 44,
       roles={"Values": ["Metric Selector.Metric"]},
       objects={
           "layout": obj(columnCount=3, rowCount=1, cellPadding=4, orientation=0, maxTiles=3),
           "selection": obj(singleSelect=True, strictSingleSelect=True),
           "actionState": obj(IsButtonsAdvanced=True),
           "padding": state("default", paddingSelection="Narrow"),
           "shapeCustomRectangle": obj(tileShape="rectangleRoundedByPixel", rectangleRoundedCurve=8),
           "fillCustom": obj(show=True) + state("default", fillColor=TRACK, transparency=0.0)
                         + state("hover", fillColor="#E2E4DE", transparency=0.0)
                         + state("press", fillColor=LINE, transparency=0.0)
                         + state("selected", fillColor=SURFACE, transparency=0.0),
           "value": state("default", fontColor=MUTED, fontFamily=FONT_SEMI, fontSize=10.0, horizontalAlignment="center")
                    + state("hover", fontColor=INK) + state("selected", fontColor=INK),
           "outline": state("default", show=False) + state("selected", show=True, lineColor=LINE, weight=1.0),
           "label": state("default", show=False),
           "selectionIcon": state("default", show=False),
           "general": default_filter("Metric Selector", "Metric", "'Attrition Rate'"),
       },
       vco=quiet(), sort=("Metric Selector.Metric", "Ascending"), alt="Metric shown in the four driver charts")

fx = M
for vname, m, lbl, tone in [("why_ot", "M:Attrition Rate (Overtime)", "With overtime", LEAVER),
                            ("why_not", "M:Attrition Rate (No Overtime)", "Without overtime", INK),
                            ("why_mult", "M:Overtime Risk Multiple", "Overtime risk", LEAVER)]:
    figure(p2, vname, m, lbl, fx, 140, tone=tone)
    fx += 176 + 16
p2.add("why_matrix", "pivotTable", M, 236, LEFT_W, 460,
       roles={"Rows": ["Job Level"], "Columns": ["Overtime Status"], "Values": ["M:Attrition Rate"]},
       names={"M:Attrition Rate": "Attrition rate"},
       objects={
           "values": [{"properties": props(fontSize=16.0, fontFamily=FONT_SEMI, bandedRowHeaders=False, backColorPrimary=PAPER, backColorSecondary=PAPER)},
                      {"properties": {"backColor": {"solid": {"color": measure("Color Heat")}},
                                      "fontColor": {"solid": {"color": measure("Color Heat Text")}}},
                       "selector": {**ALL_POINTS, "metadata": "_Measures.Attrition Rate"}}],
           "columnHeaders": obj(fontSize=11.0, fontFamily=FONT_SEMI, fontColor=SLATE, backColor=PAPER, alignment="Center",
                                outlineStyle=0),
           "rowHeaders": obj(fontSize=11.0, fontFamily=FONT_SEMI, fontColor=INK, backColor=PAPER, outlineStyle=0),
           "grid": obj(gridHorizontal=True, gridHorizontalColor=PAPER, gridHorizontalWeight=4,
                       gridVertical=True, gridVerticalColor=PAPER, gridVerticalWeight=4, rowPadding=16,
                       outlineColor=PAPER, outlineWeight=0),
           "columnFormatting": [{"properties": props(alignment="Center"),
                                 "selector": {"metadata": "_Measures.Attrition Rate"}}],
           "subTotals": obj(rowSubtotals=False, columnSubtotals=False),
           "columnWidth": [{"properties": props(value=170.0), "selector": {"metadata": "_Measures.Attrition Rate"}}],
           "total": obj(applyToHeaders=False),
       },
       vco=chart_title("M:Title Matrix", "Attrition rate by job level and overtime. Darker = more people leave."),
       sort=("Job Level", "Ascending"), alt="Heat matrix: attrition rate by job level and overtime")

SMV = "M:Selected Metric"
for vname, vtype, cat, ttl, sub, sx, sy, sort in [
    ("why_jobsat", "clusteredColumnChart", "Job Satisfaction", "M:Title Job Satisfaction", "Job satisfaction", RX, 140, ("Job Satisfaction", "Ascending")),
    ("why_wlb", "clusteredColumnChart", "Work-Life Balance", "M:Title Work-Life", "Work-life balance", RX + HALF + G, 140, ("Work-Life Balance", "Ascending")),
    ("why_travel", "clusteredBarChart", "BusinessTravel", "M:Title Travel", "Business travel", RX, 424, (SMV, "Descending")),
    ("why_stock", "clusteredColumnChart", "Stock Options", "M:Title Stock", "Stock option level", RX + HALF + G, 424, ("Stock Options", "Ascending")),
]:
    bars(p2, vname, vtype, cat, SMV, sx, sy, HALF, 272, ttl, None, sort=sort, color_measure="Color Metric Bar",
         alt=f"{sub}: the metric chosen in the switch")
    p2.visuals[-1]["visual"]["visualContainerObjects"]["subTitle"] = obj(
        show=True, text="M:Subtitle Metric", fontFamily=FONT, fontSize=9.0, fontColor=MUTED, alignment="left")

# ================================================================ Page 3: What it costs
p3 = Page(*PAGES[2])
header(p3, "Pay, pay equity and the payback of a raise")
x = 0
for i, (f, lbl) in enumerate([("Department", "Department"), ("Gender", "Gender"), ("Job Level", "Job level")]):
    x = dropdown(p3, i, f, lbl)


def slider(p, vname, field, label, sx, default):
    p.add(vname, "slicer", sx, 72, 220, 52, roles={"Values": [field]},
          objects={"data": obj(mode="Single", numericStart=float(default.rstrip("D"))),
                   "header": obj(show=True, text=label, fontColor=MUTED, fontFamily=FONT, textSize=9.0),
                   "items": obj(fontColor=INK, fontFamily=FONT_SEMI, textSize=10.0),
                   "slider": obj(show=True, color=KEPT, handleFillColor=KEPT, handleBorderColor=SURFACE),
                   "general": default_filter(*field.split("."), default, single_value=True)},
          vco={**quiet(), "background": obj(show=True, color=SURFACE, transparency=0.0),
               "border": obj(show=True, color=LINE, radius=8.0, width=1.0),
               "padding": obj(top=4.0, bottom=4.0, left=10.0, right=10.0)}, alt=label)


slider(p3, "f_raise", "Raise %.Raise %", "Raise for people who stayed", x + 12, "0.1D")
slider(p3, "f_repl", "Replacement Cost %.Replacement Cost %", "Cost to replace a leaver", x + 12 + 232, "0.5D")
reset_button(p3, x + 12 + 464 + 4)

sentence(p3, "cost_hero", "M:Hero Raise", M - 6, 140, LEFT_W, 112, size=17.0, font=FONT_SEMI)
fx = M
for vname, m, lbl, tone, units in [("cost_attr", "M:Attrition Cost (Est.)", "Yearly cost of attrition", LEAVER, 1000000),
                                   ("cost_raise", "M:Raise Cost (Annual)", "Yearly cost of the raise", KEPT, 1000000),
                                   ("cost_be", "M:Break-even Leavers", "Departures to prevent", INK, None)]:
    figure(p3, vname, m, lbl, fx, 264, w=176, tone=tone, units=units)
    fx += 176 + 16
p3.add("cost_levels", "clusteredBarChart", M, 360, LEFT_W, 336,
       roles={"Category": ["Job Level"], "Y": ["M:Leavers", "M:Break-even Leavers"]},
       names={"M:Leavers": "People who left", "M:Break-even Leavers": "Departures the raise must prevent"},
       objects={"dataPoint": obj({"metadata": "_Measures.Leavers"}, fill=LEAVER)
                             + obj({"metadata": "_Measures.Break-even Leavers"}, fill=KEPT),
                "labels": obj(show=True, color=INK, fontFamily=FONT, fontSize=9.0),
                "valueAxis": obj(show=False, gridlineShow=False),
                "categoryAxis": obj(show=True, labelColor=SLATE, fontFamily=FONT, fontSize=9.0, showAxisTitle=False),
                "legend": obj(show=True, position="Top", showTitle=False, fontFamily=FONT, fontSize=9.0, labelColor=SLATE),
                "layout": obj(clusteredGapOverlaps=0, clusteredGapSize=2)},
       vco=chart_title("M:Title Break-even", "Where the teal bar is shorter, the raise pays for itself"),
       sort=("Job Level", "Ascending"), alt="Leavers against break-even departures, by job level")

p3.add("cost_gender", "clusteredBarChart", RX, 140, RW, 330,
       roles={"Category": ["JobRole"], "Y": ["M:Avg Monthly Income"], "Series": ["Gender"]},
       names={"M:Avg Monthly Income": "Average monthly income"},
       objects={"dataPoint": obj(series_selector("Gender", "Female"), fill=FEMALE)
                             + obj(series_selector("Gender", "Male"), fill=MALE),
                "labels": obj(show=False),
                "valueAxis": obj(show=True, gridlineShow=False, labelColor=MUTED, fontSize=8.0, showAxisTitle=False),
                "categoryAxis": obj(show=True, labelColor=SLATE, fontFamily=FONT, fontSize=9.0, showAxisTitle=False),
                "legend": obj(show=True, position="Top", showTitle=False, fontFamily=FONT, fontSize=9.0, labelColor=SLATE),
                "layout": obj(clusteredGapOverlaps=0, clusteredGapSize=2)},
       vco=chart_title("M:Title Gender Pay", "Average monthly income by role, women and men"),
       sort=("M:Avg Monthly Income", "Descending"), alt="Average monthly income by role and gender")
p3.add("cost_scatter", "scatterChart", RX, 480, RW, 216,
       roles={"Category": ["JobRole"], "X": ["M:Avg Monthly Income"], "Y": ["M:Attrition Rate"], "Size": ["M:Employees"]},
       names={"M:Avg Monthly Income": "Average monthly income", "M:Attrition Rate": "Attrition rate"},
       objects={"dataPoint": obj(fill=LEAVER),
                "categoryLabels": obj(show=False),
                "categoryAxis": obj(show=True, showAxisTitle=True, labelColor=MUTED, fontSize=8.0, gridlineShow=False),
                "valueAxis": obj(show=True, showAxisTitle=True, labelColor=MUTED, fontSize=8.0, gridlineShow=False,
                                 start=0.0, end=0.5),  # fixed 0-50% so the 39.8% bubble is not clipped
                "legend": obj(show=False)},
       vco={**chart_title("Lower-paid roles lose more people", "Each bubble is a role, sized by headcount. Hover one to see which."),
            "visualTooltip": obj(show=True, type="Canvas", section=TT_PAGE)},
       alt="Scatter of average income against attrition rate per role")

# ================================================================ Tooltip page (grows out of role bars and bubbles)
tt = Page(TT_PAGE, "Role tooltip", 320, 200)
sentence(tt, "tt_name", "M:Tooltip Role", 6, 8, 308, 32, size=13.0, font=FONT_SEMI)
figure(tt, "tt_rate", "M:Attrition Rate", "Attrition rate", 12, 44, w=140, h=72, tone=LEAVER, size=18.0)
figure(tt, "tt_ot", "M:Overtime Share", "Work overtime", 164, 44, w=140, h=72, size=18.0)
figure(tt, "tt_pay", "M:Avg Monthly Income", "Avg monthly income", 12, 120, w=140, h=72, size=18.0)
sentence(tt, "tt_left", "M:Tooltip Leavers", 158, 150, 156, 28, size=10.0, tone=SLATE)

# ---------------------------------------------------------------- write
RD = f"{RP}/definition"
write(f"{NAME}.pbip", {"$schema": SCH + "pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
                       "artifacts": [{"report": {"path": RP}}], "settings": {"enableAutoRecovery": True}})
write(f"{RP}/definition.pbir", {"$schema": SCH + "item/report/definitionProperties/2.0.0/schema.json",
                                "version": "4.0", "datasetReference": {"byPath": {"path": f"../{SM}"}}})
write(f"{RD}/version.json", {"$schema": SCH + "item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
write(f"{RD}/report.json", {
    "$schema": SCH + "item/report/definition/report/3.0.0/schema.json",
    "themeCollection": {"customTheme": {"name": "HRPaper.json", "type": "RegisteredResources",
                                        "reportVersionAtImport": {"visual": "2.4.0", "report": "3.0.0", "page": "2.0.0"}}},
    "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                          "items": [{"name": "HRPaper.json", "path": "HRPaper.json", "type": "CustomTheme"}]}],
    "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True,
                 "allowChangeFilterTypes": True, "useEnhancedTooltips": True},
})
all_pages = [p1, p2, p3, tt]
write(f"{RD}/pages/pages.json", {"$schema": SCH + "item/report/definition/pagesMetadata/1.0.0/schema.json",
                                 "pageOrder": [p.name for p in all_pages], "activePageName": p1.name})
for pg in all_pages:
    page = {"$schema": SCH + "item/report/definition/page/2.0.0/schema.json",
            "name": pg.name, "displayName": pg.display, "displayOption": "FitToPage",
            "height": pg.height, "width": pg.width,
            "objects": {"background": obj(color=PAPER, transparency=0.0),
                        "outspace": obj(color=PAPER, transparency=0.0)}}
    if pg is tt:
        page.update(displayOption="ActualSize", visibility="HiddenInViewMode", type="Tooltip",
                    pageBinding={"name": "role_tooltip", "type": "Tooltip"})
        page["objects"]["background"] = obj(color=SURFACE, transparency=0.0)
    write(f"{RD}/pages/{pg.name}/page.json", page)
    for v in pg.visuals:
        write(f"{RD}/pages/{pg.name}/visuals/{v['name']}/visual.json", v)

write(f"{RP}/StaticResources/RegisteredResources/HRPaper.json", {
    "name": "HR Paper",
    "dataColors": [LEAVER, KEPT, STAYED, FEMALE, MALE, SLATE, "#7A5CC2", "#D9A21B"],
    "background": SURFACE, "foreground": INK, "tableAccent": LEAVER,
    "good": "#2E9E6A", "neutral": "#D9A21B", "bad": LEAVER,
    "textClasses": {
        "title": {"fontFace": FONT_SEMI, "fontSize": 12, "color": INK},
        "label": {"fontFace": FONT, "fontSize": 9, "color": SLATE},
        "callout": {"fontFace": FONT_SEMI, "fontSize": 26, "color": INK},
        "header": {"fontFace": FONT_SEMI, "fontSize": 11, "color": INK},
    },
    "visualStyles": {
        "*": {"*": {
            "background": [{"show": False}], "border": [{"show": False}], "dropShadow": [{"show": False}],
            "visualTooltip": [{"background": {"solid": {"color": SURFACE}}, "titleFontColor": {"solid": {"color": MUTED}},
                               "valueFontColor": {"solid": {"color": INK}}, "fontFamily": FONT}],
        }},
        "page": {"*": {"background": [{"color": {"solid": {"color": PAPER}}, "transparency": 0}],
                       "outspace": [{"color": {"solid": {"color": PAPER}}}]}},
    },
})
print("pages:", {pg.display: len(pg.visuals) for pg in all_pages})

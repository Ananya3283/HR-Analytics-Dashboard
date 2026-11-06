"""Generate the HR-Analytics Power BI Project (PBIP: TMDL model + PBIR report)."""
import json, os, shutil, sys

REPO = sys.argv[1]
NAME = "HR-Analytics"
SM, RP = f"{NAME}.SemanticModel", f"{NAME}.Report"
DATA_FOLDER = os.path.join(REPO, "data") + "\\"
SCH = "https://developer.microsoft.com/json-schemas/fabric/"

# Palette shared with the web version (validated with the dataviz palette checker)
NAVY, INDIGO, ORANGE, INK, MUTED, BG, LINE = "#172026", "#C8325B", "#C8325B", "#172026", "#5D6B75", "#F7F7F4", "#DCDED8"
TEAL, SLATE, NAV_OFF = "#00829B", "#46535D", "#2A3640"
LEAVER_KPIS = {"M:Leavers", "M:Attrition Rate", "M:Attrition Rate (Overtime)", "M:Attrition Rate (First 2 Years)", "M:Attrition Cost (Est.)"}
KEPT_KPIS = {"M:Raise Cost (Annual)", "M:Break-even Leavers"}

# Replace only the definitions; keep Power BI's .pbi folders (data cache, local settings)
for d in (f"{SM}/definition", f"{RP}/definition", f"{RP}/StaticResources"):
    shutil.rmtree(os.path.join(REPO, d), ignore_errors=True)


def write(rel, content):
    p = os.path.join(REPO, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if not isinstance(content, str):
        content = json.dumps(content, indent=2, ensure_ascii=False)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.rstrip("\n") + "\n")


# ---------------------------------------------------------------- project files
write(f"{NAME}.pbip", {
    "$schema": SCH + "pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0",
    "artifacts": [{"report": {"path": RP}}],
    "settings": {"enableAutoRecovery": True},
})
write(f"{SM}/definition.pbism", {
    "$schema": SCH + "item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "4.2", "settings": {}})
write(f"{RP}/definition.pbir", {
    "$schema": SCH + "item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0", "datasetReference": {"byPath": {"path": f"../{SM}"}}})

# ---------------------------------------------------------------- semantic model (TMDL)
T = "\t"


def q(name):
    """Quote a TMDL object name when needed."""
    return name if name.replace("_", "").isalnum() else "'" + name.replace("'", "''") + "'"


def block(text, depth):
    return "\n".join(T * depth + line if line.strip() else "" for line in text.strip("\n").split("\n"))


write(f"{SM}/definition/database.tmdl", "database\n\tcompatibilityLevel: 1601\n")

TABLES = ["Employees", "_Measures", "Metric Selector", "Raise %", "Replacement Cost %"]
write(f"{SM}/definition/model.tmdl", "\n".join([
    "model Model",
    "\tculture: en-US",
    "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
    "\tdiscourageImplicitMeasures",
    "\tsourceQueryCulture: en-US",
    "",
    '\tannotation PBI_QueryOrder = ["DataFolder","Employees"]',
    "",
    *[f"ref table {q(t)}" for t in TABLES],
]))
write(f"{SM}/definition/expressions.tmdl",
      f'expression DataFolder = "{DATA_FOLDER}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
      "\tannotation PBI_ResultType = Text\n")

# Employees: (name, dataType, summarizeBy, formatString, sortByColumn, hidden)
INT, STR = "int64", "string"
emp_cols = [
    ("EmployeeNumber", INT, "none", "0", None, False),
    ("Age", INT, "none", "0", None, False),
    ("Attrition", STR, None, None, None, False),
    ("Attrition Flag", INT, "sum", "0", None, True),
    ("BusinessTravel", STR, None, None, None, False),
    ("Department", STR, None, None, None, False),
    ("DistanceFromHome", INT, "none", "0", None, False),
    ("Education", INT, "none", "0", None, True),
    ("Education Level", STR, None, None, "Education", False),
    ("EducationField", STR, None, None, None, False),
    ("EnvironmentSatisfaction", INT, "none", "0", None, True),
    ("Environment Satisfaction", STR, None, None, "EnvironmentSatisfaction", False),
    ("Gender", STR, None, None, None, False),
    ("JobInvolvement", INT, "none", "0", None, False),
    ("JobLevel", INT, "none", "0", None, True),
    ("Job Level", STR, None, None, "JobLevel", False),
    ("JobRole", STR, None, None, None, False),
    ("JobSatisfaction", INT, "none", "0", None, True),
    ("Job Satisfaction", STR, None, None, "JobSatisfaction", False),
    ("MaritalStatus", STR, None, None, None, False),
    ("MonthlyIncome", INT, "sum", "#,0", None, False),
    ("NumCompaniesWorked", INT, "none", "0", None, False),
    ("OverTime", STR, None, None, None, False),
    ("PercentSalaryHike", INT, "none", "0", None, False),
    ("PerformanceRating", INT, "none", "0", None, False),
    ("RelationshipSatisfaction", INT, "none", "0", None, False),
    ("StockOptionLevel", INT, "none", "0", None, True),
    ("Stock Options", STR, None, None, "StockOptionLevel", False),
    ("TotalWorkingYears", INT, "none", "0", None, False),
    ("TrainingTimesLastYear", INT, "none", "0", None, False),
    ("WorkLifeBalance", INT, "none", "0", None, True),
    ("Work-Life Balance", STR, None, None, "WorkLifeBalance", False),
    ("YearsAtCompany", INT, "none", "0", None, False),
    ("YearsInCurrentRole", INT, "none", "0", None, False),
    ("YearsSinceLastPromotion", INT, "none", "0", None, False),
    ("YearsWithCurrManager", INT, "none", "0", None, False),
    ("Age Band", STR, None, None, "Age Band Order", False),
    ("Age Band Order", INT, "none", "0", None, True),
    ("Tenure Band", STR, None, None, "Tenure Band Order", False),
    ("Tenure Band Order", INT, "none", "0", None, True),
    ("Income Band", STR, None, None, "Income Band Order", False),
    ("Income Band Order", INT, "none", "0", None, True),
    ("Overtime Status", STR, None, None, "Overtime Order", False),
    ("Overtime Order", INT, "none", "0", None, True),
    # Hero dot grid: pixel position of each employee in a 49-wide grid, one block per department
    ("Dot X", INT, "none", "0", None, True),
    ("Dot Y", INT, "none", "0", None, True),
    ("Dot Label Y", INT, "none", "0", None, True),
]

M_EMPLOYEES = r'''
let
    Source = Csv.Document(File.Contents(DataFolder & "HR.csv"), [Delimiter = ",", Columns = 35, Encoding = 65001, QuoteStyle = QuoteStyle.None]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // EmployeeCount, Over18 and StandardHours hold one value for every row; the three *Rate columns are undocumented
    Dropped = Table.RemoveColumns(Promoted, {"EmployeeCount", "Over18", "StandardHours", "DailyRate", "HourlyRate", "MonthlyRate"}),
    TextCols = {"Attrition", "BusinessTravel", "Department", "EducationField", "Gender", "JobRole", "MaritalStatus", "OverTime"},
    Typed = Table.TransformColumnTypes(Dropped,
        List.Transform(Table.ColumnNames(Dropped), each {_, if List.Contains(TextCols, _) then type text else Int64.Type})),
    CleanTravel = Table.ReplaceValue(Typed, "_", " ", Replacer.ReplaceText, {"BusinessTravel"}),
    Flag = Table.AddColumn(CleanTravel, "Attrition Flag", each if [Attrition] = "Yes" then 1 else 0, Int64.Type),
    // Code-to-label lookups from the IBM data dictionary
    EduLabel = Table.AddColumn(Flag, "Education Level", each {"Below College", "College", "Bachelor", "Master", "Doctor"}{[Education] - 1}, type text),
    EnvLabel = Table.AddColumn(EduLabel, "Environment Satisfaction", each {"Low", "Medium", "High", "Very High"}{[EnvironmentSatisfaction] - 1}, type text),
    JobSatLabel = Table.AddColumn(EnvLabel, "Job Satisfaction", each {"Low", "Medium", "High", "Very High"}{[JobSatisfaction] - 1}, type text),
    WlbLabel = Table.AddColumn(JobSatLabel, "Work-Life Balance", each {"Bad", "Good", "Better", "Best"}{[WorkLifeBalance] - 1}, type text),
    LevelLabel = Table.AddColumn(WlbLabel, "Job Level", each "Level " & Text.From([JobLevel]), type text),
    StockLabel = Table.AddColumn(LevelLabel, "Stock Options", each "Level " & Text.From([StockOptionLevel]), type text),
    // Bands: each label gets an order column so visuals sort 18-25, 26-35 ... instead of alphabetically
    AgeOrder = Table.AddColumn(StockLabel, "Age Band Order", each if [Age] <= 25 then 1 else if [Age] <= 35 then 2 else if [Age] <= 45 then 3 else if [Age] <= 55 then 4 else 5, Int64.Type),
    AgeBand = Table.AddColumn(AgeOrder, "Age Band", each {"18-25", "26-35", "36-45", "46-55", "56+"}{[Age Band Order] - 1}, type text),
    TenureOrder = Table.AddColumn(AgeBand, "Tenure Band Order", each if [YearsAtCompany] <= 2 then 1 else if [YearsAtCompany] <= 5 then 2 else if [YearsAtCompany] <= 10 then 3 else 4, Int64.Type),
    TenureBand = Table.AddColumn(TenureOrder, "Tenure Band", each {"0-2 yrs", "3-5 yrs", "6-10 yrs", "10+ yrs"}{[Tenure Band Order] - 1}, type text),
    IncomeOrder = Table.AddColumn(TenureBand, "Income Band Order", each if [MonthlyIncome] < 3000 then 1 else if [MonthlyIncome] < 5000 then 2 else if [MonthlyIncome] < 10000 then 3 else 4, Int64.Type),
    IncomeBand = Table.AddColumn(IncomeOrder, "Income Band", each {"Under 3K", "3K-5K", "5K-10K", "10K+"}{[Income Band Order] - 1}, type text),
    OtOrder = Table.AddColumn(IncomeBand, "Overtime Order", each if [OverTime] = "Yes" then 2 else 1, Int64.Type),
    OtStatus = Table.AddColumn(OtOrder, "Overtime Status", each if [OverTime] = "Yes" then "Overtime" else "No overtime", type text),
    // Dot grid: each department is a block of 49-dot rows, leavers first; 22px label band above, 12px gap below
    Depts = List.Sort(List.Distinct(OtStatus[Department])),
    DeptRows = List.Transform(Depts, (d) => Number.RoundUp(Table.RowCount(Table.SelectRows(OtStatus, each [Department] = d)) / 49)),
    Tops = List.Accumulate(List.Positions(Depts), {}, (acc, i) => acc & {if i = 0 then 0 else List.Last(acc) + 22 + DeptRows{i - 1} * 10 + 12}),
    Grouped = Table.Group(OtStatus, {"Department"}, {{"G", each Table.AddIndexColumn(
        Table.Sort(_, {{"Attrition Flag", Order.Descending}, {"EmployeeNumber", Order.Ascending}}), "Dot Index", 0, 1, Int64.Type)}}),
    Combined = Table.Combine(Grouped[G]),
    LabelY = Table.AddColumn(Combined, "Dot Label Y", each Tops{List.PositionOf(Depts, [Department])} + 14, Int64.Type),
    DotX = Table.AddColumn(LabelY, "Dot X", each 5 + Number.Mod([Dot Index], 49) * 10, Int64.Type),
    DotY = Table.AddColumn(DotX, "Dot Y", each [Dot Label Y] + 13 + Number.IntegerDivide([Dot Index], 49) * 10, Int64.Type),
    Final = Table.RemoveColumns(DotY, {"Dot Index"})
in
    Final
'''


def column_tmdl(name, dtype, summ, fmt, sort_by, hidden, source=None, calc=False):
    lines = [f"\tcolumn {q(name)}", f"\t\tdataType: {dtype}"]
    if fmt: lines.append(f"\t\tformatString: {fmt}")
    if hidden: lines.append("\t\tisHidden")
    if calc: lines += ["\t\tisDataTypeInferred", "\t\tisNameInferred"]
    lines.append(f"\t\tsummarizeBy: {summ or 'none'}")
    lines.append(f"\t\tsourceColumn: {source or name}")
    if sort_by: lines.append(f"\t\tsortByColumn: {q(sort_by)}")
    return "\n".join(lines)


emp = ["table Employees", ""]
for c in emp_cols:
    emp += [column_tmdl(*c), ""]
emp += ["\tpartition Employees = m", "\t\tmode: import", "\t\tsource =", block(M_EMPLOYEES, 3)]
write(f"{SM}/definition/tables/Employees.tmdl", "\n".join(emp))


def calc_table(name, cols, dax, hidden_table=False):
    out = [f"table {q(name)}"] + (["\tisHidden"] if hidden_table else []) + [""]
    for c in cols:
        out += [column_tmdl(c[0], c[1], "none", c[2], c[3] if len(c) > 3 else None, c[4] if len(c) > 4 else False,
                            source=f"[{c[0]}]", calc=True), ""]
    out += [f"\tpartition {q(name)} = calculated", "\t\tmode: import", "\t\tsource =", block(dax, 3)]
    return "\n".join(out)


write(f"{SM}/definition/tables/Metric Selector.tmdl", calc_table(
    "Metric Selector",
    [("Metric", STR, None, "Metric Order"), ("Metric Order", INT, "0", None, True)],
    'DATATABLE (\n    "Metric", STRING, "Metric Order", INTEGER,\n    { { "Attrition Rate", 1 }, { "Leavers", 2 }, { "Headcount", 3 } }\n)'))
write(f"{SM}/definition/tables/Raise %.tmdl", calc_table(
    "Raise %", [("Raise %", "double", "0.0%")],
    # Fine steps so the story report can drive it with a slider; SELECTEDVALUE still defaults to 10%
    'SELECTCOLUMNS ( GENERATESERIES ( 0, 0.2, 0.005 ), "Raise %", ROUND ( [Value], 3 ) )'))
write(f"{SM}/definition/tables/Replacement Cost %.tmdl", calc_table(
    "Replacement Cost %", [("Replacement Cost %", "double", "0%")],
    'SELECTCOLUMNS ( GENERATESERIES ( 0.25, 1.5, 0.05 ), "Replacement Cost %", ROUND ( [Value], 2 ) )'))

# Measures: (name, folder, formatString, DAX, description)
MEASURES = [
    ("Employees", "1 KPIs", "#,0", "COUNTROWS ( Employees )", "Headcount in the current filter context (leavers included)."),
    ("Leavers", "1 KPIs", "#,0", 'CALCULATE ( COUNTROWS ( Employees ), Employees[Attrition] = "Yes" )', "Employees who left."),
    ("Active Employees", "1 KPIs", "#,0", 'CALCULATE ( COUNTROWS ( Employees ), Employees[Attrition] = "No" )', "Employees still at the company."),
    ("Attrition Rate", "1 KPIs", "0.0%", "DIVIDE ( [Leavers], [Employees] )", "Leavers divided by headcount."),
    ("Avg Monthly Income", "1 KPIs", "#,0", "AVERAGE ( Employees[MonthlyIncome] )", None),
    ("Avg Age", "1 KPIs", "0.0", "AVERAGE ( Employees[Age] )", None),
    ("Avg Tenure (Years)", "1 KPIs", "0.0", "AVERAGE ( Employees[YearsAtCompany] )", None),

    ("Attrition Rate (Overtime)", "2 Drivers", "0.0%", 'CALCULATE ( [Attrition Rate], Employees[OverTime] = "Yes" )', None),
    ("Attrition Rate (No Overtime)", "2 Drivers", "0.0%", 'CALCULATE ( [Attrition Rate], Employees[OverTime] = "No" )', None),
    ("Overtime Risk Multiple", "2 Drivers", '0.0"x"', "DIVIDE ( [Attrition Rate (Overtime)], [Attrition Rate (No Overtime)] )",
     "How many times more often overtime staff leave than staff without overtime."),
    ("Attrition Rate (First 2 Years)", "2 Drivers", "0.0%", "CALCULATE ( [Attrition Rate], Employees[YearsAtCompany] <= 2 )", None),
    ("Selected Metric", "2 Drivers", None, '''
SWITCH (
    SELECTEDVALUE ( 'Metric Selector'[Metric], "Attrition Rate" ),
    "Leavers", [Leavers],
    "Headcount", [Employees],
    [Attrition Rate]
)''', "Driven by the Metric Selector slicer on the Attrition Drivers page."),

    ("Monthly Payroll", "3 Compensation", "#,0", "SUM ( Employees[MonthlyIncome] )", None),
    ("Annual Payroll", "3 Compensation", "#,0", "[Monthly Payroll] * 12", None),
    ("Avg Income (Male)", "3 Compensation", "#,0", 'CALCULATE ( [Avg Monthly Income], Employees[Gender] = "Male" )', None),
    ("Avg Income (Female)", "3 Compensation", "#,0", 'CALCULATE ( [Avg Monthly Income], Employees[Gender] = "Female" )', None),
    ("Gender Pay Gap %", "3 Compensation", "0.0%", "DIVIDE ( [Avg Income (Male)] - [Avg Income (Female)], [Avg Income (Male)] )",
     "Positive = men paid more on average, negative = women paid more."),

    ("Raise % Value", "4 What-if", "0.0%", "SELECTEDVALUE ( 'Raise %'[Raise %], 0.10 )", "Raise from the slicer; 10% when nothing or several values are selected."),
    ("Replacement Cost % Value", "4 What-if", "0%", "SELECTEDVALUE ( 'Replacement Cost %'[Replacement Cost %], 0.50 )",
     "Cost to replace a leaver as a share of their annual salary (assumption, default 50%)."),
    ("Attrition Cost (Est.)", "4 What-if", "#,0",
     'CALCULATE ( SUM ( Employees[MonthlyIncome] ), Employees[Attrition] = "Yes" ) * 12 * [Replacement Cost % Value]',
     "Annual salary of every leaver times the replacement-cost assumption."),
    ("Cost per Leaver", "4 What-if", "#,0", "DIVIDE ( [Attrition Cost (Est.)], [Leavers] )", None),
    ("Raise Cost (Annual)", "4 What-if", "#,0",
     'CALCULATE ( SUM ( Employees[MonthlyIncome] ), Employees[Attrition] = "No" ) * 12 * [Raise % Value]',
     "Yearly cost of giving the selected raise to every current employee in the filter context."),
    ("Projected Annual Payroll", "4 What-if", "#,0", "[Annual Payroll] + [Raise Cost (Annual)]", None),
    ("Break-even Leavers", "4 What-if", "#,0", "DIVIDE ( [Raise Cost (Annual)], [Cost per Leaver] )",
     "Leavers the raise must prevent each year to pay for itself."),
    ("Break-even % of Leavers", "4 What-if", "0%", "DIVIDE ( [Break-even Leavers], [Leavers] )",
     "Share of current leavers the raise must keep to pay for itself. Above 100% = it cannot pay back."),

    ("Insight Top Role", "5 Insights", None, '''
VAR Roles =
    FILTER (
        ADDCOLUMNS ( VALUES ( Employees[JobRole] ), "@Rate", [Attrition Rate], "@N", [Employees] ),
        [@N] >= 20
    )
VAR TopRole = TOPN ( 1, Roles, [@Rate], DESC )
RETURN
    IF (
        ISEMPTY ( Roles ),
        "Too few employees in this selection to rank roles",
        "Riskiest role: " & MAXX ( TopRole, Employees[JobRole] ) & " (" & FORMAT ( MAXX ( TopRole, [@Rate] ), "0.0%" ) & " leave)"
    )''', "Job role with the highest attrition rate among roles with 20+ employees."),
    ("Insight Overtime", "5 Insights", None, '''
IF (
    ISBLANK ( [Overtime Risk Multiple] ),
    "No overtime comparison in this selection",
    "Overtime staff leave " & FORMAT ( [Overtime Risk Multiple], "0.0" ) & "x as often ("
        & FORMAT ( [Attrition Rate (Overtime)], "0%" ) & " vs " & FORMAT ( [Attrition Rate (No Overtime)], "0%" ) & ")"
)''', None),
    ("Insight New Joiners", "5 Insights", None, '''
VAR EarlyLeavers = CALCULATE ( [Leavers], Employees[YearsAtCompany] <= 2 )
RETURN
    IF (
        [Leavers] > 0,
        FORMAT ( DIVIDE ( EarlyLeavers, [Leavers] ), "0%" ) & " of leavers quit within 2 years ("
            & FORMAT ( [Attrition Rate (First 2 Years)], "0%" ) & " early attrition)",
        "No leavers in this selection"
    )''', None),
    ("Insight Pay", "5 Insights", None, '''
VAR Low = CALCULATE ( [Attrition Rate], Employees[Income Band] = "Under 3K" )
VAR High = CALCULATE ( [Attrition Rate], Employees[Income Band] = "10K+" )
RETURN
    IF (
        ISBLANK ( Low ) || ISBLANK ( High ),
        "Pay comparison needs both low and high earners in the selection",
        "Under-3K earners leave at " & FORMAT ( Low, "0%" ) & " vs " & FORMAT ( High, "0%" ) & " for 10K+"
    )''', None),
    ("Insight Raise", "5 Insights", None, '''
IF (
    [Raise % Value] = 0 || [Leavers] = 0,
    "Pick a raise above 0% to see its payback",
    FORMAT ( [Raise % Value], "0.0%" ) & " raise costs " & FORMAT ( [Raise Cost (Annual)] / 1e6, "0.0" ) & "M/yr: "
        & IF (
            [Break-even Leavers] > [Leavers],
            "it needs " & FORMAT ( [Break-even Leavers], "#,0" ) & " fewer leavers to pay back, but only "
                & FORMAT ( [Leavers], "#,0" ) & " left",
            "it pays back if it keeps " & FORMAT ( [Break-even Leavers], "#,0" ) & " of "
                & FORMAT ( [Leavers], "#,0" ) & " leavers (" & FORMAT ( [Break-even % of Leavers], "0%" ) & ")"
        )
)''', "Plain-English payback of the selected raise."),
]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story_measures import STORY_MEASURES  # noqa: E402
MEASURES += STORY_MEASURES

SELECTED_METRIC_FORMAT = '''
SWITCH (
    SELECTEDVALUE ( 'Metric Selector'[Metric], "Attrition Rate" ),
    "Attrition Rate", "0.0%",
    "#,0"
)'''

mt = ["table _Measures", ""]  # "Measures" is a reserved table name in Power BI
for name, folder, fmt, dax, desc in MEASURES:
    if desc:
        mt.append(f"\t/// {desc}")
    if "\n" in dax.strip():
        mt += [f"\tmeasure {q(name)} =", block(dax, 3)]
    else:
        mt.append(f"\tmeasure {q(name)} = {dax}")
    if fmt:
        mt.append(f"\t\tformatString: {fmt}")
    mt.append(f"\t\tdisplayFolder: {folder}")
    if name == "Dot Grid SVG":
        mt.append("\t\tdataCategory: ImageUrl")
    if name == "Selected Metric":
        # child objects must follow the measure's plain properties
        mt += ["", "\t\tformatStringDefinition =", block(SELECTED_METRIC_FORMAT, 3)]
    mt.append("")
mt += [column_tmdl("Value", INT, "none", "0", None, True, source="[Value]", calc=True), "",
       "\tpartition _Measures = calculated", "\t\tmode: import", '\t\tsource = ROW ( "Value", 0 )']
write(f"{SM}/definition/tables/_Measures.tmdl", "\n".join(mt))

# ---------------------------------------------------------------- report (PBIR)
V_SCH = SCH + "item/report/definition/visualContainer/2.4.0/schema.json"


def lit(v):
    if isinstance(v, bool): s = "true" if v else "false"
    elif isinstance(v, int): s = f"{v}L"
    elif isinstance(v, float): s = f"{v}D"
    else: s = "'" + v.replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def color(hex_):
    return {"solid": {"color": lit(hex_)}}


def props(**kw):
    out = {}
    for k, v in kw.items():
        if isinstance(v, str) and v.startswith("#") and len(v) == 7:
            out[k] = color(v)
        elif isinstance(v, dict):
            out[k] = v
        else:
            out[k] = lit(v)
    return out


def obj(selector=None, **kw):
    o = {"properties": props(**kw)}
    if selector: o["selector"] = selector
    return [o]


def col(field):
    return ("Employees", field) if "." not in field else tuple(field.split(".", 1))


def field_ref(f):
    """'M:Attrition Rate' = measure, 'Table.Column' or 'Column' (Employees) = column."""
    if f.startswith("M:"):
        n = f[2:]
        return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": n}}, f"_Measures.{n}", n
    t, c = col(f)
    return {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}, f"{t}.{c}", c


def projections(fields, active_first=False):
    out = []
    for i, f in enumerate(fields):
        ref, qref, native = field_ref(f)
        p = {"field": ref, "queryRef": qref, "nativeQueryRef": native}
        if active_first and i == 0: p["active"] = True
        out.append(p)
    return {"projections": out}


class Page:
    def __init__(self, name, display):
        self.name, self.display, self.visuals = name, display, []

    def add(self, vname, vtype, x, y, w, h, roles=None, objects=None, vco=None, sort=None, extra=None):
        visual = {"visualType": vtype}
        if roles:
            qs = {role: projections(fs, active_first=(role == "Category")) for role, fs in roles.items()}
            visual["query"] = {"queryState": qs}
            if sort:
                f, direction = sort
                visual["query"]["sortDefinition"] = {
                    "sort": [{"field": field_ref(f)[0], "direction": direction}], "isDefaultSort": True}
        if objects: visual["objects"] = objects
        if vco: visual["visualContainerObjects"] = vco
        if roles and vtype not in ("slicer", "card", "multiRowCard"): visual["drillFilterOtherVisuals"] = True
        container = {"$schema": V_SCH, "name": vname,
                     "position": {"x": x, "y": y, "z": len(self.visuals) * 1000, "height": h, "width": w,
                                  "tabOrder": len(self.visuals) * 1000},
                     "visual": visual}
        if extra: container["visual"].update(extra)
        self.visuals.append(container)


def title(text):
    return {"title": obj(show=True, text=text)}


def no_title():
    return {"title": obj(show=False)}


PAGES = [("page_overview", "Overview"), ("page_drivers", "Attrition Drivers"), ("page_comp", "Compensation & What-If")]
W, H, M, G = 1280, 720, 16, 8


def header(p, subtitle):
    p.add("header_bar", "textbox", 0, 0, W, 60, objects={"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": "HR Analytics", "textStyle": {"fontWeight": "bold", "fontSize": "20pt", "color": "#FFFFFF"}},
                      {"value": "   " + subtitle, "textStyle": {"fontSize": "12pt", "color": "#AEB8BF"}}]}]}}]},
        vco={"background": obj(show=True, color=NAVY, transparency=0.0), "border": obj(show=False),
             "title": obj(show=False), "padding": obj(left=16.0, top=12.0)})
    bx = W - M - 3 * 168 + G
    for i, (pname, disp) in enumerate(PAGES):
        active = pname == p.name
        p.add(f"nav_{pname}", "actionButton", bx + i * 168, 12, 160, 36,
              # Buttons: the show switch has no selector; per-state styling sits under selector id "default"
              objects={
                  "icon": obj(show=False),
                  "text": obj(show=True) + obj({"id": "default"}, text=disp, fontColor=(NAVY if active else "#FFFFFF"),
                                               fontSize=11.0, bold=True),
                  "fill": obj(show=True) + obj({"id": "default"}, fillColor=("#FFFFFF" if active else NAV_OFF),
                                               transparency=0.0),
                  "outline": obj(show=True) + obj({"id": "default"}, lineColor="#FFFFFF", weight=1.0, roundEdge=8.0),
              },
              vco={"visualLink": obj(show=True, type="PageNavigation", navigationSection=pname),
                   "title": obj(show=False), "background": obj(show=False), "border": obj(show=False)})


def slicer(p, vname, field, x, w, label, single=False, sync=True):
    objects = {"data": obj(mode="Dropdown"), "header": obj(show=True, text=label, fontColor=INK, textSize=10.0),
               "items": obj(textSize=10.0)}
    if single:
        objects["selection"] = obj(singleSelect=True, selectAllCheckboxEnabled=False)
    extra = {"syncGroup": {"groupName": field, "fieldChanges": True, "filterChanges": True}} if sync else None
    p.add(vname, "slicer", x, 68, w, 52, roles={"Values": [field]}, objects=objects,
          vco={"title": obj(show=False), "padding": obj(top=2.0, bottom=2.0, left=8.0, right=8.0)}, extra=extra)


def kpis(p, items):
    n = len(items)
    w = (W - 2 * M - (n - 1) * G) / n
    for i, (m, label) in enumerate(items):
        p.add(f"kpi_{i}", "card", round(M + i * (w + G)), 128, round(w), 76, roles={"Values": [m]},
              objects={"labels": obj(color=(INDIGO if m in LEAVER_KPIS else TEAL if m in KEPT_KPIS else INK),
                                     fontSize=22.0, fontFamily="Segoe UI Semibold"),
                       "categoryLabels": obj(show=True, color=MUTED, fontSize=10.0)},
              vco={"background": obj(show=True, color="#FFFFFF", transparency=0.0), "title": obj(show=False),
                   "border": obj(show=False), "dropShadow": obj(show=False)})
        # Card category label shows the measure name; rename via the projection display name
        p.visuals[-1]["visual"]["query"]["queryState"]["Values"]["projections"][0]["displayName"] = label


ROW2_Y, ROW3_Y = 212, 466
ROW_H = 246
COLS3 = [(M, 404), (M + 404 + G, 420), (M + 404 + G + 420 + G, W - M - (M + 404 + G + 420 + G))]


def bar(p, vname, vtype, cat, val, x, w, y, h, ttl, series=None, sort=None, color=INDIGO):
    roles = {"Category": [cat], "Y": [val]}
    if series: roles["Series"] = [series]
    objects = {"labels": obj(show=True, fontSize=9.0, color=INK),
               "valueAxis": obj(show=False, gridlineShow=False),
               "categoryAxis": obj(show=True, fontSize=9.0, color=MUTED, showAxisTitle=False)}
    if not series:
        objects["dataPoint"] = obj(fill=color)
        objects["legend"] = obj(show=False)
    else:
        objects["legend"] = obj(show=True, position="Top", fontSize=9.0)
    p.add(vname, vtype, x, y, w, h, roles=roles, objects=objects, vco=title(ttl), sort=sort)


# ---------- Page 1: Overview
p1 = Page(*PAGES[0])
header(p1, "Workforce & attrition overview")
for i, (f, lbl) in enumerate([("Department", "Department"), ("Gender", "Gender"), ("Job Level", "Job level"),
                              ("Age Band", "Age band"), ("EducationField", "Education field")]):
    slicer(p1, f"slicer_{i}", f, M + i * 250, 242, lbl)
kpis(p1, [("M:Employees", "Employees"), ("M:Leavers", "Leavers"), ("M:Attrition Rate", "Attrition rate"),
          ("M:Avg Monthly Income", "Avg monthly income"), ("M:Avg Age", "Avg age"), ("M:Avg Tenure (Years)", "Avg tenure (yrs)")])
bar(p1, "attr_dept", "clusteredBarChart", "Department", "M:Attrition Rate", *COLS3[0], ROW2_Y, ROW_H,
    "Attrition rate by department", sort=("M:Attrition Rate", "Descending"))
bar(p1, "attr_role", "clusteredBarChart", "JobRole", "M:Attrition Rate", *COLS3[1], ROW2_Y, ROW_H,
    "Attrition rate by job role", sort=("M:Attrition Rate", "Descending"))
p1.add("gender_donut", "donutChart", *COLS3[2][:1], ROW2_Y, COLS3[2][1], ROW_H,
       roles={"Category": ["Gender"], "Y": ["M:Leavers"]},
       objects={"labels": obj(show=True, labelStyle="Category, percent of total", fontSize=9.0),
                "legend": obj(show=False), "slices": obj(innerRadiusRatio=60)},
       vco=title("Leavers by gender"))
bar(p1, "attr_age", "clusteredColumnChart", "Age Band", "M:Attrition Rate", *COLS3[0], ROW3_Y, ROW_H,
    "Attrition rate by age band", sort=("Age Band", "Ascending"))
bar(p1, "attr_tenure", "clusteredColumnChart", "Tenure Band", "M:Attrition Rate", *COLS3[1], ROW3_Y, ROW_H,
    "Attrition rate by years at company", sort=("Tenure Band", "Ascending"))
ix, iw = COLS3[2]
p1.add("insights_title", "textbox", ix, ROW3_Y, iw, 34, objects={"general": [{"properties": {"paragraphs": [
    {"textRuns": [{"value": "Key insights", "textStyle": {"fontWeight": "bold", "fontSize": "11pt", "color": INK}},
                  {"value": "  (update with filters)", "textStyle": {"fontSize": "9pt", "color": MUTED}}]}]}}]},
    vco={"title": obj(show=False)})
for i, m in enumerate(["Insight Top Role", "Insight Overtime", "Insight New Joiners", "Insight Pay"]):
    p1.add(f"insight_{i}", "card", ix, ROW3_Y + 38 + i * 52, iw, 48, roles={"Values": [f"M:{m}"]},
           objects={"labels": obj(color=NAVY, fontSize=10.0, fontFamily="Segoe UI Semibold"),
                    "categoryLabels": obj(show=False), "wordWrap": obj(show=True)},
           vco={"title": obj(show=False), "background": obj(show=True, color="#FFFFFF", transparency=0.0),
                "border": obj(show=True, color=ORANGE, radius=8.0)})

# ---------- Page 2: Attrition drivers
p2 = Page(*PAGES[1])
header(p2, "What drives people to leave")
for i, (f, lbl) in enumerate([("Department", "Department"), ("Gender", "Gender"), ("Job Level", "Job level"),
                              ("Age Band", "Age band")]):
    slicer(p2, f"slicer_{i}", f, M + i * 250, 242, lbl)
slicer(p2, "slicer_metric", "Metric Selector.Metric", M + 4 * 250, 242, "Metric shown in charts", single=True, sync=False)
kpis(p2, [("M:Attrition Rate", "Attrition rate"), ("M:Attrition Rate (Overtime)", "With overtime"),
          ("M:Attrition Rate (No Overtime)", "Without overtime"), ("M:Overtime Risk Multiple", "Overtime risk multiple"),
          ("M:Attrition Rate (First 2 Years)", "First 2 years"), ("M:Leavers", "Leavers")])
SM_ = "M:Selected Metric"
bar(p2, "drv_ot", "clusteredColumnChart", "OverTime", SM_, *COLS3[0], ROW2_Y, ROW_H, "By overtime", sort=("OverTime", "Descending"))
bar(p2, "drv_jobsat", "clusteredColumnChart", "Job Satisfaction", SM_, *COLS3[1], ROW2_Y, ROW_H, "By job satisfaction",
    sort=("Job Satisfaction", "Ascending"))
bar(p2, "drv_wlb", "clusteredColumnChart", "Work-Life Balance", SM_, *COLS3[2], ROW2_Y, ROW_H, "By work-life balance",
    sort=("Work-Life Balance", "Ascending"))
bar(p2, "drv_travel", "clusteredBarChart", "BusinessTravel", SM_, *COLS3[0], ROW3_Y, ROW_H, "By business travel",
    sort=(SM_, "Descending"))
bar(p2, "drv_stock", "clusteredColumnChart", "Stock Options", SM_, *COLS3[1], ROW3_Y, ROW_H, "By stock option level",
    sort=("Stock Options", "Ascending"))
p2.add("drv_matrix", "pivotTable", COLS3[2][0], ROW3_Y, COLS3[2][1], ROW_H,
       roles={"Rows": ["Job Level"], "Columns": ["OverTime"], "Values": ["M:Attrition Rate"]},
       objects={"values": obj(fontSize=10.0), "columnHeaders": obj(fontSize=10.0, bold=True),
                "rowHeaders": obj(fontSize=10.0)},
       vco=title("Attrition rate: job level x overtime"), sort=("Job Level", "Ascending"))

# ---------- Page 3: Compensation & what-if
p3 = Page(*PAGES[2])
header(p3, "Pay, pay equity and the cost of attrition")
for i, (f, lbl) in enumerate([("Department", "Department"), ("Gender", "Gender"), ("Job Level", "Job level")]):
    slicer(p3, f"slicer_{i}", f, M + i * 250, 242, lbl)
slicer(p3, "slicer_raise", "Raise %.Raise %", M + 3 * 250, 242, "What-if: raise for current staff", single=True, sync=False)
slicer(p3, "slicer_repl", "Replacement Cost %.Replacement Cost %", M + 4 * 250, 242,
       "Assumed replacement cost (% of salary)", single=True, sync=False)
kpis(p3, [("M:Annual Payroll", "Annual payroll"), ("M:Gender Pay Gap %", "Gender pay gap (M vs F)"),
          ("M:Attrition Cost (Est.)", "Est. cost of attrition"), ("M:Raise Cost (Annual)", "Cost of raise / yr"),
          ("M:Break-even Leavers", "Leavers to keep to break even"), ("M:Break-even % of Leavers", "...as % of leavers")])
bar(p3, "comp_level", "clusteredColumnChart", "Job Level", "M:Avg Monthly Income", *COLS3[0], ROW2_Y, ROW_H,
    "Avg monthly income by job level", sort=("Job Level", "Ascending"), color=SLATE)
bar(p3, "comp_band", "clusteredColumnChart", "Income Band", "M:Attrition Rate", *COLS3[1], ROW2_Y, ROW_H,
    "Attrition rate by income band", sort=("Income Band", "Ascending"))
bar(p3, "comp_gender", "clusteredBarChart", "JobRole", "M:Avg Monthly Income", *COLS3[2], ROW2_Y, ROW_H,
    "Avg monthly income by role and gender", series="Gender", sort=("M:Avg Monthly Income", "Descending"))
p3.visuals[-1]["visual"]["objects"]["labels"] = obj(show=False)
p3.add("comp_scatter", "scatterChart", M, ROW3_Y, 404, ROW_H,
       roles={"Category": ["JobRole"], "X": ["M:Avg Monthly Income"], "Y": ["M:Attrition Rate"], "Size": ["M:Employees"]},
       objects={"categoryLabels": obj(show=True, fontSize=8.0), "dataPoint": obj(fill=INDIGO),
                "categoryAxis": obj(show=True, showAxisTitle=True, fontSize=9.0),
                "valueAxis": obj(show=True, showAxisTitle=True, fontSize=9.0)},
       vco=title("Pay vs attrition by role (bubble = headcount)"))
p3.add("comp_table", "tableEx", M + 404 + G, ROW3_Y, W - 2 * M - 404 - G, ROW_H - 56,
       roles={"Values": ["JobRole", "M:Employees", "M:Leavers", "M:Attrition Rate", "M:Avg Monthly Income",
                         "M:Attrition Cost (Est.)", "M:Raise Cost (Annual)"]},
       objects={"values": obj(fontSize=9.0), "columnHeaders": obj(fontSize=9.0, bold=True, wordWrap=True),
                "total": obj(totals=True, fontSize=9.0, bold=True)},
       vco=title("Role scorecard"), sort=("M:Attrition Cost (Est.)", "Descending"))
p3.visuals[-1]["visual"]["query"]["queryState"]["Values"]["projections"][0]["displayName"] = "Job role"
p3.add("comp_insight", "card", M + 404 + G, ROW3_Y + ROW_H - 48, W - 2 * M - 404 - G, 48,
       roles={"Values": ["M:Insight Raise"]},
       objects={"labels": obj(color=NAVY, fontSize=12.0, fontFamily="Segoe UI Semibold"), "categoryLabels": obj(show=False),
                "wordWrap": obj(show=True)},
       vco={"title": obj(show=False), "background": obj(show=True, color="#E8F4F6", transparency=0.0),
            "border": obj(show=True, color=TEAL, radius=8.0)})

# ---------- write report
RD = f"{RP}/definition"
write(f"{RD}/version.json", {"$schema": SCH + "item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
write(f"{RD}/report.json", {
    "$schema": SCH + "item/report/definition/report/3.0.0/schema.json",
    "themeCollection": {"customTheme": {"name": "HRNavy.json", "type": "RegisteredResources",
                                        "reportVersionAtImport": {"visual": "2.4.0", "report": "3.0.0", "page": "2.0.0"}}},
    "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                          "items": [{"name": "HRNavy.json", "path": "HRNavy.json", "type": "CustomTheme"}]}],
    "settings": {"useStylableVisualContainerHeader": True, "defaultDrillFilterOtherVisuals": True,
                 "allowChangeFilterTypes": True, "useEnhancedTooltips": True},
})
write(f"{RD}/pages/pages.json", {"$schema": SCH + "item/report/definition/pagesMetadata/1.0.0/schema.json",
                                 "pageOrder": [p for p, _ in PAGES], "activePageName": PAGES[0][0]})
for pg in (p1, p2, p3):
    write(f"{RD}/pages/{pg.name}/page.json", {
        "$schema": SCH + "item/report/definition/page/2.0.0/schema.json",
        "name": pg.name, "displayName": pg.display, "displayOption": "FitToPage", "height": H, "width": W,
        "objects": {"background": obj(color=BG, transparency=0.0)}})
    for v in pg.visuals:
        write(f"{RD}/pages/{pg.name}/visuals/{v['name']}/visual.json", v)

write(f"{RP}/StaticResources/RegisteredResources/HRNavy.json", {
    "name": "HR Navy",
    "dataColors": ["#3D63C9", "#B26B00", INDIGO, TEAL, "#9AA8B3", SLATE, "#7A5CC2", "#D9A21B"],  # Female, Male first
    "background": "#FFFFFF", "foreground": INK, "tableAccent": NAVY,
    "good": "#2E9E6A", "neutral": "#D9A21B", "bad": "#C23B5A",
    "textClasses": {
        "title": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": INK},
        "label": {"fontFace": "Segoe UI", "fontSize": 9, "color": MUTED},
        "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 22, "color": INK},
    },
    "visualStyles": {
        "*": {"*": {
            "background": [{"show": True, "color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}],
            "border": [{"show": True, "color": {"solid": {"color": LINE}}, "radius": 8}],
            "dropShadow": [{"show": False}],
            "padding": [{"top": 6, "bottom": 6, "left": 10, "right": 10}],
            "title": [{"show": True, "fontSize": 11, "fontColor": {"solid": {"color": INK}}}],
        }},
        "page": {"*": {"background": [{"color": {"solid": {"color": BG}}, "transparency": 0}]}},
    },
})

print("pages:", {pg.display: len(pg.visuals) for pg in (p1, p2, p3)}, "measures:", len(MEASURES))

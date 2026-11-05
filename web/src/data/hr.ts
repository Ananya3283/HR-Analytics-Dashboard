// Loads data/HR.csv (the same file Power BI and the SQL use) and mirrors the DAX measures.
import csv from "../../../data/HR.csv?raw"

export type Employee = {
  id: number
  age: number
  left: boolean
  travel: string
  department: string
  educationField: string
  gender: "Female" | "Male"
  jobLevel: number
  jobRole: string
  jobSatisfaction: number
  workLifeBalance: number
  monthlyIncome: number
  overtime: boolean
  stockOptionLevel: number
  yearsAtCompany: number
  ageBand: string
  tenureBand: string
  incomeBand: string
}

export const AGE_BANDS = ["18-25", "26-35", "36-45", "46-55", "56+"]
export const TENURE_BANDS = ["0-2 yrs", "3-5 yrs", "6-10 yrs", "10+ yrs"]
export const INCOME_BANDS = ["Under 3K", "3K-5K", "5K-10K", "10K+"]
export const SATISFACTION = ["Low", "Medium", "High", "Very high"]
export const WORK_LIFE = ["Bad", "Good", "Better", "Best"]

const ageBand = (a: number) => AGE_BANDS[a <= 25 ? 0 : a <= 35 ? 1 : a <= 45 ? 2 : a <= 55 ? 3 : 4]
const tenureBand = (y: number) => TENURE_BANDS[y <= 2 ? 0 : y <= 5 ? 1 : y <= 10 ? 2 : 3]
const incomeBand = (m: number) => INCOME_BANDS[m < 3000 ? 0 : m < 5000 ? 1 : m < 10000 ? 2 : 3]

function parse(text: string): Employee[] {
  const [header, ...lines] = text.replace(/^﻿/, "").trim().split(/\r?\n/)
  const cols = header.split(",")
  const ix = Object.fromEntries(cols.map((c, i) => [c, i]))
  return lines.map((line) => {
    const v = line.split(",")
    const n = (c: string) => Number(v[ix[c]])
    const s = (c: string) => v[ix[c]]
    return {
      id: n("EmployeeNumber"),
      age: n("Age"),
      left: s("Attrition") === "Yes",
      travel: s("BusinessTravel").replace("_", " ").replace("Travel Frequently", "Frequent").replace("Travel Rarely", "Rare").replace("Non-Travel", "None"),
      department: s("Department"),
      educationField: s("EducationField"),
      gender: s("Gender") as Employee["gender"],
      jobLevel: n("JobLevel"),
      jobRole: s("JobRole"),
      jobSatisfaction: n("JobSatisfaction"),
      workLifeBalance: n("WorkLifeBalance"),
      monthlyIncome: n("MonthlyIncome"),
      overtime: s("OverTime") === "Yes",
      stockOptionLevel: n("StockOptionLevel"),
      yearsAtCompany: n("YearsAtCompany"),
      ageBand: ageBand(n("Age")),
      tenureBand: tenureBand(n("YearsAtCompany")),
      incomeBand: incomeBand(n("MonthlyIncome")),
    }
  })
}

export const EMPLOYEES = parse(csv)

// ---------- filters (the slicers)
export type Filters = { department: string; gender: string; level: string; age: string }
export const ALL = "All"
export const options = {
  department: [...new Set(EMPLOYEES.map((e) => e.department))].sort(),
  gender: ["Female", "Male"],
  level: ["1", "2", "3", "4", "5"],
  age: AGE_BANDS,
}
export const applyFilters = (rows: Employee[], f: Filters) =>
  rows.filter(
    (e) =>
      (f.department === ALL || e.department === f.department) &&
      (f.gender === ALL || e.gender === f.gender) &&
      (f.level === ALL || e.jobLevel === Number(f.level)) &&
      (f.age === ALL || e.ageBand === f.age),
  )

// ---------- measures (same definitions as the DAX in _Measures.tmdl)
const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0)
export const leavers = (rows: Employee[]) => rows.filter((e) => e.left).length
export const rate = (rows: Employee[]) => (rows.length ? leavers(rows) / rows.length : null)
export const avg = (rows: Employee[], f: (e: Employee) => number) => (rows.length ? sum(rows.map(f)) / rows.length : null)

export type Metric = "rate" | "leavers" | "headcount"
export const metricValue = (rows: Employee[], m: Metric) =>
  m === "leavers" ? leavers(rows) : m === "headcount" ? rows.length : rate(rows)

/** Group rows by a key in a fixed category order and evaluate a measure per group. */
export function breakdown<K extends string>(rows: Employee[], key: (e: Employee) => K, order: readonly K[], measure: (g: Employee[]) => number | null) {
  return order
    .map((k) => {
      const g = rows.filter((e) => key(e) === k)
      return { key: k, n: g.length, left: leavers(g), value: g.length ? measure(g) : null }
    })
    .filter((d) => d.n > 0)
}

export function whatIf(rows: Employee[], raisePct: number, replacementPct: number) {
  const stayers = rows.filter((e) => !e.left)
  const gone = rows.filter((e) => e.left)
  const attritionCost = sum(gone.map((e) => e.monthlyIncome * 12)) * replacementPct
  const costPerLeaver = gone.length ? attritionCost / gone.length : 0
  const raiseCost = sum(stayers.map((e) => e.monthlyIncome * 12)) * raisePct
  const breakEven = costPerLeaver ? raiseCost / costPerLeaver : 0
  return { attritionCost, costPerLeaver, raiseCost, breakEven, leavers: gone.length, payroll: sum(rows.map((e) => e.monthlyIncome * 12)) }
}

// ---------- insight sentences (mirror the DAX "Insight" measures)
const pct = (x: number | null, d = 0) => (x == null ? "n/a" : `${(x * 100).toFixed(d)}%`)

export function insights(rows: Employee[]): string[] {
  const out: string[] = []
  const roles = breakdown(rows, (e) => e.jobRole, [...new Set(rows.map((e) => e.jobRole))], rate).filter((r) => r.n >= 20)
  if (roles.length) {
    const top = roles.reduce((a, b) => ((b.value ?? 0) > (a.value ?? 0) ? b : a))
    out.push(`The riskiest role is ${top.key}: ${pct(top.value, 1)} of them left.`)
  }
  const ot = rate(rows.filter((e) => e.overtime))
  const noOt = rate(rows.filter((e) => !e.overtime))
  if (ot != null && noOt) out.push(`People on overtime leave ${(ot / noOt).toFixed(1)}× as often (${pct(ot)} vs ${pct(noOt)}).`)
  const l = leavers(rows)
  if (l) {
    const early = rows.filter((e) => e.left && e.yearsAtCompany <= 2).length
    out.push(`${pct(early / l)} of leavers quit within their first two years.`)
  }
  const low = rate(rows.filter((e) => e.incomeBand === "Under 3K"))
  const high = rate(rows.filter((e) => e.incomeBand === "10K+"))
  if (low != null && high != null) out.push(`Under-3K earners leave at ${pct(low)}, against ${pct(high)} for 10K+.`)
  return out
}

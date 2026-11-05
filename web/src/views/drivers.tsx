import { HeatGrid, OrderedColumns, Panel, RankBars } from "@/components/charts"
import { Figures } from "@/components/figures"
import { Segmented } from "@/components/segmented"
import { SATISFACTION, WORK_LIFE, breakdown, leavers, metricValue, rate, type Employee, type Metric } from "@/data/hr"
import type { Fmt } from "@/lib/format"

const METRICS: { value: Metric; label: string }[] = [
  { value: "rate", label: "Attrition rate" },
  { value: "leavers", label: "People who left" },
  { value: "headcount", label: "Headcount" },
]

export function Drivers({ rows, metric, setMetric }: { rows: Employee[]; metric: Metric; setMetric: (m: Metric) => void }) {
  const m = (g: Employee[]) => metricValue(g, metric)
  const f: Fmt = metric === "rate" ? "pct" : "int"
  const color = metric === "headcount" ? "var(--stayed)" : "var(--left)"
  const ot = rate(rows.filter((e) => e.overtime))
  const noOt = rate(rows.filter((e) => !e.overtime))

  return (
    <div className="space-y-12">
      <section className="max-w-2xl">
        <h1 className="text-4xl leading-[1.05] font-extrabold tracking-tight text-balance sm:text-5xl">Overtime is the clearest warning sign.</h1>
        <p className="mt-4 text-muted-foreground">
          Every chart below splits the same people by one factor. Switch the measure to see whether a group stands out because of its rate or just its size.
        </p>
      </section>

      <Figures
        items={[
          { label: "Attrition rate", value: rate(rows), format: "pct", tone: "left" },
          { label: "With overtime", value: ot, format: "pct", tone: "left" },
          { label: "Without overtime", value: noOt, format: "pct" },
          { label: "Overtime multiple", value: ot != null && noOt ? ot / noOt : null, format: "x" },
          { label: "In first two years", value: rate(rows.filter((e) => e.yearsAtCompany <= 2)), format: "pct", tone: "left" },
          { label: "Left", value: leavers(rows), format: "int" },
        ]}
      />

      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm text-muted-foreground">Show</span>
        <Segmented id="metric" label="Measure shown in the charts" value={metric} onChange={setMetric} options={METRICS} />
      </div>

      <div className="grid gap-x-12 gap-y-10 md:grid-cols-2 xl:grid-cols-3">
        <Panel title="Overtime">
          <OrderedColumns data={breakdown(rows, (e) => (e.overtime ? "Overtime" : "No overtime"), ["Overtime", "No overtime"], m)} format={f} color={color} />
        </Panel>
        <Panel title="Job satisfaction">
          <OrderedColumns data={breakdown(rows, (e) => SATISFACTION[e.jobSatisfaction - 1], SATISFACTION, m)} format={f} color={color} />
        </Panel>
        <Panel title="Work-life balance">
          <OrderedColumns data={breakdown(rows, (e) => WORK_LIFE[e.workLifeBalance - 1], WORK_LIFE, m)} format={f} color={color} />
        </Panel>
        <Panel title="Business travel">
          <RankBars data={breakdown(rows, (e) => e.travel, ["Frequent", "Rare", "None"], m)} format={f} color={color} />
        </Panel>
        <Panel title="Stock option level" note="Level 0 means no stock options.">
          <OrderedColumns data={breakdown(rows, (e) => `Level ${e.stockOptionLevel}`, ["Level 0", "Level 1", "Level 2", "Level 3"], m)} format={f} color={color} />
        </Panel>
        <Panel title="Job level and overtime" note="Attrition rate. Darker means more people left.">
          <HeatGrid
            rows={["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]}
            cols={["No overtime", "Overtime"]}
            cell={(r, c) => {
              const g = rows.filter((e) => `Level ${e.jobLevel}` === r && e.overtime === (c === "Overtime"))
              return { value: rate(g), n: g.length }
            }}
          />
        </Panel>
      </div>
    </div>
  )
}

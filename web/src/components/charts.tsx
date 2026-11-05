import { Bar, BarChart, CartesianGrid, Cell, LabelList, Legend, Scatter, ScatterChart, XAxis, YAxis, ZAxis } from "recharts"
import { useReducedMotion } from "motion/react"
import { ChartContainer, ChartTooltip, type ChartConfig } from "@/components/ui/chart"
import { fmt, type Fmt } from "@/lib/format"
import { cn } from "@/lib/utils"

export type Datum = { key: string; value: number | null; n?: number; left?: number }

/** Shared panel: a heading and the chart, no card chrome. */
export function Panel({ title, note, children, className }: { title: string; note?: string; children: React.ReactNode; className?: string }) {
  return (
    <section className={cn("min-w-0", className)}>
      <h3 className="text-base font-semibold">{title}</h3>
      {note && <p className="mt-0.5 text-sm text-muted-foreground">{note}</p>}
      <div className="mt-3">{children}</div>
    </section>
  )
}

function Tip({ active, payload, format }: { active?: boolean; payload?: { payload: Datum }[]; format: Fmt }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded-md border bg-popover px-2.5 py-1.5 text-xs shadow-md">
      <div className="font-semibold">{d.key}</div>
      <div className="tabular-nums">{fmt(d.value, format)}</div>
      {d.n != null && (
        <div className="text-muted-foreground tabular-nums">
          {d.left} of {d.n.toLocaleString("en-US")} left
        </div>
      )}
    </div>
  )
}

const config = { value: { label: "Value", color: "var(--left)" } } satisfies ChartConfig

/** Raspberry bars: the highest one carries full colour, the rest step back to the ramp's lightest tint. */
function fills(data: Datum[], color: string) {
  if (color !== "var(--left)") return data.map(() => color)
  const max = Math.max(...data.map((d) => d.value ?? 0))
  return data.map((d) => (d.value === max ? "var(--left)" : "var(--heat-1)"))
}

/** Ranked horizontal bars, highest first. */
export function RankBars({ data, format, color = "var(--left)", height }: { data: Datum[]; format: Fmt; color?: string; height?: number }) {
  const reduce = useReducedMotion()
  const sorted = [...data].sort((a, b) => (b.value ?? 0) - (a.value ?? 0))
  return (
    <ChartContainer config={config} className="aspect-auto w-full" style={{ height: height ?? sorted.length * 30 + 12 }}>
      <BarChart data={sorted} layout="vertical" margin={{ left: 0, right: 52, top: 0, bottom: 0 }} barCategoryGap={6}>
        <XAxis type="number" hide domain={[0, "dataMax"]} />
        <YAxis type="category" dataKey="key" width={156} tickLine={false} axisLine={false} tick={{ fontSize: 13 }} />
        <ChartTooltip cursor={{ fill: "var(--muted)" }} content={<Tip format={format} />} />
        <Bar dataKey="value" fill={color} radius={[0, 4, 4, 0]} isAnimationActive={!reduce} animationDuration={400}>
          {fills(sorted, color).map((c, i) => <Cell key={i} fill={c} />)}
          <LabelList dataKey="value" position="right" className="fill-foreground tabular-nums" fontSize={12} formatter={(v) => fmt(v as number, format)} />
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}

/** Columns in a fixed category order (bands, levels, scores). */
export function OrderedColumns({ data, format, color = "var(--left)", height = 210 }: { data: Datum[]; format: Fmt; color?: string; height?: number }) {
  const reduce = useReducedMotion()
  return (
    <ChartContainer config={config} className="aspect-auto w-full" style={{ height }}>
      <BarChart data={data} margin={{ left: 0, right: 0, top: 22, bottom: 0 }} barCategoryGap="22%">
        <XAxis dataKey="key" tickLine={false} axisLine={{ stroke: "var(--border)" }} tick={{ fontSize: 12 }} interval={0} />
        <YAxis hide domain={[0, "dataMax"]} />
        <ChartTooltip cursor={{ fill: "var(--muted)" }} content={<Tip format={format} />} />
        <Bar dataKey="value" fill={color} radius={[4, 4, 0, 0]} isAnimationActive={!reduce} animationDuration={400}>
          {fills(data, color).map((c, i) => <Cell key={i} fill={c} />)}
          <LabelList dataKey="value" position="top" className="fill-foreground tabular-nums" fontSize={12} formatter={(v) => fmt(v as number, format)} />
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}

/** Average income by role, women and men side by side. */
export function GenderPay({ data }: { data: { key: string; Female: number | null; Male: number | null }[] }) {
  const reduce = useReducedMotion()
  const cfg = { Female: { label: "Women", color: "var(--female)" }, Male: { label: "Men", color: "var(--male)" } } satisfies ChartConfig
  return (
    <ChartContainer config={cfg} className="aspect-auto w-full" style={{ height: data.length * 40 + 40 }}>
      <BarChart data={data} layout="vertical" margin={{ left: 0, right: 8, top: 0, bottom: 0 }} barGap={2} barCategoryGap={8}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="key" width={156} tickLine={false} axisLine={false} tick={{ fontSize: 13 }} />
        <ChartTooltip
          cursor={{ fill: "var(--muted)" }}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <div className="rounded-md border bg-popover px-2.5 py-1.5 text-xs shadow-md">
                <div className="font-semibold">{payload[0].payload.key}</div>
                {payload.map((p) => (
                  <div key={String(p.dataKey)} className="flex items-center gap-1.5 tabular-nums">
                    <span className="size-2 rounded-full" style={{ background: p.color }} />
                    {p.dataKey === "Female" ? "Women" : "Men"} {fmt(p.value as number, "int")}
                  </div>
                ))}
              </div>
            ) : null
          }
        />
        <Legend verticalAlign="top" align="left" height={28} iconType="circle" iconSize={8} formatter={(v) => <span className="text-sm text-foreground">{v === "Female" ? "Women" : "Men"}</span>} />
        <Bar dataKey="Female" fill="var(--female)" radius={[0, 4, 4, 0]} isAnimationActive={!reduce} animationDuration={400} />
        <Bar dataKey="Male" fill="var(--male)" radius={[0, 4, 4, 0]} isAnimationActive={!reduce} animationDuration={400} />
      </BarChart>
    </ChartContainer>
  )
}

// Direct-label only the roles the story needs; the rest are one hover away (dataviz: selective labels)
const LABELLED = new Set(["Sales Representative", "Laboratory Technician", "Sales Executive", "Manager"])

/** Pay against attrition per role; bubble size = headcount. */
export function PayScatter({ data }: { data: { key: string; income: number; rate: number; n: number }[] }) {
  const reduce = useReducedMotion()
  return (
    <ChartContainer config={config} className="aspect-auto w-full" style={{ height: 300 }}>
      <ScatterChart margin={{ left: 4, right: 72, top: 12, bottom: 20 }}>
        <CartesianGrid stroke="var(--border)" strokeDasharray="2 4" />
        <XAxis type="number" dataKey="income" name="Avg monthly income" tickFormatter={(v) => fmt(v, "money")} tick={{ fontSize: 12 }}
          label={{ value: "Average monthly income", position: "bottom", offset: 2, fontSize: 12, fill: "var(--muted-foreground)" }} />
        <YAxis type="number" dataKey="rate" name="Attrition rate" tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 12 }} width={40} />
        <ZAxis type="number" dataKey="n" range={[60, 600]} />
        <ChartTooltip
          cursor={false}
          content={({ active, payload }) =>
            active && payload?.length ? (
              <div className="rounded-md border bg-popover px-2.5 py-1.5 text-xs shadow-md">
                <div className="font-semibold">{payload[0].payload.key}</div>
                <div className="tabular-nums">{fmt(payload[0].payload.rate, "pct")} left, earning {fmt(payload[0].payload.income, "int")} a month</div>
                <div className="text-muted-foreground tabular-nums">{payload[0].payload.n} people</div>
              </div>
            ) : null
          }
        />
        <Scatter data={data} fill="var(--left)" fillOpacity={0.75} stroke="var(--background)" strokeWidth={2} isAnimationActive={!reduce}>
          <LabelList
            dataKey="key"
            content={({ x, y, value }) =>
              LABELLED.has(String(value)) ? (
                <text x={Number(x) + 18} y={Number(y) + 4} fontSize={12} className="fill-foreground">{String(value)}</text>
              ) : null
            }
          />
        </Scatter>
      </ScatterChart>
    </ChartContainer>
  )
}

/** Job level x overtime attrition grid on the sequential raspberry ramp. */
export function HeatGrid({ rows, cols, cell }: { rows: string[]; cols: string[]; cell: (r: string, c: string) => { value: number | null; n: number } }) {
  const step = (v: number) => (v < 0.08 ? 1 : v < 0.15 ? 2 : v < 0.25 ? 3 : v < 0.4 ? 4 : 5)
  return (
    <table className="w-full border-separate border-spacing-0.5 text-sm tabular-nums">
      <thead>
        <tr>
          <th className="w-24 text-left font-normal text-muted-foreground">Job level</th>
          {cols.map((c) => (
            <th key={c} className="pb-1 font-normal text-muted-foreground">{c}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r}>
            <th className="text-left font-normal">{r}</th>
            {cols.map((c) => {
              const { value, n } = cell(r, c)
              const s = value == null ? 0 : step(value)
              return (
                <td
                  key={c}
                  title={`${r}, ${c}: ${fmt(value, "pct")} of ${n} people left`}
                  className="h-10 rounded-sm text-center font-semibold"
                  style={{
                    background: s ? `var(--heat-${s})` : "var(--muted)",
                    color: s >= 3 ? "#fff" : "var(--foreground)",
                    transition: "background-color var(--duration-fast) var(--ease-smooth-out)",
                  }}
                >
                  {n ? fmt(value, "pct") : "–"}
                </td>
              )
            })}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

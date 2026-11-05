import NumberFlow from "@number-flow/react"
import { AnimatePresence, motion } from "motion/react"
import { GenderPay, OrderedColumns, Panel, PayScatter } from "@/components/charts"
import { Figures } from "@/components/figures"
import { Slider } from "@/components/ui/slider"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { EMPLOYEES, INCOME_BANDS, avg, breakdown, leavers, rate, whatIf, type Employee } from "@/data/hr"
import { fmt } from "@/lib/format"

const INK = "#46535d" // neutral bars for money: not a category, so not a data hue

export function Compensation({ rows, raise, setRaise, repl, setRepl }: {
  rows: Employee[]; raise: number; setRaise: (v: number) => void; repl: number; setRepl: (v: number) => void
}) {
  const w = whatIf(rows, raise, repl)
  const paysBack = w.breakEven <= w.leavers
  const max = Math.max(w.breakEven, w.leavers, 1)
  const roles = [...new Set(EMPLOYEES.map((e) => e.jobRole))]
  const women = avg(rows.filter((e) => e.gender === "Female"), (e) => e.monthlyIncome)
  const men = avg(rows.filter((e) => e.gender === "Male"), (e) => e.monthlyIncome)
  const byRole = roles
    .map((r) => {
      const g = rows.filter((e) => e.jobRole === r)
      const wi = whatIf(g, raise, repl)
      return { key: r, n: g.length, left: leavers(g), rate: rate(g), income: avg(g, (e) => e.monthlyIncome), cost: wi.attritionCost, raise: wi.raiseCost }
    })
    .filter((r) => r.n > 0)
    .sort((a, b) => b.cost - a.cost)

  return (
    <div className="space-y-12">
      {/* Hero: the what-if, answered in one live sentence */}
      <section className="grid gap-10 lg:grid-cols-[minmax(0,4fr)_minmax(0,7fr)]">
        <div className="space-y-8">
          <label className="block">
            <span className="flex items-baseline justify-between text-sm">
              <span className="font-semibold">Raise for everyone who stayed</span>
              <span className="tabular-nums">{fmt(raise, "pct")}</span>
            </span>
            <Slider className="mt-3" min={0} max={0.2} step={0.025} value={raise} onValueChange={(v) => setRaise(v as number)} aria-label="Raise percentage" />
          </label>
          <label className="block">
            <span className="flex items-baseline justify-between text-sm">
              <span className="font-semibold">Cost to replace one leaver</span>
              <span className="tabular-nums">{Math.round(repl * 100)}% of salary</span>
            </span>
            <Slider className="mt-3" min={0.25} max={1.5} step={0.25} value={repl} onValueChange={(v) => setRepl(v as number)} aria-label="Replacement cost as a share of annual salary" />
            <span className="mt-2 block text-sm text-muted-foreground">An assumption. Estimates range from a quarter to one and a half times salary.</span>
          </label>
        </div>

        <div>
          <p className="text-2xl leading-snug font-bold tracking-tight text-balance sm:text-3xl">
            A <NumberFlow value={raise} format={{ style: "percent", maximumFractionDigits: 1 }} /> raise costs{" "}
            <span className="text-kept"><NumberFlow value={w.raiseCost} format={{ notation: "compact", maximumFractionDigits: 1 }} /></span> a year.
            To pay for itself it has to prevent <span className="text-kept"><NumberFlow value={Math.round(w.breakEven)} /></span> departures.{" "}
            <span className="text-leaver"><NumberFlow value={w.leavers} /></span> people left.
          </p>
          <div className="mt-6 space-y-2" aria-hidden="true">
            {[
              { label: "Departures the raise must prevent", v: w.breakEven, c: "var(--kept)" },
              { label: "People who actually left", v: w.leavers, c: "var(--left)" },
            ].map((b) => (
              <div key={b.label} className="grid grid-cols-[minmax(0,12rem)_1fr] items-center gap-3 text-sm">
                <span className="text-muted-foreground">{b.label}</span>
                <div className="h-3 rounded-r bg-muted">
                  <motion.div
                    className="h-full rounded-r"
                    style={{ background: b.c, transformOrigin: "left" }}
                    animate={{ scaleX: Math.min(b.v / max, 1) }}
                    transition={{ type: "spring", visualDuration: 0.4, bounce: 0 }}
                  />
                </div>
              </div>
            ))}
          </div>
          <AnimatePresence mode="wait" initial={false}>
            <motion.p
              key={raise === 0 ? "zero" : paysBack ? "yes" : "no"}
              initial={{ opacity: 0, y: 4, filter: "blur(2px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, filter: "blur(2px)", transition: { duration: 0.15 } }}
              transition={{ duration: 0.15 }}
              className="mt-5 font-semibold"
            >
              {raise === 0
                ? "Move the raise slider to test a pay rise."
                : paysBack
                  ? `It pays for itself if it keeps ${fmt(w.breakEven / Math.max(w.leavers, 1), "pct")} of the people who would leave.`
                  : "It cannot pay for itself. Target the raise at a smaller, higher-risk group instead (try Job level 1)."}
            </motion.p>
          </AnimatePresence>
        </div>
      </section>

      <Figures
        items={[
          { label: "Annual payroll", value: w.payroll, format: "money" },
          { label: "Avg monthly income", value: avg(rows, (e) => e.monthlyIncome), format: "int" },
          { label: "Gender pay gap", value: men && women ? (men - women) / men : null, format: "pct" },
          { label: "Cost of attrition a year", value: w.attritionCost, format: "money", tone: "left" },
          { label: "Cost per leaver", value: w.costPerLeaver, format: "money" },
          { label: "Cost of the raise a year", value: w.raiseCost, format: "money", tone: "kept" },
        ]}
      />
      <p className="-mt-8 text-sm text-muted-foreground">Gender pay gap: positive means men earn more on average, negative means women do.</p>

      <div className="grid gap-x-12 gap-y-10 lg:grid-cols-2">
        <Panel title="Average monthly income by job level">
          <OrderedColumns data={breakdown(rows, (e) => `Level ${e.jobLevel}`, ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"], (g) => avg(g, (e) => e.monthlyIncome))} format="money" color={INK} />
        </Panel>
        <Panel title="Attrition rate by monthly income" note="Lower earners leave more often.">
          <OrderedColumns data={breakdown(rows, (e) => e.incomeBand, INCOME_BANDS, rate)} format="pct" />
        </Panel>
        <Panel title="Pay against attrition, by role" note="Bubble size is headcount. Lower-paid roles sit higher.">
          <PayScatter data={byRole.filter((r) => r.rate != null && r.income != null).map((r) => ({ key: r.key, income: r.income!, rate: r.rate!, n: r.n }))} />
        </Panel>
        <Panel title="Average monthly income by role">
          <GenderPay
            data={roles.map((r) => ({
              key: r,
              Female: avg(rows.filter((e) => e.jobRole === r && e.gender === "Female"), (e) => e.monthlyIncome),
              Male: avg(rows.filter((e) => e.jobRole === r && e.gender === "Male"), (e) => e.monthlyIncome),
            })).filter((d) => d.Female != null || d.Male != null).sort((a, b) => (b.Male ?? 0) - (a.Male ?? 0))}
          />
        </Panel>
      </div>

      <Panel title="Role scorecard" note="Sorted by the yearly cost of the people each role lost.">
        <div className="overflow-x-auto">
          <Table className="tabular-nums">
            <TableHeader>
              <TableRow>
                <TableHead>Job role</TableHead>
                <TableHead className="text-right">People</TableHead>
                <TableHead className="text-right">Left</TableHead>
                <TableHead className="text-right">Attrition rate</TableHead>
                <TableHead className="text-right">Avg monthly income</TableHead>
                <TableHead className="text-right">Cost of attrition</TableHead>
                <TableHead className="text-right">Cost of raise</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {byRole.map((r) => (
                <TableRow key={r.key}>
                  <TableCell className="font-semibold">{r.key}</TableCell>
                  <TableCell className="text-right">{fmt(r.n, "int")}</TableCell>
                  <TableCell className="text-right">{fmt(r.left, "int")}</TableCell>
                  <TableCell className="text-right">{fmt(r.rate, "pct")}</TableCell>
                  <TableCell className="text-right">{fmt(r.income, "int")}</TableCell>
                  <TableCell className="text-right">{fmt(r.cost, "money")}</TableCell>
                  <TableCell className="text-right">{fmt(r.raise, "money")}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </Panel>
    </div>
  )
}

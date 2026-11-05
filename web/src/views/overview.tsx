import NumberFlow from "@number-flow/react"
import { AnimatePresence, motion } from "motion/react"
import { useMemo } from "react"
import { OrderedColumns, Panel, RankBars } from "@/components/charts"
import { Figures } from "@/components/figures"
import { PeopleGrid } from "@/components/people-grid"
import { AGE_BANDS, EMPLOYEES, TENURE_BANDS, avg, breakdown, insights, leavers, rate, type Employee } from "@/data/hr"

export function Overview({ rows }: { rows: Employee[] }) {
  const selected = useMemo(() => new Set(rows.map((e) => e.id)), [rows])
  const l = leavers(rows)
  const roles = [...new Set(EMPLOYEES.map((e) => e.jobRole))]
  const depts = [...new Set(EMPLOYEES.map((e) => e.department))]

  return (
    <div className="space-y-12">
      <section className="grid items-start gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div>
          <h1 className="text-4xl leading-[1.05] font-extrabold tracking-tight text-balance sm:text-5xl">
            <NumberFlow value={rows.length} /> people.{" "}
            <span className="text-leaver">
              <NumberFlow value={l} /> left.
            </span>
          </h1>
          <p className="mt-4 max-w-md text-muted-foreground">
            Each dot is one employee in the IBM HR dataset. Raspberry dots are people who left. Hover a dot to see who it is, and use the filters to light up a group.
          </p>
          <h2 className="mt-8 text-base font-semibold">What stands out</h2>
          <ul className="mt-2 space-y-2.5">
            <AnimatePresence mode="popLayout" initial={false}>
              {insights(rows).map((s) => (
                <motion.li
                  key={s}
                  layout
                  initial={{ opacity: 0, y: 4, filter: "blur(2px)" }}
                  animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                  exit={{ opacity: 0, filter: "blur(2px)", transition: { duration: 0.15 } }}
                  transition={{ duration: 0.15, ease: [0.22, 1, 0.36, 1] }}
                  className="border-l-2 border-leaver pl-3 leading-snug"
                >
                  {s}
                </motion.li>
              ))}
            </AnimatePresence>
          </ul>
        </div>
        <PeopleGrid people={EMPLOYEES} selected={selected} />
      </section>

      <Figures
        items={[
          { label: "Employees", value: rows.length, format: "int" },
          { label: "Left", value: l, format: "int", tone: "left" },
          { label: "Attrition rate", value: rate(rows), format: "pct", tone: "left" },
          { label: "Avg monthly income", value: avg(rows, (e) => e.monthlyIncome), format: "int" },
          { label: "Avg age", value: avg(rows, (e) => e.age), format: "dec" },
          { label: "Avg years at company", value: avg(rows, (e) => e.yearsAtCompany), format: "dec" },
        ]}
      />

      <div className="grid gap-x-12 gap-y-10 lg:grid-cols-2">
        <Panel title="Attrition rate by job role" note="Roles with the highest share of people leaving come first.">
          <RankBars data={breakdown(rows, (e) => e.jobRole, roles, rate)} format="pct" />
        </Panel>
        <div className="space-y-10">
          <Panel title="Attrition rate by department">
            <RankBars data={breakdown(rows, (e) => e.department, depts, rate)} format="pct" />
          </Panel>
          <Panel title="Attrition rate by gender">
            <RankBars data={breakdown(rows, (e) => (e.gender === "Female" ? "Women" : "Men"), ["Women", "Men"], rate)} format="pct" />
          </Panel>
        </div>
        <Panel title="Attrition rate by age">
          <OrderedColumns data={breakdown(rows, (e) => e.ageBand, AGE_BANDS, rate)} format="pct" />
        </Panel>
        <Panel title="Attrition rate by years at the company" note="New joiners are the most likely to leave.">
          <OrderedColumns data={breakdown(rows, (e) => e.tenureBand, TENURE_BANDS, rate)} format="pct" />
        </Panel>
      </div>
    </div>
  )
}

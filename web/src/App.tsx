import { AnimatePresence, motion } from "motion/react"
import { parseAsFloat, parseAsString, parseAsStringLiteral, useQueryStates } from "nuqs"
import { useMemo } from "react"
import { FilterBar } from "@/components/filter-bar"
import { Segmented } from "@/components/segmented"
import { ALL, EMPLOYEES, applyFilters, type Filters } from "@/data/hr"
import { Compensation } from "@/views/compensation"
import { Drivers } from "@/views/drivers"
import { Overview } from "@/views/overview"

const VIEWS = ["overview", "drivers", "pay"] as const
type View = (typeof VIEWS)[number]

// Every view setting lives in the URL, so a filtered view can be shared as a link
const params = {
  view: parseAsStringLiteral(VIEWS).withDefault("overview"),
  department: parseAsString.withDefault(ALL),
  gender: parseAsString.withDefault(ALL),
  level: parseAsString.withDefault(ALL),
  age: parseAsString.withDefault(ALL),
  metric: parseAsStringLiteral(["rate", "leavers", "headcount"] as const).withDefault("rate"),
  raise: parseAsFloat.withDefault(0.1),
  repl: parseAsFloat.withDefault(0.5),
}

export default function App() {
  const [q, setQ] = useQueryStates(params)
  const filters: Filters = { department: q.department, gender: q.gender, level: q.level, age: q.age }
  const rows = useMemo(() => applyFilters(EMPLOYEES, filters), [q.department, q.gender, q.level, q.age]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="mx-auto max-w-7xl px-4 pb-24 sm:px-8">
      <header className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 pt-8">
        <p className="font-bold">HR attrition analysis</p>
        <p className="text-sm text-muted-foreground">
          IBM HR dataset, 1,470 employees.{" "}
          <a className="font-semibold text-foreground underline underline-offset-4 hover:text-kept" href="https://github.com/Ananya3283/HR-Analytics-Dashboard">
            Code, SQL and Power BI file
          </a>
        </p>
      </header>

      <div className="sticky top-0 z-20 -mx-4 mt-6 border-b bg-background/90 px-4 py-4 backdrop-blur sm:-mx-8 sm:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <Segmented<View>
            id="view"
            label="Dashboard view"
            value={q.view}
            onChange={(view) => setQ({ view })}
            options={[
              { value: "overview", label: "Who leaves" },
              { value: "drivers", label: "Why" },
              { value: "pay", label: "Pay and what-if" },
            ]}
          />
          <FilterBar value={filters} onChange={(k, v) => setQ({ [k]: v === ALL ? null : v })} />
        </div>
      </div>

      <main className="mt-10">
        {rows.length === 0 ? (
          <p className="py-24 text-center text-muted-foreground">No employees match these filters. Clear one to see results.</p>
        ) : (
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={q.view}
              initial={{ opacity: 0, y: 8, filter: "blur(3px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              exit={{ opacity: 0, filter: "blur(3px)", transition: { duration: 0.15 } }}
              transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            >
              {q.view === "overview" && <Overview rows={rows} />}
              {q.view === "drivers" && <Drivers rows={rows} metric={q.metric} setMetric={(metric) => setQ({ metric })} />}
              {q.view === "pay" && (
                <Compensation rows={rows} raise={q.raise} setRaise={(raise) => setQ({ raise })} repl={q.repl} setRepl={(repl) => setQ({ repl })} />
              )}
            </motion.div>
          </AnimatePresence>
        )}
      </main>
    </div>
  )
}

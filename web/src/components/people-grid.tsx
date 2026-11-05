import { useMemo, useRef, useState } from "react"
import type { Employee } from "@/data/hr"

const COLS = 49 // 49 x 30 = 1,470 seats, one per employee
const GAP = 12
const R = 4

type Props = { people: Employee[]; selected: Set<number> }

/** The hero: every employee is a dot. Leavers in raspberry; filtered-out people fade back. */
export function PeopleGrid({ people, selected }: Props) {
  const rows = Math.ceil(people.length / COLS)
  const ref = useRef<SVGSVGElement>(null)
  const [hover, setHover] = useState<{ e: Employee; x: number; y: number } | null>(null)

  // Leavers first within each department block, so the pattern reads at a glance
  const ordered = useMemo(
    () => [...people].sort((a, b) => a.department.localeCompare(b.department) || Number(b.left) - Number(a.left) || a.id - b.id),
    [people],
  )

  function onMove(ev: React.PointerEvent<SVGSVGElement>) {
    const svg = ref.current
    if (!svg) return
    const box = svg.getBoundingClientRect()
    const scale = (COLS * GAP) / box.width
    const col = Math.floor(((ev.clientX - box.left) * scale) / GAP)
    const row = Math.floor(((ev.clientY - box.top) * scale) / GAP)
    const e = ordered[row * COLS + col]
    setHover(e && col >= 0 && col < COLS ? { e, x: ev.clientX - box.left, y: ev.clientY - box.top } : null)
  }

  return (
    <figure className="relative">
      <svg
        ref={ref}
        viewBox={`0 0 ${COLS * GAP} ${rows * GAP}`}
        className="block h-auto w-full touch-none"
        role="img"
        aria-label={`${people.length} employees as dots; ${people.filter((p) => p.left).length} who left are highlighted`}
        onPointerMove={onMove}
        onPointerLeave={() => setHover(null)}
      >
        {ordered.map((e, i) => {
          const on = selected.has(e.id)
          return (
            <circle
              key={e.id}
              cx={(i % COLS) * GAP + GAP / 2}
              cy={Math.floor(i / COLS) * GAP + GAP / 2}
              r={R}
              fill={e.left ? "var(--left)" : "var(--stayed)"}
              opacity={on ? 1 : 0.14}
              style={{ transition: "opacity var(--duration-fast) var(--ease-smooth-out)" }}
            />
          )
        })}
      </svg>
      {hover && (
        <div
          className="pointer-events-none absolute z-10 w-max -translate-x-1/2 -translate-y-[calc(100%+10px)] rounded-md bg-primary px-2.5 py-1.5 text-xs text-primary-foreground shadow-md"
          style={{ left: hover.x, top: hover.y }}
        >
          <span className="font-semibold">{hover.e.jobRole}</span>, age {hover.e.age}, {hover.e.department}
          <br />
          {hover.e.left ? "Left" : "Stayed"} after {hover.e.yearsAtCompany} {hover.e.yearsAtCompany === 1 ? "year" : "years"}
          {hover.e.overtime ? ", worked overtime" : ""}
        </div>
      )}
    </figure>
  )
}

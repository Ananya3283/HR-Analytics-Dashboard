import NumberFlow from "@number-flow/react"
import { flowFormat, type Fmt } from "@/lib/format"
import { cn } from "@/lib/utils"

export type Figure = { label: string; value: number | null; format: Fmt; tone?: "left" | "kept"; suffix?: string }

/** A row of figures separated by rules (not cards). Numbers roll digit by digit when filters change. */
export function Figures({ items, className }: { items: Figure[]; className?: string }) {
  return (
    <dl className={cn("grid grid-cols-2 border-y sm:grid-cols-3 lg:grid-cols-6", className)}>
      {items.map((f) => (
        <div key={f.label} className="border-b px-1 py-4 sm:px-4 lg:border-b-0 lg:border-l lg:first:border-l-0 lg:first:pl-0">
          <dt className="text-sm text-muted-foreground">{f.label}</dt>
          <dd
            className={cn(
              "mt-1 text-3xl font-bold tracking-tight tabular-nums",
              f.tone === "left" && "text-leaver",
              f.tone === "kept" && "text-kept",
            )}
          >
            {f.value == null ? (
              "–"
            ) : (
              <NumberFlow value={f.value} format={flowFormat[f.format]} suffix={f.format === "x" ? "×" : f.suffix} />
            )}
          </dd>
        </div>
      ))}
    </dl>
  )
}

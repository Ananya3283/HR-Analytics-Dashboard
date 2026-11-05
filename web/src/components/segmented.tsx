import { motion } from "motion/react"
import { cn } from "@/lib/utils"

type Option<T extends string> = { value: T; label: string }

/** Segmented control with a sliding pill (shared layoutId, spring). Used for views and metric switch. */
export function Segmented<T extends string>({
  id, value, onChange, options, label, className,
}: { id: string; value: T; onChange: (v: T) => void; options: Option<T>[]; label: string; className?: string }) {
  return (
    <div role="tablist" aria-label={label} className={cn("inline-flex rounded-full bg-muted p-1", className)}>
      {options.map((o) => {
        const active = o.value === value
        return (
          <button
            key={o.value}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(o.value)}
            className={cn(
              "relative rounded-full px-4 py-1.5 text-sm font-semibold transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring active:scale-[0.97]",
              active ? "text-primary-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {active && (
              <motion.span
                layoutId={`pill-${id}`}
                className="absolute inset-0 rounded-full bg-primary"
                transition={{ type: "spring", visualDuration: 0.25, bounce: 0.15 }}
              />
            )}
            <span className="relative">{o.label}</span>
          </button>
        )
      })}
    </div>
  )
}

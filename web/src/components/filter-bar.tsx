import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ALL, options, type Filters } from "@/data/hr"

const FIELDS: { key: keyof Filters; label: string; all: string; show?: (v: string) => string }[] = [
  { key: "department", label: "Department", all: "All departments" },
  { key: "gender", label: "Gender", all: "Everyone", show: (v) => (v === "Female" ? "Women" : "Men") },
  { key: "level", label: "Job level", all: "All levels", show: (v) => `Level ${v}` },
  { key: "age", label: "Age", all: "All ages" },
]

export function FilterBar({ value, onChange }: { value: Filters; onChange: (k: keyof Filters, v: string) => void }) {
  const active = FIELDS.some((f) => value[f.key] !== ALL)
  return (
    <div className="flex flex-wrap items-end gap-3">
      {FIELDS.map((f) => {
        const items = [{ value: ALL, label: f.all }, ...options[f.key].map((o) => ({ value: o, label: f.show ? f.show(o) : o }))]
        return (
          <label key={f.key} className="grid min-w-40 flex-1 gap-1 text-sm text-muted-foreground sm:flex-none">
            {f.label}
            <Select items={items} value={value[f.key]} onValueChange={(v) => onChange(f.key, String(v ?? ALL))}>
              <SelectTrigger className="w-full bg-card text-foreground sm:w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {items.map((it) => (
                  <SelectItem key={it.value} value={it.value}>
                    {it.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>
        )
      })}
      {active && (
        <button
          onClick={() => FIELDS.forEach((f) => onChange(f.key, ALL))}
          className="h-9 rounded-md px-3 text-sm font-semibold text-kept underline-offset-4 hover:underline focus-visible:ring-2 focus-visible:ring-ring outline-none"
        >
          Clear filters
        </button>
      )}
    </div>
  )
}

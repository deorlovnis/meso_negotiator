interface StatusBadgeProps {
  text: string
}

export function StatusBadge({ text }: StatusBadgeProps) {
  return (
    <div className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-1.5">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
      <span className="text-[11px] font-semibold uppercase tracking-widest text-emerald-700">
        {text}
      </span>
    </div>
  )
}

export function ErrorSection({ error }: { error?: string | null }) {
  return <pre className="rounded-md bg-red-50 p-3 text-xs text-red-700 dark:bg-red-950 dark:text-red-300">{error || "No error recorded."}</pre>;
}

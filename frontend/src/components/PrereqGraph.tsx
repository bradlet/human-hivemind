import { Link } from "react-router-dom";
import type { PrereqNode } from "../lib/api";

export default function PrereqGraph({ nodes }: { nodes: PrereqNode[] }) {
  if (nodes.length === 0) {
    return <div className="text-sm text-ink-500">No prerequisites.</div>;
  }
  const byDepth = new Map<number, PrereqNode[]>();
  for (const n of nodes) {
    const arr = byDepth.get(n.depth) ?? [];
    arr.push(n);
    byDepth.set(n.depth, arr);
  }
  const depths = [...byDepth.keys()].sort((a, b) => a - b);
  return (
    <div className="bg-white border border-ink-200 rounded-lg p-4">
      <div className="text-xs uppercase tracking-wider text-ink-500 mb-3">Prerequisites</div>
      <ol className="space-y-3">
        {depths.map((d) => (
          <li key={d}>
            <div className="text-xs text-ink-400 mb-1">depth {d}</div>
            <ul className="flex flex-wrap gap-2">
              {byDepth.get(d)!.map((n) => (
                <li key={n.slug}>
                  <Link
                    to={`/s/${n.slug}`}
                    className="inline-flex items-center bg-accent-subtle text-accent-ink rounded-full px-3 py-1 text-sm hover:bg-accent hover:text-white transition-colors"
                    title={n.via ? `via ${n.via}` : undefined}
                  >
                    {n.title}
                  </Link>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ol>
    </div>
  );
}

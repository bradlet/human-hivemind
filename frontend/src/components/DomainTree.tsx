import { Link } from "react-router-dom";
import type { DomainNode } from "../lib/api";

export default function DomainTree({ nodes }: { nodes: DomainNode[] }) {
  return (
    <ul className="space-y-1">
      {nodes.map((n) => (
        <DomainTreeItem key={n.slug} node={n} depth={0} />
      ))}
    </ul>
  );
}

function DomainTreeItem({ node, depth }: { node: DomainNode; depth: number }) {
  return (
    <li>
      <Link
        to={`/d/${node.slug}`}
        className="block hover:bg-ink-100 rounded px-2 py-1 text-ink-800"
        style={{ paddingLeft: `${depth * 14 + 8}px` }}
      >
        {node.title}
      </Link>
      {node.children.length > 0 && (
        <ul>
          {node.children.map((c) => (
            <DomainTreeItem key={c.slug} node={c} depth={depth + 1} />
          ))}
        </ul>
      )}
    </li>
  );
}

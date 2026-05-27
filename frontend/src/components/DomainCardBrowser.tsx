import { forwardRef, useLayoutEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen } from "lucide-react";
import type { DomainNode } from "../lib/api";

// ────────────────────────────────────────────────────────────────────────────────
// Gradient palette
// ────────────────────────────────────────────────────────────────────────────────

const KNOWN_GRADIENTS: Record<string, string> = {
  "math-and-science": "from-violet-900 via-purple-900 to-indigo-950",
  mathematics: "from-indigo-900 via-blue-900 to-cyan-950",
  "computer-science": "from-emerald-900 via-teal-900 to-cyan-950",
  physics: "from-blue-900 via-indigo-900 to-purple-950",
  chemistry: "from-green-900 via-emerald-900 to-teal-950",
  biology: "from-lime-900 via-green-900 to-emerald-950",
  humanities: "from-amber-900 via-orange-900 to-rose-950",
  literature: "from-rose-900 via-pink-900 to-fuchsia-950",
  psychology: "from-fuchsia-900 via-purple-900 to-violet-950",
};

const FALLBACK_GRADIENTS = [
  "from-slate-900 via-violet-900 to-indigo-950",
  "from-zinc-900 via-purple-900 to-fuchsia-950",
  "from-neutral-900 via-emerald-900 to-teal-950",
  "from-stone-900 via-rose-900 to-pink-950",
  "from-gray-900 via-blue-900 to-cyan-950",
  "from-slate-900 via-amber-900 to-orange-950",
  "from-zinc-900 via-fuchsia-900 to-purple-950",
  "from-neutral-900 via-indigo-900 to-violet-950",
];

function hashSlug(slug: string): number {
  let h = 0;
  for (let i = 0; i < slug.length; i++) {
    h = (h * 31 + slug.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

export function getDomainGradient(slug: string): string {
  if (KNOWN_GRADIENTS[slug]) return KNOWN_GRADIENTS[slug];
  return FALLBACK_GRADIENTS[hashSlug(slug) % FALLBACK_GRADIENTS.length];
}

// ────────────────────────────────────────────────────────────────────────────────
// Card
// ────────────────────────────────────────────────────────────────────────────────

interface DomainCardProps {
  node: DomainNode;
  isExpanded: boolean;
  onClick: () => void;
  isSubject?: boolean;
}

const DomainCard = forwardRef<HTMLDivElement, DomainCardProps>(function DomainCard(
  { node, isExpanded, onClick, isSubject },
  ref,
) {
  const navigate = useNavigate();

  if (isSubject) {
    return (
      <motion.div
        ref={ref}
        layout
        whileHover={{ y: -2 }}
        onClick={() => navigate(`/s/${node.slug}`)}
        className="rounded-xl aspect-[16/10] bg-ink-800 dark:bg-ink-900 border-l-4 border-accent dark:border-neon-violet hover:bg-ink-700 dark:hover:bg-ink-800 transition-all p-5 cursor-pointer flex flex-col justify-between shadow-lg shadow-black/20"
      >
        <div className="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-accent/15 dark:bg-neon-violet/15 text-accent dark:text-neon-violet">
          <BookOpen size={18} />
        </div>
        <div>
          <div className="text-lg font-medium text-white leading-snug">
            {node.title}
          </div>
          <div className="mt-1 text-xs text-ink-400 tracking-wider uppercase">
            Subject &rarr;
          </div>
        </div>
      </motion.div>
    );
  }

  const gradient = getDomainGradient(node.slug);

  return (
    <motion.div
      ref={ref}
      layout
      whileHover={{ y: -3 }}
      onClick={onClick}
      className={[
        "group relative overflow-hidden rounded-2xl aspect-[16/10] cursor-pointer transition-all duration-300 shadow-xl shadow-black/30",
        `bg-gradient-to-br ${gradient}`,
        isExpanded
          ? "ring-2 ring-neon-violet ring-offset-2 ring-offset-ink-50 dark:ring-offset-ink-950 shadow-[0_0_30px_rgba(168,85,247,0.4)]"
          : "hover:ring-2 hover:ring-accent/70 hover:ring-offset-2 hover:ring-offset-ink-50 dark:hover:ring-offset-ink-950",
      ].join(" ")}
    >
      <img
        src={`/api/images/domains/${node.slug}`}
        onLoad={(e) => {
          e.currentTarget.style.opacity = "0.35";
        }}
        onError={(e) => {
          e.currentTarget.style.display = "none";
        }}
        className="absolute inset-0 w-full h-full object-cover opacity-0 transition-opacity duration-500 pointer-events-none"
        alt=""
      />

      <div
        className="absolute inset-0 opacity-[0.08] pointer-events-none mix-blend-overlay"
        style={{
          backgroundImage:
            "linear-gradient(to right, white 1px, transparent 1px), linear-gradient(to bottom, white 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      <div
        className="absolute -top-16 -right-16 w-48 h-48 rounded-full opacity-30 blur-3xl pointer-events-none group-hover:opacity-50 transition-opacity duration-500"
        style={{ background: "#a855f7" }}
      />

      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent pointer-events-none" />

      <Link
        to={`/d/${node.slug}`}
        onClick={(e) => e.stopPropagation()}
        className="absolute top-4 right-4 z-10 text-xs text-white/70 hover:text-white border border-white/20 hover:border-white/50 rounded-full px-3 py-1 backdrop-blur-sm transition-colors"
      >
        View list &rarr;
      </Link>

      <div className="absolute left-5 right-5 bottom-5 z-10">
        <div className="text-2xl font-semibold text-white drop-shadow-lg leading-tight">
          {node.title}
        </div>
      </div>
    </motion.div>
  );
});

// ────────────────────────────────────────────────────────────────────────────────
// Browser
// ────────────────────────────────────────────────────────────────────────────────

interface DomainCardBrowserProps {
  nodes: DomainNode[];
}

interface ComputedLines {
  source: { x: number; y: number } | null;
  paths: Array<{ d: string; x: number; y: number }>;
  key: string;
}

export default function DomainCardBrowser({ nodes }: DomainCardBrowserProps) {
  const [expandedSlug, setExpandedSlug] = useState<string | null>(null);
  const navigate = useNavigate();
  const expandedNode = nodes.find((n) => n.slug === expandedSlug) ?? null;

  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const parentRefs = useRef<Record<string, HTMLDivElement | null>>({});
  // Scoped per parent slug so a cross-fade between two expansions can't have
  // their child refs collide on the same array indices.
  const childRefs = useRef<Record<string, (HTMLDivElement | null)[]>>({});

  const [lines, setLines] = useState<ComputedLines>({
    source: null,
    paths: [],
    key: "",
  });

  // Compute connector paths from the clicked parent card to each child card,
  // all expressed in the wrapper div's local coordinate space. Wrapper is the
  // shared positioned ancestor for both the parent grid AND the expanded row,
  // so a single SVG positioned absolutely inside it can render the lines
  // without being clipped by the height-animating <motion.div> below.
  useLayoutEffect(() => {
    if (!expandedNode) {
      setLines({ source: null, paths: [], key: "" });
      return;
    }

    const compute = () => {
      const wrapper = wrapperRef.current;
      if (!wrapper) return;
      const wrapperRect = wrapper.getBoundingClientRect();
      const parentEl = parentRefs.current[expandedNode.slug];

      let sourceX = wrapper.offsetWidth / 2;
      let sourceY = 0;
      if (parentEl) {
        const pRect = parentEl.getBoundingClientRect();
        sourceX = pRect.left + pRect.width / 2 - wrapperRect.left;
        sourceY = pRect.bottom - wrapperRect.top;
      }

      const refs = childRefs.current[expandedNode.slug] ?? [];

      // Establish the first-row baseline from the first attached child. Using
      // the smallest non-null offsetTop in the array makes us robust against
      // brief layout shifts during expansion.
      let firstRowTop: number | null = null;
      for (const el of refs) {
        if (!el) continue;
        const top = el.getBoundingClientRect().top - wrapperRect.top;
        if (firstRowTop === null || top < firstRowTop) firstRowTop = top;
      }

      const paths: Array<{ d: string; x: number; y: number }> = [];
      for (let i = 0; i < expandedNode.children.length; i++) {
        const el = refs[i];
        if (!el) continue;
        const elRect = el.getBoundingClientRect();
        const targetY = elRect.top - wrapperRect.top;
        if (firstRowTop !== null && targetY > firstRowTop + 4) continue;
        const targetX = elRect.left + elRect.width / 2 - wrapperRect.left;
        const midY = sourceY + (targetY - sourceY) * 0.55;
        const d = `M ${sourceX} ${sourceY} C ${sourceX} ${midY}, ${targetX} ${midY}, ${targetX} ${targetY}`;
        paths.push({ d, x: targetX, y: targetY });
      }
      setLines({
        source: { x: sourceX, y: sourceY },
        paths,
        key: expandedNode.slug,
      });
    };

    compute();

    const ro = new ResizeObserver(compute);
    if (wrapperRef.current) ro.observe(wrapperRef.current);
    const parentEl = parentRefs.current[expandedNode.slug];
    if (parentEl) ro.observe(parentEl);
    (childRefs.current[expandedNode.slug] ?? []).forEach(
      (el) => el && ro.observe(el),
    );
    return () => ro.disconnect();
  }, [expandedNode]);

  return (
    <div ref={wrapperRef} className="relative space-y-2">
      {/* Parent row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {nodes.map((node) => (
          <DomainCard
            key={node.slug}
            ref={(el) => {
              parentRefs.current[node.slug] = el;
            }}
            node={node}
            isExpanded={expandedSlug === node.slug}
            onClick={() => {
              if (node.children.length === 0) {
                navigate(`/d/${node.slug}`);
                return;
              }
              setExpandedSlug((prev) =>
                prev === node.slug ? null : node.slug,
              );
            }}
          />
        ))}
      </div>

      {/* Connector SVG — sibling of (not inside) the height-animated wrapper,
          so it isn't clipped by overflow:hidden during expand/collapse. */}
      {expandedNode && (
        <svg
          aria-hidden
          className="absolute inset-0 w-full h-full pointer-events-none"
          style={{ overflow: "visible" }}
        >
          {lines.source && (
            <motion.circle
              key={`${lines.key}-src`}
              cx={lines.source.x}
              cy={lines.source.y}
              r={4}
              fill="#a855f7"
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              style={{ filter: "drop-shadow(0 0 6px #a855f7)" }}
            />
          )}
          {lines.paths.map((p, i) => (
            <g key={`${lines.key}-${i}`}>
              <motion.path
                d={p.d}
                stroke="#a855f7"
                strokeWidth={1.5}
                fill="none"
                strokeLinecap="round"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 0.9 }}
                transition={{
                  duration: 0.6,
                  delay: i * 0.08,
                  ease: "easeOut",
                }}
                style={{
                  filter:
                    "drop-shadow(0 0 6px #a855f7) drop-shadow(0 0 12px #a855f7)",
                }}
              />
              <motion.circle
                cx={p.x}
                cy={p.y}
                r={3}
                fill="#a855f7"
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: i * 0.08 + 0.5 }}
                style={{ filter: "drop-shadow(0 0 4px #a855f7)" }}
              />
            </g>
          ))}
        </svg>
      )}

      {/* Expanded children — height-animated. No SVG inside.
          mode="popLayout" drops the exiting wrapper out of layout flow
          immediately so the entering one snaps to its final slot on the
          first frame; this gives the layout effect correct positions for
          the new children without waiting for the exit animation. */}
      <AnimatePresence initial={false} mode="popLayout">
        {expandedNode && expandedNode.children.length > 0 && (
          <motion.div
            key={expandedNode.slug}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="pt-20 pb-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {expandedNode.children.map((child, i) => {
                  const isSubject = child.children.length === 0;
                  const slug = expandedNode.slug;
                  return (
                    <motion.div
                      key={child.slug}
                      ref={(el) => {
                        if (!childRefs.current[slug]) {
                          childRefs.current[slug] = [];
                        }
                        childRefs.current[slug][i] = el;
                      }}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{
                        duration: 0.4,
                        delay: 0.2,
                        ease: "easeOut",
                      }}
                    >
                      <DomainCard
                        node={child}
                        isExpanded={false}
                        isSubject={isSubject}
                        onClick={() => {
                          if (isSubject) {
                            navigate(`/s/${child.slug}`);
                          } else {
                            navigate(`/d/${child.slug}`);
                          }
                        }}
                      />
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

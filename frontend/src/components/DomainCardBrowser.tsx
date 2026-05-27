import { useState } from "react";
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
// Electric lines connector
// ────────────────────────────────────────────────────────────────────────────────

function ElectricLines({ count }: { count: number }) {
  if (count <= 0) return null;
  const width = 1000;
  const height = 80;
  const topX = width / 2;
  const topY = 0;
  // Compute evenly spaced bottom anchor points across the full width
  const positions = Array.from({ length: count }, (_, i) => {
    if (count === 1) return width / 2;
    const margin = width / (count + 1);
    return margin * (i + 1);
  });

  return (
    <div
      className="relative w-full pointer-events-none"
      style={{ height: `${height}px` }}
      aria-hidden
    >
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="absolute inset-0 w-full h-full"
      >
        {/* Top source dot */}
        <motion.circle
          cx={topX}
          cy={topY + 2}
          r={4}
          fill="#a855f7"
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          style={{ filter: "drop-shadow(0 0 6px #a855f7)" }}
        />

        {positions.map((x, i) => {
          const midY = height * 0.55;
          // Slight curve via cubic Bezier — bow outwards
          const d = `M ${topX} ${topY} C ${topX} ${midY}, ${x} ${midY}, ${x} ${height}`;
          return (
            <g key={i}>
              <motion.path
                d={d}
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
                cx={x}
                cy={height - 2}
                r={3}
                fill="#a855f7"
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: i * 0.08 + 0.5 }}
                style={{ filter: "drop-shadow(0 0 4px #a855f7)" }}
              />
            </g>
          );
        })}
      </svg>
    </div>
  );
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

function DomainCard({ node, isExpanded, onClick, isSubject }: DomainCardProps) {
  const navigate = useNavigate();

  if (isSubject) {
    return (
      <motion.div
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
  const childCount = node.children.length;

  return (
    <motion.div
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
      {/* Optional background image — only visible if it loads */}
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

      {/* Subtle grid texture */}
      <div
        className="absolute inset-0 opacity-[0.08] pointer-events-none mix-blend-overlay"
        style={{
          backgroundImage:
            "linear-gradient(to right, white 1px, transparent 1px), linear-gradient(to bottom, white 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      {/* Glow blob top-right */}
      <div
        className="absolute -top-16 -right-16 w-48 h-48 rounded-full opacity-30 blur-3xl pointer-events-none group-hover:opacity-50 transition-opacity duration-500"
        style={{ background: "#a855f7" }}
      />

      {/* Vignette */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent pointer-events-none" />

      {/* Top-right "View list" link */}
      <Link
        to={`/d/${node.slug}`}
        onClick={(e) => e.stopPropagation()}
        className="absolute top-4 right-4 z-10 text-xs text-white/70 hover:text-white border border-white/20 hover:border-white/50 rounded-full px-3 py-1 backdrop-blur-sm transition-colors"
      >
        View list &rarr;
      </Link>

      {/* Bottom-left content */}
      <div className="absolute left-5 right-5 bottom-5 z-10">
        <div className="text-[10px] uppercase tracking-[0.3em] text-white/50 mb-1.5">
          {childCount > 0
            ? `${childCount} ${childCount === 1 ? "topic" : "topics"}`
            : node.slug}
        </div>
        <div className="text-2xl font-semibold text-white drop-shadow-lg leading-tight">
          {node.title}
        </div>
      </div>
    </motion.div>
  );
}

// ────────────────────────────────────────────────────────────────────────────────
// Browser
// ────────────────────────────────────────────────────────────────────────────────

interface DomainCardBrowserProps {
  nodes: DomainNode[];
}

export default function DomainCardBrowser({ nodes }: DomainCardBrowserProps) {
  const [expandedSlug, setExpandedSlug] = useState<string | null>(null);
  const navigate = useNavigate();
  const expandedNode = nodes.find((n) => n.slug === expandedSlug) ?? null;

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {nodes.map((node) => (
          <DomainCard
            key={node.slug}
            node={node}
            isExpanded={expandedSlug === node.slug}
            onClick={() => {
              if (node.children.length === 0) {
                // Top-level node with no children — navigate to domain page
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

      <AnimatePresence initial={false}>
        {expandedNode && expandedNode.children.length > 0 && (
          <motion.div
            key={expandedNode.slug}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <ElectricLines count={expandedNode.children.length} />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 pt-2 pb-4">
              {expandedNode.children.map((child) => {
                const isSubject = child.children.length === 0;
                return (
                  <motion.div
                    key={child.slug}
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
                        // Children navigate rather than further nesting
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
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

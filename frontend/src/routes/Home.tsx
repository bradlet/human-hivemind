import { useEffect } from "react";
import { Link } from "react-router-dom";
import useSWR from "swr";
import {
  motion,
  useMotionValue,
  useTransform,
} from "framer-motion";
import { BookOpen, Cpu, GitFork, ChevronDown } from "lucide-react";
import { api } from "../lib/api";
import BrainSVG from "../components/BrainSVG";
import MatrixCanvas from "../components/MatrixCanvas";
import DomainCardBrowser from "../components/DomainCardBrowser";

export default function Home() {
  // Manually-driven progress 0→1. Scroll events at scrollY===0 are hijacked to
  // drive this; the page itself only scrolls once progress hits a boundary
  // (1 going down, 0 going up). Bidirectional — reversing scroll plays the
  // rotation in reverse so the user can scrub through it freely.
  const progressMV = useMotionValue(0);

  const rotateY = useTransform(progressMV, [0, 1], [0, 180]);
  const brainScale = useTransform(progressMV, [0, 0.5, 1.0], [0.9, 1.05, 0.95]);
  const scrollHintOpacity = useTransform(progressMV, [0, 0.2], [1, 0]);
  const headlineY = useTransform(progressMV, [0, 1], [0, -40]);

  // Matrix rain holds a constant opacity for the lifetime of the hero so it
  // stays visible when the user scrolls back up to the top.
  const MATRIX_OPACITY = 0.85;

  useEffect(() => {
    const WHEEL_SENSITIVITY = 0.0015;
    const TOUCH_SENSITIVITY = 0.004;
    const KEY_STEP = 0.12;
    let touchY = 0;

    // True if a scroll input with this directional sign at the current state
    // should be absorbed by the rotation instead of scrolling the page.
    const shouldHijack = (deltaY: number) => {
      if (window.scrollY > 0) return false;
      const p = progressMV.get();
      if (deltaY > 0 && p < 1) return true;
      if (deltaY < 0 && p > 0) return true;
      return false;
    };

    const apply = (delta: number) => {
      const next = Math.min(1, Math.max(0, progressMV.get() + delta));
      progressMV.set(next);
    };

    const onWheel = (e: WheelEvent) => {
      if (!shouldHijack(e.deltaY)) return;
      e.preventDefault();
      apply(e.deltaY * WHEEL_SENSITIVITY);
    };
    const onTouchStart = (e: TouchEvent) => {
      touchY = e.touches[0].clientY;
    };
    const onTouchMove = (e: TouchEvent) => {
      const cur = e.touches[0].clientY;
      const delta = touchY - cur;
      touchY = cur;
      if (!shouldHijack(delta)) return;
      e.preventDefault();
      apply(delta * TOUCH_SENSITIVITY);
    };
    const onKey = (e: KeyboardEvent) => {
      if ([" ", "ArrowDown", "PageDown"].includes(e.key)) {
        if (!shouldHijack(1)) return;
        e.preventDefault();
        apply(KEY_STEP);
      } else if (["ArrowUp", "PageUp"].includes(e.key)) {
        if (!shouldHijack(-1)) return;
        e.preventDefault();
        apply(-KEY_STEP);
      }
    };

    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchmove", onTouchMove, { passive: false });
    window.addEventListener("keydown", onKey);

    return () => {
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("touchstart", onTouchStart);
      window.removeEventListener("touchmove", onTouchMove);
      window.removeEventListener("keydown", onKey);
    };
  }, [progressMV]);

  const domains = useSWR("domains", api.domains);

  return (
    <div>
      {/* ─────────────────────────────────────────── HERO ─────────────────────────────────────────── */}
      <section className="relative h-screen">
        <div className="absolute inset-0 flex items-center justify-center overflow-hidden dark:bg-ink-950 bg-gradient-to-b from-ink-50 to-ink-100 dark:from-ink-950 dark:to-ink-900">
          {/* Matrix rain backdrop */}
          <MatrixCanvas opacity={MATRIX_OPACITY} />

          {/* Radial atmospheric overlays */}
          <div
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "radial-gradient(circle at 50% 45%, rgba(124,58,237,0.18), transparent 55%), radial-gradient(circle at 80% 80%, rgba(0,255,65,0.08), transparent 60%)",
            }}
          />
          {/* Vignette overlay — keep light so the matrix rain stays visible. */}
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-ink-50/40 via-transparent to-ink-50/10 dark:from-ink-950/40 dark:via-transparent dark:to-ink-950/20" />

          {/* Subtle grid texture */}
          <div
            className="pointer-events-none absolute inset-0 opacity-[0.07] dark:opacity-[0.12]"
            style={{
              backgroundImage:
                "linear-gradient(to right, currentColor 1px, transparent 1px), linear-gradient(to bottom, currentColor 1px, transparent 1px)",
              backgroundSize: "48px 48px",
              color: "#7c3aed",
            }}
          />

          {/* Centerpiece */}
          <div className="relative z-10 flex flex-col items-center text-center px-4">
            {/* Perspective MUST live on the parent of the rotating element —
                applied to the same element it has no effect and the rotation
                degenerates into a flat X-scale (the "squish"). */}
            <div
              style={{ perspective: "1400px", perspectiveOrigin: "50% 50%" }}
              className="text-accent dark:text-neon-violet drop-shadow-[0_0_30px_rgba(168,85,247,0.45)]"
            >
              <motion.div
                style={{
                  rotateY,
                  scale: brainScale,
                  transformStyle: "preserve-3d",
                  backfaceVisibility: "visible",
                }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1.2, ease: "easeOut" }}
              >
                <BrainSVG className="w-[320px] md:w-[400px] h-auto" />
              </motion.div>
            </div>

            <motion.div style={{ y: headlineY }} className="mt-20 max-w-3xl">
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4, duration: 0.8 }}
                className="text-[10px] uppercase tracking-[0.4em] text-accent dark:text-neon-green mb-4"
              >
                Human Hivemind
              </motion.div>
              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.55, duration: 0.9 }}
                className="text-4xl md:text-6xl font-light tracking-tight text-ink-50 leading-[1.05] [text-shadow:_0_2px_24px_rgba(0,0,0,0.6)]"
              >
                Knowledge, structured.{" "}
                <span className="text-accent dark:text-neon-violet">
                  For humans and machines.
                </span>
              </motion.h1>
              <motion.p
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 0.9 }}
                className="mt-6 text-base md:text-lg text-ink-200 max-w-2xl mx-auto [text-shadow:_0_1px_16px_rgba(0,0,0,0.7)]"
              >
                A free, open-source platform where anyone can learn anything —
                and where every course doubles as structured knowledge for AI.
              </motion.p>
            </motion.div>
          </div>

          {/* Scroll hint */}
          <motion.div
            style={{ opacity: scrollHintOpacity }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-ink-300 text-xs uppercase tracking-[0.3em]"
          >
            <span>Scroll to explore</span>
            <motion.span
              animate={{ y: [0, 6, 0] }}
              transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
            >
              <ChevronDown size={18} />
            </motion.span>
          </motion.div>
        </div>
      </section>

      {/* ─────────────────────────────────────────── ABOUT ─────────────────────────────────────────── */}
      <section className="relative max-w-3xl mx-auto px-4 py-24 sm:py-32">
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 h-px w-24 bg-gradient-to-r from-transparent via-accent to-transparent dark:via-neon-violet" />
        <div className="text-[10px] uppercase tracking-[0.4em] text-accent dark:text-neon-green mb-5">
          The Premise
        </div>
        <h2 className="text-3xl md:text-5xl font-light tracking-tight text-ink-900 dark:text-ink-50 leading-tight">
          The bridge between human knowledge and AI.
        </h2>
        <div className="mt-8 space-y-5 text-ink-700 dark:text-ink-300 text-base md:text-lg leading-relaxed">
          <p>
            Every subject on Human Hivemind is a structured course — an
            overview, an ordered set of lessons with explicit learning
            objectives, and a graph of prerequisites. Written, edited, and
            forked by humans, the way Wikipedia ought to teach.
          </p>
          <p>
            Every subject is also automatically compiled into a token-efficient
            AI representation. The same knowledge people write becomes the
            ground truth AI tutors and agents reach for — no parallel
            corpus, no drift, no opacity.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <FeatureCard
            icon={<BookOpen size={20} />}
            title="Structured Courses"
            body="Overviews, ordered lessons, learning objectives, and explicit prerequisite graphs."
          />
          <FeatureCard
            icon={<Cpu size={20} />}
            title="AI-Ready"
            body="Each course compiles to a compact, machine-readable form for agents and tutors."
          />
          <FeatureCard
            icon={<GitFork size={20} />}
            title="Forkable"
            body="Take any subject, fork it, rewrite it. Versioned, attributed, open source."
          />
        </div>
      </section>

      {/* ─────────────────────────────────── DOMAIN BROWSER PREVIEW ─────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <div className="mb-8 flex items-end justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-3xl font-semibold dark:text-ink-100 tracking-tight">Browse by Domain</h2>
            <p className="mt-2 text-sm text-ink-500 dark:text-ink-400">
              Click a domain to explore what's inside. Click "View list" for the traditional view.
            </p>
          </div>
          <Link
            to="/browse"
            className="text-sm text-accent dark:text-neon-violet hover:underline whitespace-nowrap"
          >
            See full browse &rarr;
          </Link>
        </div>
        {domains.data && <DomainCardBrowser nodes={domains.data.domains} />}
      </section>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="dark:bg-ink-900/50 bg-white/50 border border-ink-200 dark:border-ink-800 backdrop-blur-sm rounded-2xl p-6 transition-colors hover:border-accent/40 dark:hover:border-neon-violet/40">
      <div className="inline-flex items-center justify-center w-9 h-9 rounded-lg bg-accent/10 dark:bg-neon-violet/10 text-accent dark:text-neon-violet mb-4">
        {icon}
      </div>
      <h3 className="text-base font-semibold text-ink-900 dark:text-ink-50">
        {title}
      </h3>
      <p className="mt-2 text-sm text-ink-600 dark:text-ink-400 leading-relaxed">
        {body}
      </p>
    </div>
  );
}


import { useEffect, useRef } from "react";

type Props = {
  opacity: number;
  className?: string;
};

const FONT_SIZE = 14;
const TRAIL_FADE = "rgba(0, 0, 0, 0.05)";
const RAIN_COLOR = "#00ff41";

/**
 * Matrix-style binary rain on a canvas background.
 * - Trail effect via translucent black overlay each tick.
 * - Columns recomputed on resize via ResizeObserver.
 * - When opacity collapses, the component unmounts the canvas and halts the RAF loop.
 */
export default function MatrixCanvas({ opacity, className }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let drops: number[] = [];
    let rafId = 0;
    // Fractional cells advanced per frame. 1.0 = one cell/frame (~60 cells/sec).
    const FALL_SPEED = 0.22;
    // Probability per frame of swapping the character at a given column.
    const GLYPH_CHANGE_PROB = 0.06;
    const glyphs: string[] = [];

    const resize = () => {
      const { clientWidth, clientHeight } = canvas;
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(clientWidth * dpr);
      canvas.height = Math.floor(clientHeight * dpr);
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
      const columns = Math.max(1, Math.floor(clientWidth / FONT_SIZE));
      // Short negative offset so the rain is visible within the first second
      // of mount instead of waiting for drops to catch up from far above.
      drops = new Array(columns).fill(0).map(() => Math.random() * -15);
      glyphs.length = 0;
      for (let i = 0; i < columns; i++) {
        glyphs.push(Math.random() < 0.5 ? "0" : "1");
      }
      // Clear background fresh
      ctx.fillStyle = "#000";
      ctx.fillRect(0, 0, clientWidth, clientHeight);
    };

    resize();

    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const tick = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;

      // Trail fade
      ctx.fillStyle = TRAIL_FADE;
      ctx.fillRect(0, 0, width, height);

      ctx.fillStyle = RAIN_COLOR;
      ctx.font = `${FONT_SIZE}px ui-monospace, SFMono-Regular, Menlo, monospace`;
      ctx.textBaseline = "top";

      for (let i = 0; i < drops.length; i++) {
        if (Math.random() < GLYPH_CHANGE_PROB) {
          glyphs[i] = Math.random() < 0.5 ? "0" : "1";
        }
        const x = i * FONT_SIZE;
        const y = drops[i] * FONT_SIZE;
        ctx.fillText(glyphs[i], x, y);

        if (y > height && Math.random() > 0.985) {
          drops[i] = 0;
        } else {
          drops[i] += FALL_SPEED;
        }
      }

      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafId);
      ro.disconnect();
    };
  }, []);

  if (opacity <= 0.01) return null;

  return (
    <canvas
      ref={canvasRef}
      className={
        "absolute inset-0 w-full h-full pointer-events-none " + (className ?? "")
      }
      style={{ opacity }}
    />
  );
}

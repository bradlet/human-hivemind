type Props = { className?: string };

/**
 * Brain silhouette rendered as a CSS mask so the parent's `color` tints it.
 * Glow comes from stacked `drop-shadow` filters that inherit `currentColor`,
 * matching the violet/neon-violet hue used elsewhere on the hero.
 */
export default function BrainSVG({ className }: Props) {
  const maskStyle: React.CSSProperties = {
    maskImage: "url(/brain-silhouette.svg)",
    WebkitMaskImage: "url(/brain-silhouette.svg)",
    maskRepeat: "no-repeat",
    WebkitMaskRepeat: "no-repeat",
    maskPosition: "center",
    WebkitMaskPosition: "center",
    maskSize: "contain",
    WebkitMaskSize: "contain",
    backgroundColor: "currentColor",
    filter:
      "drop-shadow(0 0 6px currentColor) drop-shadow(0 0 16px currentColor) drop-shadow(0 0 32px currentColor)",
  };

  return (
    <div
      role="img"
      aria-label="Stylized brain"
      className={"aspect-[800/660] " + (className ?? "")}
      style={maskStyle}
    />
  );
}

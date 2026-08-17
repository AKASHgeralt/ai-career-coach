/**
 * Procedural wireframe artwork. Everything here is generated SVG — no image
 * assets, no external libraries — so it stays sharp at any size and inherits
 * the accent colour from the stylesheet.
 */

const ACCENT = '#4da6ff'

/* A ridgeline / topographic massif. Stacked contour lines whose profile is a
   sum of gaussians, each row nudged forward to read as depth. */
export function WireTerrain({ lines = 26, className = '', opacity = 1 }) {
  const W = 1200
  const H = 420
  const steps = 96

  const paths = []
  for (let i = 0; i < lines; i++) {
    const depth = i / (lines - 1)              // 0 = far, 1 = near
    const baseY = H * (0.30 + depth * 0.62)
    const amp = (1 - depth * 0.42) * H * 0.34

    const pts = []
    for (let s = 0; s <= steps; s++) {
      const t = s / steps
      const peak =
        Math.exp(-Math.pow((t - 0.50) * 3.1, 2)) * 1.00 +
        Math.exp(-Math.pow((t - 0.27) * 6.4, 2)) * 0.46 +
        Math.exp(-Math.pow((t - 0.73) * 6.9, 2)) * 0.40 +
        Math.exp(-Math.pow((t - 0.88) * 9.0, 2)) * 0.22
      const jitter =
        Math.sin(t * 21 + i * 1.7) * 0.030 +
        Math.sin(t * 43 + i * 0.9) * 0.014
      const y = baseY - (peak + jitter) * amp
      pts.push(`${(t * W).toFixed(1)},${y.toFixed(1)}`)
    }
    paths.push({ d: `M ${pts.join(' L ')}`, depth })
  }

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="xMidYMax slice"
      className={className}
      style={{ opacity }}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="terrainFade" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={ACCENT} stopOpacity="0" />
          <stop offset="18%" stopColor={ACCENT} stopOpacity="1" />
          <stop offset="82%" stopColor={ACCENT} stopOpacity="1" />
          <stop offset="100%" stopColor={ACCENT} stopOpacity="0" />
        </linearGradient>
      </defs>
      {paths.map(({ d, depth }, i) => (
        <path
          key={i}
          d={d}
          fill="none"
          stroke="url(#terrainFade)"
          strokeWidth={0.6 + depth * 0.9}
          opacity={0.14 + depth * 0.5}
        />
      ))}
    </svg>
  )
}

/* A glowing wireframe tube — stacked ellipses along an axis with a hot core,
   echoing the cylinder motif in the reference. */
export function WireTube({ rings = 16, className = '', flip = false }) {
  const W = 320
  const H = 220
  const rx = 26
  const ry = 58
  const stepX = 15
  const startX = 44
  const cy = H / 2

  const items = []
  for (let i = 0; i < rings; i++) {
    const t = i / (rings - 1)
    items.push({
      cx: startX + i * stepX,
      rx: rx * (1 - t * 0.12),
      ry: ry * (1 - t * 0.18),
      o: 0.55 - t * 0.4,
    })
  }

  const last = items[items.length - 1]

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className={className}
      style={{ transform: flip ? 'scaleX(-1)' : undefined }}
      aria-hidden="true"
    >
      <defs>
        <radialGradient id="tubeCore">
          <stop offset="0%" stopColor="#dff0ff" stopOpacity="0.95" />
          <stop offset="35%" stopColor={ACCENT} stopOpacity="0.55" />
          <stop offset="100%" stopColor={ACCENT} stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* longitudinal edges */}
      <path
        d={`M ${items[0].cx} ${cy - ry} L ${last.cx} ${cy - last.ry}`}
        stroke={ACCENT} strokeWidth="0.8" fill="none" opacity="0.4"
      />
      <path
        d={`M ${items[0].cx} ${cy + ry} L ${last.cx} ${cy + last.ry}`}
        stroke={ACCENT} strokeWidth="0.8" fill="none" opacity="0.4"
      />

      {items.map(({ cx, rx: r, ry: y, o }, i) => (
        <ellipse
          key={i}
          cx={cx} cy={cy} rx={r} ry={y}
          fill="none" stroke={ACCENT} strokeWidth="0.9" opacity={o}
        />
      ))}

      {/* hot mouth */}
      <ellipse cx={items[0].cx} cy={cy} rx={rx} ry={ry} fill="url(#tubeCore)" />
      <ellipse
        cx={items[0].cx} cy={cy} rx={rx} ry={ry}
        fill="none" stroke="#cfe8ff" strokeWidth="1.2" opacity="0.85"
      />
    </svg>
  )
}

/* Small ringed marker used as a decorative "hotspot", as seen dotted around
   the reference scenes. Purely ornamental. */
export function Hotspot({ className = '', size = 26 }) {
  return (
    <span
      className={`hotspot inline-flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <span
        style={{
          width: 3, height: 3, borderRadius: 999,
          background: ACCENT, boxShadow: `0 0 8px ${ACCENT}`,
        }}
      />
    </span>
  )
}

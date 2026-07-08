import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'

interface Feature { type: string; properties: { LEVEL3_COD: string; LEVEL3_NAM: string }; geometry: GeoJSON.Geometry }

/** A small world map on the species card: the species' native TDWG regions filled in
 *  its subfamily colour, introduced regions dashed. Hover a region for its name — so
 *  the opaque codes (CMN, GAB…) become legible geography. */
export function RangeMap({ native, introduced, color }: {
  native: string[]; introduced: string[]; color: string
}) {
  const wrap = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [hover, setHover] = useState<{ name: string; x: number; y: number } | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch('/data/tdwg_level3.geojson').then((r) => r.json()).then((geo) => {
      if (cancelled || !wrap.current || !svgRef.current) return
      const W = wrap.current.clientWidth
      const H = wrap.current.clientHeight
      const nat = new Set(native)
      const intro = new Set(introduced)
      const features = geo.features as Feature[]
      const svg = d3.select(svgRef.current).attr('viewBox', `0 0 ${W} ${H}`)
      svg.selectAll('*').remove()
      // zoom the map to the species' range (native + introduced) with padding for
      // context, so a single-region endemic fills the frame instead of a lost speck.
      const rangeCodes = new Set([...native, ...introduced])
      const rangeFeats = features.filter((f) => rangeCodes.has(f.properties.LEVEL3_COD))
      const fitTarget = { type: 'FeatureCollection',
        features: rangeFeats.length ? rangeFeats : features } as never
      const pad = Math.min(W, H) * 0.22
      const projection = d3.geoNaturalEarth1()
        .fitExtent([[pad, pad], [W - pad, H - pad]], fitTarget)
      const path = d3.geoPath(projection)
      const isNat = (d: Feature) => nat.has(d.properties.LEVEL3_COD)
      const isIntro = (d: Feature) => intro.has(d.properties.LEVEL3_COD)
      const g = svg.append('g')
      g.selectAll('path').data(features).join('path')
        .attr('d', path as never)
        .attr('fill', (d) => (isNat(d) ? color : isIntro(d) ? '#2a3120' : '#141a11'))
        .attr('stroke', (d) => (isIntro(d) ? color : '#0d110c'))
        .attr('stroke-dasharray', (d) => (isIntro(d) ? '2,2' : 'none'))
        .attr('stroke-width', (d) => (isNat(d) || isIntro(d) ? 0.8 : 0.3))
        .on('mousemove', function (event, d) {
          if (!isNat(d) && !isIntro(d)) return
          d3.select(this).attr('stroke', '#EDF0E2').attr('stroke-width', 1.1).raise()
          const [x, y] = d3.pointer(event, wrap.current)
          setHover({ name: d.properties.LEVEL3_NAM + (isIntro(d) ? ' · introduced' : ''), x, y })
        })
        .on('mouseleave', function (_e, d) {
          d3.select(this).attr('stroke', isIntro(d) ? color : '#0d110c').attr('stroke-width', isNat(d) || isIntro(d) ? 0.8 : 0.3)
          setHover(null)
        })
      // drop only true frame-spanning antimeridian smears (higher threshold than the
      // world maps, since a zoomed continental view has legitimately large regions)
      requestAnimationFrame(() => {
        g.selectAll<SVGPathElement, unknown>('path').each(function () {
          try { if (this.getBBox().width > W * 0.92) this.remove() } catch { /* detached */ }
        })
      })
    })
    return () => { cancelled = true }
  }, [native, introduced, color])

  return (
    <div ref={wrap} style={{
      position: 'relative', width: '100%', height: 210, background: 'var(--panel)',
      border: '1px solid var(--hairline)', borderRadius: 9, overflow: 'hidden',
    }}>
      <svg ref={svgRef} style={{ width: '100%', height: '100%', display: 'block' }} />
      {hover && (
        <div style={{
          position: 'absolute', left: hover.x + 12, top: hover.y + 10, pointerEvents: 'none',
          background: 'var(--ground-raised)', border: '1px solid var(--hairline)', borderRadius: 6,
          padding: '4px 8px', fontSize: 11.5, whiteSpace: 'nowrap', zIndex: 3,
        }}>{hover.name}</div>
      )}
    </div>
  )
}

import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { api } from '../api/client'
import type { RegionRichness } from '../api/types'
import { RegionPanel } from './RegionPanel'
import { Detail } from './Catalogue'

interface Feature {
  type: string
  properties: { LEVEL3_COD: string; LEVEL3_NAM: string }
  geometry: GeoJSON.Geometry
}
interface Hover { name: string; richness: number; rainfall: number | null; x: number; y: number }
type Layer = 'richness' | 'rainfall'

// Two views of the same geography. Flip between them and the wet tropics and the
// palm-diversity hotspots light up in the same places — the correlation, shown.
const LAYERS: Record<Layer, {
  label: string; value: (r: RegionRichness) => number | null; ramp: string[]; fmt: (v: number) => string
}> = {
  richness: {
    label: 'Native palm species per region',
    value: (r) => r.richness,
    ramp: ['#1B2415', '#2E6B3E', '#7FB86A', '#E7C766'],
    fmt: (v) => `${v}`,
  },
  rainfall: {
    label: 'Mean annual rainfall (mm)',
    value: (r) => r.rainfall,
    ramp: ['#20180F', '#6E5A2E', '#2E8A7E', '#6FC7E0'],
    fmt: (v) => v.toLocaleString(),
  },
}

/** World map of palm species richness by TDWG botanical country, with a rainfall
 *  overlay — the diversity reveal (Borneo, Colombia, New Guinea light up) and the
 *  wet-tropics correlation behind it. The hover always reports both numbers, so the
 *  correlation reads at a glance whichever layer colours the map. */
export function AtlasMap({ onSeeOnTree }: { onSeeOnTree?: (slug: string) => void }) {
  const wrap = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const cache = useRef<{ rows: RegionRichness[]; geo: { features: Feature[] } } | null>(null)
  const [hover, setHover] = useState<Hover | null>(null)
  const [max, setMax] = useState(0)
  const [layer, setLayer] = useState<Layer>('richness')
  const [region, setRegion] = useState<{ code: string; name: string } | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const cfg = LAYERS[layer]

    const draw = (rows: RegionRichness[], geo: { features: Feature[] }) => {
      if (cancelled || !wrap.current || !svgRef.current) return
      const byCode = new Map(rows.map((r) => [r.code, r]))
      const maxV = d3.max(rows, (r) => cfg.value(r) ?? 0) ?? 1
      setMax(maxV)

      const W = wrap.current.clientWidth
      const H = wrap.current.clientHeight
      const svg = d3.select(svgRef.current).attr('viewBox', `0 0 ${W} ${H}`)
      svg.selectAll('*').remove()

      const features = geo.features
      const projection = d3.geoNaturalEarth1()
        .fitSize([W, H - 8], { type: 'FeatureCollection', features } as never)
      const path = d3.geoPath(projection)
      const color = d3.scaleSequentialSqrt<string>()
        .domain([0, maxV])
        .interpolator(d3.interpolateRgbBasis(cfg.ramp))

      const g = svg.append('g')
      g.selectAll('path')
        .data(features)
        .join('path')
        .attr('d', path as never)
        .attr('fill', (d) => {
          const row = byCode.get(d.properties.LEVEL3_COD)
          const v = row ? cfg.value(row) : null
          return v != null && v > 0 ? color(v) : '#171C12'
        })
        .attr('stroke', '#0D110C')
        .attr('stroke-width', 0.4)
        .style('cursor', 'pointer')
        .on('mousemove', function (event, d) {
          const [x, y] = d3.pointer(event, wrap.current)
          d3.select(this).attr('stroke', '#D9B25A').attr('stroke-width', 1).raise()
          const row = byCode.get(d.properties.LEVEL3_COD)
          setHover({ name: d.properties.LEVEL3_NAM, richness: row?.richness ?? 0, rainfall: row?.rainfall ?? null, x, y })
        })
        .on('mouseleave', function () {
          d3.select(this).attr('stroke', '#0D110C').attr('stroke-width', 0.4)
          setHover(null)
        })
        .on('click', (_e, d) => setRegion({ code: d.properties.LEVEL3_COD, name: d.properties.LEVEL3_NAM }))

      // Drop antimeridian-smeared / degenerate polygons after layout (getBBox reads 0
      // if measured before paint).
      requestAnimationFrame(() => {
        g.selectAll<SVGPathElement, unknown>('path').each(function () {
          try { if (this.getBBox().width > W * 0.6) this.remove() } catch { /* detached */ }
        })
      })
    }

    if (cache.current) {
      draw(cache.current.rows, cache.current.geo)
    } else {
      Promise.all([
        api.ranges(),
        fetch('/data/tdwg_level3.geojson').then((r) => r.json()),
      ]).then(([rows, geo]) => {
        if (cancelled) return
        cache.current = { rows: rows as RegionRichness[], geo }
        draw(rows as RegionRichness[], geo)
      })
    }
    return () => { cancelled = true }
  }, [layer])

  const cfg = LAYERS[layer]
  return (
    <div ref={wrap} style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height: '100%', display: 'block' }} />

      {/* layer toggle */}
      <div style={{ position: 'absolute', top: 18, left: 18, zIndex: 6 }}>
        <div className="seg" style={{ fontSize: 12 }}>
          <button className={layer === 'richness' ? 'active' : ''} onClick={() => setLayer('richness')}>Palm richness</button>
          <button className={layer === 'rainfall' ? 'active' : ''} onClick={() => setLayer('rainfall')}>Rainfall</button>
        </div>
      </div>

      {hover && (() => {
        // both numbers, active layer first — so the correlation reads in one glance
        const rich = hover.richness > 0 ? `${hover.richness} native palm species` : 'no native palms'
        const rain = hover.rainfall != null ? `${hover.rainfall.toLocaleString()} mm rain / yr` : null
        const lines = (layer === 'rainfall' ? [rain, rich] : [rich, rain]).filter(Boolean) as string[]
        return (
          <div style={{
            position: 'absolute', left: hover.x + 14, top: hover.y + 12, pointerEvents: 'none',
            background: 'var(--ground-raised)', border: '1px solid var(--hairline)',
            borderRadius: 8, padding: '8px 11px', fontSize: 12.5, maxWidth: 230, zIndex: 5,
          }}>
            <div style={{ fontWeight: 700 }}>{hover.name}</div>
            {lines.map((t, i) => (
              <div key={i} style={{
                color: i === 0 ? 'var(--ink)' : 'var(--ink-faint)', fontFamily: 'var(--font-mono)',
                fontSize: 11, marginTop: i === 0 ? 3 : 1,
              }}>{t}</div>
            ))}
          </div>
        )
      })()}

      <div style={{
        position: 'absolute', left: 18, bottom: 16, fontSize: 11,
        color: 'var(--ink-muted)', fontFamily: 'var(--font-mono)',
      }}>
        <div style={{ letterSpacing: '.14em', textTransform: 'uppercase', fontSize: 9, marginBottom: 5, color: 'var(--ink-faint)' }}>
          {cfg.label}
        </div>
        <div style={{ width: 180, height: 9, borderRadius: 5, background: `linear-gradient(90deg,${cfg.ramp.join(',')})` }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', width: 180, marginTop: 3 }}>
          <span>0</span><span>{cfg.fmt(max)}</span>
        </div>
        <div style={{ fontSize: 9.5, color: 'var(--ink-faint)', marginTop: 7, maxWidth: 250, lineHeight: 1.4 }}>
          {layer === 'rainfall'
            ? 'WorldClim bio12, mean per region. Palm diversity peaks in the wet tropics — with dry-adapted exceptions.'
            : 'Diversity peaks in the ever-wet tropics; toggle Rainfall to see why.'}
        </div>
      </div>

      {region && (
        <RegionPanel code={region.code} name={region.name} onSelect={setSelected} onClose={() => setRegion(null)} />
      )}
      {selected && (
        <aside style={{
          position: 'absolute', top: 0, right: 0, bottom: 0, width: 460, zIndex: 20,
          background: 'var(--ground)', borderLeft: '1px solid var(--hairline)',
          boxShadow: '-18px 0 40px rgba(0,0,0,.5)', display: 'flex', flexDirection: 'column',
        }}>
          <button onClick={() => setSelected(null)} style={{
            alignSelf: 'flex-end', margin: 10, background: 'var(--panel)', color: 'var(--ink-muted)',
            border: '1px solid var(--hairline)', borderRadius: 7, padding: '5px 11px', cursor: 'pointer', fontSize: 13,
          }}>Close ✕</button>
          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}><Detail slug={selected} onSeeOnTree={onSeeOnTree} /></div>
        </aside>
      )}
    </div>
  )
}

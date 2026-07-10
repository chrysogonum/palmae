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
interface Hover { name: string; row: RegionRichness; x: number; y: number }
type Layer = 'richness' | 'rainfall' | 'anomaly' | 'roles'
type View = 'map' | 'scatter'
type Role = 'radiator' | 'incubator' | 'corridor' | 'accumulator'

// Our TDWG-level-3 mapping of the biogeographic roles from Kühnhäuser et al. 2025 —
// how each tropical-Asian region contributes to overall palm diversity. Approximate:
// a few TDWG botanical countries straddle two of the paper's bioregions.
const REGION_ROLE: Record<string, Role> = {
  BOR: 'radiator',
  MYA: 'incubator', THA: 'incubator', LAO: 'incubator', CBD: 'incubator', VIE: 'incubator', NWG: 'incubator', SUL: 'incubator',
  SUM: 'corridor', JAW: 'corridor', MLY: 'corridor', MOL: 'corridor',
  QLD: 'accumulator', NTA: 'accumulator', IND: 'accumulator', PHI: 'accumulator',
}
const ROLE_INFO: Record<Role, { color: string; label: string; desc: string }> = {
  radiator: { color: '#E0873C', label: 'Radiator', desc: 'generates & exports diversity' },
  incubator: { color: '#5FB07A', label: 'Incubator', desc: 'breeds diversity in isolation' },
  corridor: { color: '#6FA8D0', label: 'Corridor', desc: 'connects neighbouring regions' },
  accumulator: { color: '#B080C0', label: 'Accumulator', desc: 'acquires diversity from elsewhere' },
}

const RICH_RAMP = ['#1B2415', '#2E6B3E', '#7FB86A', '#E7C766']
const RAIN_RAMP = ['#20180F', '#6E5A2E', '#2E8A7E', '#6FC7E0']
// coldest-month mean temperature, cold → warm (matches the Palm Line)
const cmmtColor = d3.scaleLinear<string>()
  .domain([-5, 5, 12, 20, 28]).range(['#4C7BB0', '#8FBEDC', '#CBD9C4', '#8FBE6B', '#E0A63C']).clamp(true)
// richness × rainfall anomaly: palm-POOR (brown) ← 0 → palm-RICH for the rain (green)
const anomColor = d3.scaleLinear<string>()
  .domain([-0.6, 0, 0.6]).range(['#C6803C', '#2A2E22', '#5FC07D']).clamp(true)

const MAP_LAYERS: Record<'richness' | 'rainfall', { label: string; ramp: string[]; val: (r: RegionRichness) => number | null; fmt: (v: number) => string }> = {
  richness: { label: 'Native palm species per region', ramp: RICH_RAMP, val: (r) => r.richness, fmt: (v) => `${v}` },
  rainfall: { label: 'Mean annual rainfall (mm)', ramp: RAIN_RAMP, val: (r) => r.rainfall, fmt: (v) => v.toLocaleString() },
}

/** World map of palm richness with rainfall and richness×rainfall-anomaly layers, plus
 *  a scatter view. Shows the wet-tropics correlation and — controlling for frost and
 *  island area — where diversity departs from what rainfall predicts (the size/isolation
 *  signal of Kühnhäuser et al. 2025). */
export function AtlasMap({ onSeeOnTree }: { onSeeOnTree?: (slug: string) => void }) {
  const wrap = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const cache = useRef<{ rows: RegionRichness[]; geo: { features: Feature[] }; name: Map<string, string> } | null>(null)
  const [hover, setHover] = useState<Hover | null>(null)
  const [view, setView] = useState<View>('map')
  const [layer, setLayer] = useState<Layer>('richness')
  const [region, setRegion] = useState<{ code: string; name: string } | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const drawMap = (rows: RegionRichness[], geo: { features: Feature[] }) => {
      const byCode = new Map(rows.map((r) => [r.code, r]))
      const W = wrap.current!.clientWidth
      const H = wrap.current!.clientHeight
      const svg = d3.select(svgRef.current!).attr('viewBox', `0 0 ${W} ${H}`)
      svg.selectAll('*').remove()
      const features = geo.features
      const projection = d3.geoNaturalEarth1().fitSize([W, H - 8], { type: 'FeatureCollection', features } as never)
      const path = d3.geoPath(projection)

      let fill: (r: RegionRichness) => string
      if (layer === 'roles') {
        fill = (r) => { const role = REGION_ROLE[r.code]; return role ? ROLE_INFO[role].color : '#171C12' }
      } else if (layer === 'anomaly') {
        fill = (r) => (r.anomaly == null ? '#171C12' : anomColor(r.anomaly))
      } else {
        const cfg = MAP_LAYERS[layer]
        const maxV = d3.max(rows, (r) => cfg.val(r) ?? 0) ?? 1
        const scale = d3.scaleSequentialSqrt<string>().domain([0, maxV]).interpolator(d3.interpolateRgbBasis(cfg.ramp))
        fill = (r) => { const v = cfg.val(r); return v != null && v > 0 ? scale(v) : '#171C12' }
      }

      const g = svg.append('g')
      // track the currently-highlighted region so we clear it on the next move rather
      // than relying on a per-path mouseleave (which .raise() makes unreliable — that
      // left every swept-over region stuck lit)
      let lit: SVGPathElement | null = null
      const clear = () => { if (lit) { d3.select(lit).attr('stroke', '#0D110C').attr('stroke-width', 0.4); lit = null } }
      g.selectAll('path').data(features).join('path')
        .attr('d', path as never)
        .attr('fill', (d) => { const r = byCode.get(d.properties.LEVEL3_COD); return r ? fill(r) : '#171C12' })
        .attr('stroke', '#0D110C').attr('stroke-width', 0.4).style('cursor', 'pointer')
        .on('mousemove', function (event, d) {
          const [x, y] = d3.pointer(event, wrap.current)
          if (lit !== this) { clear(); d3.select(this).attr('stroke', '#D9B25A').attr('stroke-width', 1).raise(); lit = this as SVGPathElement }
          const r = byCode.get(d.properties.LEVEL3_COD)
          if (r) setHover({ name: d.properties.LEVEL3_NAM, row: r, x, y })
        })
        .on('click', (_e, d) => setRegion({ code: d.properties.LEVEL3_COD, name: d.properties.LEVEL3_NAM }))
      // moving onto open ocean (svg background, no region) or off the map clears it
      svg.on('mousemove', (event) => { if (event.target === svgRef.current) { clear(); setHover(null) } })
        .on('mouseleave', () => { clear(); setHover(null) })

      requestAnimationFrame(() => {
        g.selectAll<SVGPathElement, unknown>('path').each(function () {
          try { if (this.getBBox().width > W * 0.6) this.remove() } catch { /* detached */ }
        })
      })
    }

    const drawScatter = (rows: RegionRichness[], name: Map<string, string>) => {
      const W = wrap.current!.clientWidth
      const H = wrap.current!.clientHeight
      const svg = d3.select(svgRef.current!).attr('viewBox', `0 0 ${W} ${H}`)
      svg.selectAll('*').remove()
      svg.on('mousemove', null).on('mouseleave', null)  // drop the map view's svg-level handlers
      const m = { top: 34, right: 30, bottom: 48, left: 58 }
      const pts = rows.filter((r) => r.rainfall != null)
      const x = d3.scaleLinear().domain([0, (d3.max(pts, (r) => r.rainfall!) ?? 5000) * 1.02]).range([m.left, W - m.right])
      const y = d3.scaleLinear().domain([0, (d3.max(pts, (r) => r.richness) ?? 300) * 1.05]).range([H - m.bottom, m.top]).nice()

      const g = svg.append('g')
      // axes + faint gridlines
      const xa = d3.axisBottom(x).ticks(6).tickFormat((d) => `${(+d).toLocaleString()}`)
      const ya = d3.axisLeft(y).ticks(6)
      g.append('g').attr('transform', `translate(0,${H - m.bottom})`).call(xa)
        .call((s) => s.selectAll('text').attr('fill', 'var(--ink-faint)').attr('font-size', 10))
        .call((s) => s.selectAll('line,path').attr('stroke', 'var(--hairline)'))
      g.append('g').attr('transform', `translate(${m.left},0)`).call(ya)
        .call((s) => s.selectAll('text').attr('fill', 'var(--ink-faint)').attr('font-size', 10))
        .call((s) => s.selectAll('line,path').attr('stroke', 'var(--hairline)'))
      g.append('text').attr('x', (m.left + W - m.right) / 2).attr('y', H - 10).attr('text-anchor', 'middle')
        .attr('fill', 'var(--ink-muted)').attr('font-size', 11).text('Mean annual rainfall (mm)')
      g.append('text').attr('transform', `translate(15,${(m.top + H - m.bottom) / 2}) rotate(-90)`).attr('text-anchor', 'middle')
        .attr('fill', 'var(--ink-muted)').attr('font-size', 11).text('Native palm species')

      // trend over the eligible set (warm + sizeable) — the baseline the anomaly measures against
      const elig = pts.filter((r) => r.anomaly != null).slice().sort((a, b) => a.rainfall! - b.rainfall!)
      if (elig.length > 12) {
        const nb = 8, per = Math.ceil(elig.length / nb), pts2: [number, number][] = []
        for (let i = 0; i < elig.length; i += per) {
          const chunk = elig.slice(i, i + per)
          const mx = d3.mean(chunk, (r) => r.rainfall!)!
          const my = d3.median(chunk, (r) => r.richness)!
          pts2.push([mx, my])
        }
        g.append('path').datum(pts2).attr('fill', 'none').attr('stroke', 'var(--ink-faint)')
          .attr('stroke-width', 1.5).attr('stroke-dasharray', '4,3').attr('opacity', 0.7)
          .attr('d', d3.line<[number, number]>().x((d) => x(d[0])).y((d) => y(d[1])).curve(d3.curveMonotoneX))
      }

      // dots — colour by coldest-month temperature; dim the ones excluded from the anomaly
      g.selectAll('circle').data(pts).join('circle')
        .attr('cx', (r) => x(r.rainfall!)).attr('cy', (r) => y(r.richness))
        .attr('r', 3.6).attr('fill', (r) => (r.cmmt != null ? cmmtColor(r.cmmt) : '#4A5340'))
        .attr('stroke', '#0D110C').attr('stroke-width', 0.5)
        .attr('opacity', (r) => (r.anomaly != null ? 0.92 : 0.32)).style('cursor', 'pointer')
        .on('mousemove', function (event, r) {
          const [px, py] = d3.pointer(event, wrap.current)
          d3.select(this).attr('stroke', '#EDF0E2').attr('stroke-width', 1.3).attr('r', 5).raise()
          setHover({ name: name.get(r.code) ?? r.code, row: r, x: px, y: py })
        })
        .on('mouseleave', function () { d3.select(this).attr('stroke', '#0D110C').attr('stroke-width', 0.5).attr('r', 3.6); setHover(null) })
        .on('click', (_e, r) => setRegion({ code: r.code, name: name.get(r.code) ?? r.code }))

      // label the notable outliers + the biggest hotspots
      const byAnom = elig.slice().sort((a, b) => a.anomaly! - b.anomaly!)
      const labelSet = new Set([...byAnom.slice(0, 3), ...byAnom.slice(-3),
        ...pts.slice().sort((a, b) => b.richness - a.richness).slice(0, 3)].map((r) => r.code))
      g.selectAll('text.lbl').data(pts.filter((r) => labelSet.has(r.code))).join('text').attr('class', 'lbl')
        .attr('x', (r) => x(r.rainfall!) + 7).attr('y', (r) => y(r.richness) + 3)
        .attr('font-size', 10.5).attr('fill', 'var(--ink-muted)')
        .attr('font-style', 'italic').text((r) => name.get(r.code) ?? r.code)
    }

    const render = (c: { rows: RegionRichness[]; geo: { features: Feature[] }; name: Map<string, string> }) => {
      if (cancelled || !wrap.current || !svgRef.current) return
      if (view === 'scatter') drawScatter(c.rows, c.name)
      else drawMap(c.rows, c.geo)
    }

    if (cache.current) render(cache.current)
    else {
      Promise.all([api.ranges(), fetch('/data/tdwg_level3.geojson').then((r) => r.json())]).then(([rows, geo]) => {
        if (cancelled) return
        const name = new Map((geo.features as Feature[]).map((f) => [f.properties.LEVEL3_COD, f.properties.LEVEL3_NAM]))
        cache.current = { rows: rows as RegionRichness[], geo, name }
        render(cache.current)
      })
    }
    return () => { cancelled = true }
  }, [view, layer])

  return (
    <div ref={wrap} style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height: '100%', display: 'block' }} />

      {/* view + layer controls */}
      <div style={{ position: 'absolute', top: 18, left: 18, zIndex: 6, display: 'flex', gap: 10 }}>
        <div className="seg" style={{ fontSize: 12 }}>
          <button className={view === 'map' ? 'active' : ''} onClick={() => setView('map')}>Map</button>
          <button className={view === 'scatter' ? 'active' : ''} onClick={() => setView('scatter')}>Scatter</button>
        </div>
        {view === 'map' && (
          <div className="seg" style={{ fontSize: 12 }}>
            <button className={layer === 'richness' ? 'active' : ''} onClick={() => setLayer('richness')}>Palm richness</button>
            <button className={layer === 'rainfall' ? 'active' : ''} onClick={() => setLayer('rainfall')}>Rainfall</button>
            <button className={layer === 'anomaly' ? 'active' : ''} onClick={() => setLayer('anomaly')}>Anomaly</button>
            <button className={layer === 'roles' ? 'active' : ''} onClick={() => setLayer('roles')}>Roles</button>
          </div>
        )}
      </div>

      {hover && (() => {
        const r = hover.row
        const role = REGION_ROLE[r.code]
        const lines: string[] = []
        if (view === 'map' && layer === 'roles' && role) lines.push(`${ROLE_INFO[role].label} — ${ROLE_INFO[role].desc}`)
        lines.push(r.richness > 0 ? `${r.richness} native palm species` : 'no native palms')
        if (r.rainfall != null) lines.push(`${r.rainfall.toLocaleString()} mm rain / yr`)
        if (r.cmmt != null) lines.push(`coldest month ${r.cmmt}°C`)
        if (r.anomaly != null) lines.push(Math.abs(r.anomaly) < 0.15 ? 'about as many palms as rain predicts'
          : r.anomaly > 0 ? 'palm-RICH for its rainfall' : 'palm-POOR for its rainfall')
        // order: put the active metric first on the map
        if (view === 'map' && layer === 'rainfall' && r.rainfall != null) lines.unshift(lines.splice(1, 1)[0])
        return (
          <div style={{
            position: 'absolute', left: hover.x + 14, top: hover.y + 12, pointerEvents: 'none',
            background: 'var(--ground-raised)', border: '1px solid var(--hairline)',
            borderRadius: 8, padding: '8px 11px', fontSize: 12.5, maxWidth: 240, zIndex: 5,
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

      {/* legend — bottom-left over the map's ocean, but the scatter's origin lives there,
          so in scatter view it moves to the empty top-left (high-richness / low-rainfall) */}
      <div style={{
        position: 'absolute', fontSize: 11, color: 'var(--ink-muted)', fontFamily: 'var(--font-mono)',
        ...(view === 'scatter' ? { left: 74, top: 62 } : { left: 18, bottom: 16 }),
      }}>
        {view === 'scatter' ? (
          <>
            <div style={{ letterSpacing: '.14em', textTransform: 'uppercase', fontSize: 9, marginBottom: 5, color: 'var(--ink-faint)' }}>
              Coldest-month temperature
            </div>
            <div style={{ width: 180, height: 9, borderRadius: 5, background: 'linear-gradient(90deg,#4C7BB0,#8FBEDC,#CBD9C4,#8FBE6B,#E0A63C)' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', width: 180, marginTop: 3 }}><span>cold</span><span>warm</span></div>
            <div style={{ fontSize: 9.5, color: 'var(--ink-faint)', marginTop: 7, maxWidth: 300, lineHeight: 1.4 }}>
              One dot = one region. Dashed line = typical richness vs rainfall among frost-free, sizeable
              regions; dim dots (cold or tiny islands) are outside that comparison. Labels flag the outliers.
            </div>
          </>
        ) : layer === 'roles' ? (
          <>
            <div style={{ letterSpacing: '.14em', textTransform: 'uppercase', fontSize: 9, marginBottom: 6, color: 'var(--ink-faint)' }}>
              How Asian regions build palm diversity
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {(['radiator', 'incubator', 'corridor', 'accumulator'] as Role[]).map((k) => (
                <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                  <span style={{ width: 11, height: 11, borderRadius: 3, background: ROLE_INFO[k].color, flex: '0 0 auto' }} />
                  <span style={{ color: 'var(--ink)', fontSize: 11 }}>{ROLE_INFO[k].label}</span>
                  <span style={{ color: 'var(--ink-faint)', fontSize: 10.5 }}>· {ROLE_INFO[k].desc}</span>
                </div>
              ))}
            </div>
            <div style={{ fontSize: 9.5, color: 'var(--ink-faint)', marginTop: 7, maxWidth: 320, lineHeight: 1.4 }}>
              Region size &amp; isolation, not climate, drive Asian palm diversity — Kühnhäuser et al. 2025.
              Our approximate mapping of their bioregions onto TDWG botanical countries.
            </div>
          </>
        ) : layer === 'anomaly' ? (
          <>
            <div style={{ letterSpacing: '.14em', textTransform: 'uppercase', fontSize: 9, marginBottom: 5, color: 'var(--ink-faint)' }}>
              Richness vs rainfall (frost-free regions)
            </div>
            <div style={{ width: 180, height: 9, borderRadius: 5, background: 'linear-gradient(90deg,#C6803C,#2A2E22,#5FC07D)' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', width: 200, marginTop: 3 }}>
              <span>fewer palms</span><span>more</span>
            </div>
            <div style={{ fontSize: 9.5, color: 'var(--ink-faint)', marginTop: 7, maxWidth: 300, lineHeight: 1.4 }}>
              Grey = cold, tiny, or dry (excluded). Fewer-than-rainfall-predicts is the size/isolation
              signal — e.g. wet but palm-poor tropical Africa (Kühnhäuser et al. 2025). Exploratory; coarse at region scale.
            </div>
          </>
        ) : (
          <>
            <div style={{ letterSpacing: '.14em', textTransform: 'uppercase', fontSize: 9, marginBottom: 5, color: 'var(--ink-faint)' }}>
              {MAP_LAYERS[layer].label}
            </div>
            <div style={{ width: 180, height: 9, borderRadius: 5, background: `linear-gradient(90deg,${MAP_LAYERS[layer].ramp.join(',')})` }} />
            <div style={{ fontSize: 9.5, color: 'var(--ink-faint)', marginTop: 7, maxWidth: 260, lineHeight: 1.4 }}>
              {layer === 'rainfall'
                ? 'WorldClim bio12. Diversity peaks in the wet tropics — with dry-adapted exceptions.'
                : 'Diversity peaks in the ever-wet tropics; try Rainfall and Anomaly.'}
            </div>
          </>
        )}
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

import { useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'
import { api } from '../api/client'
import type { PalmLineData, RenegadeData } from '../api/types'
import { Detail } from './Catalogue'

interface Feature { type: string; properties: Record<string, unknown>; geometry: GeoJSON.Geometry }

// Coldest-month mean temperature → colour. The 2–8 °C frost band is the pale hinge:
// below it the world turns cold blue (few palms), above it warm green→gold (the
// tropical family). Reichgelt, West & Greenwood 2018.
const CMMT_STOPS: [number, string][] = [
  [-15, '#2E5E8F'], [-2, '#6CA6D9'], [2, '#D9E4EC'],
  [8, '#E7E2C6'], [16, '#83BE6B'], [30, '#E0A63C'],
]
const cmmtColor = d3.scaleLinear<string>()
  .domain(CMMT_STOPS.map((s) => s[0]))
  .range(CMMT_STOPS.map((s) => s[1]))
  .clamp(true)

/** The palm line — the money shot. Every native palm occurrence, coloured by the
 *  coldest-month mean temperature where it grows. The family hugs the warm side of
 *  the frost line; the renegades light up where they hold on past it. */
export function PalmLine({ onSeeOnTree }: { onSeeOnTree?: (slug: string) => void }) {
  const wrap = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [data, setData] = useState<PalmLineData | null>(null)
  const [reneg, setReneg] = useState<RenegadeData | null>(null)
  const [introduced, setIntroduced] = useState(false)
  const [focus, setFocus] = useState<string | null>(null)   // highlighted renegade slug
  const [selected, setSelected] = useState<string | null>(null)
  const [hover, setHover] = useState<{ sp: string; cmmt: number; x: number; y: number } | null>(null)

  useEffect(() => { api.renegades().then(setReneg).catch(() => {}) }, [])
  useEffect(() => { api.palmLine(introduced).then(setData).catch(() => {}) }, [introduced])

  const renegSet = useMemo(() => new Set(data?.renegadeSlugs ?? []), [data])

  useEffect(() => {
    if (!data || !wrap.current || !svgRef.current) return
    let cancelled = false
    fetch('/data/tdwg_level3.geojson').then((r) => r.json()).then((geo) => {
      if (cancelled || !wrap.current || !svgRef.current) return
      const W = wrap.current.clientWidth
      const H = wrap.current.clientHeight
      const svg = d3.select(svgRef.current).attr('viewBox', `0 0 ${W} ${H}`)
      svg.selectAll('*').remove()

      const features = geo.features as Feature[]
      const projection = d3.geoNaturalEarth1()
        .fitSize([W, H - 8], { type: 'FeatureCollection', features } as never)
      const path = d3.geoPath(projection)

      // muted land silhouette
      const land = svg.append('g')
      land.selectAll('path').data(features).join('path')
        .attr('d', path as never)
        .attr('fill', '#141A11').attr('stroke', '#0D110C').attr('stroke-width', 0.4)
      requestAnimationFrame(() => {
        land.selectAll<SVGPathElement, unknown>('path').each(function () {
          try { if (this.getBBox().width > W * 0.6) this.remove() } catch { /* detached */ }
        })
      })

      // occurrence points, coloured by CMMT (natives solid, introduced hollow)
      const pts = svg.append('g')
      pts.selectAll('circle').data(data.points).join('circle')
        .attr('cx', (d) => projection([d.lon, d.lat])?.[0] ?? -99)
        .attr('cy', (d) => projection([d.lon, d.lat])?.[1] ?? -99)
        .attr('r', (d) => (renegSet.has(d.sp) ? 2.6 : 1.5))
        .attr('fill', (d) => (d.native ? cmmtColor(d.cmmt) : 'none'))
        .attr('stroke', (d) => (d.native ? 'none' : cmmtColor(d.cmmt)))
        .attr('stroke-width', 0.8)
        .attr('opacity', (d) => (d.native ? 0.82 : 0.6))
        .style('cursor', 'pointer')
        .on('mousemove', function (event, d) {
          const [x, y] = d3.pointer(event, wrap.current)
          setHover({ sp: d.sp, cmmt: d.cmmt, x, y })
        })
        .on('mouseleave', () => setHover(null))
        .on('click', (_e, d) => setSelected(d.sp))

      // renegade rings on top
      svg.append('g').attr('class', 'reneg-layer')
        .selectAll('circle')
        .data(data.points.filter((d) => renegSet.has(d.sp)))
        .join('circle')
        .attr('cx', (d) => projection([d.lon, d.lat])?.[0] ?? -99)
        .attr('cy', (d) => projection([d.lon, d.lat])?.[1] ?? -99)
        .attr('r', 3.4).attr('fill', 'none')
        .attr('stroke', '#D9B25A').attr('stroke-width', 1)
        .attr('opacity', 0.9).style('pointer-events', 'none')
        .attr('data-sp', (d) => d.sp)
    })
    return () => { cancelled = true }
  }, [data, renegSet])

  // pulse the focused renegade's points
  useEffect(() => {
    const g = svgRef.current?.querySelector('.reneg-layer')
    if (!g) return
    g.querySelectorAll('circle').forEach((c) => {
      const on = focus && c.getAttribute('data-sp') === focus
      c.setAttribute('r', on ? '6' : '3.4')
      c.setAttribute('stroke-width', on ? '2' : '1')
      c.setAttribute('opacity', focus ? (on ? '1' : '0.25') : '0.9')
    })
  }, [focus, data])

  const band = data?.frostLine.band ?? [2, 8]

  return (
    <div ref={wrap} className="palmline" style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height: '100%', display: 'block' }} />

      {/* headline */}
      <div className="pl-headline">
        <div className="pl-eyebrow">The palm line</div>
        <h1 className="pl-title">Palms trace the frost line</h1>
        <p className="pl-lede">
          Every dot is a cleaned native occurrence, coloured by the coldest-month mean temperature where it
          grows. The family holds to the warm side of ~{band[0]}–{band[1]} °C — the frost line palms have
          marked in the fossil record for 50 million years. A few <span className="pl-reneg-word">renegades</span>{' '}
          (gold rings) break past it.
        </p>
        <label className="pl-toggle">
          <input type="checkbox" checked={introduced} onChange={(e) => setIntroduced(e.target.checked)} />
          Show introduced / naturalised points
        </label>
      </div>

      {/* CMMT legend with the frost band marked */}
      <div className="pl-legend">
        <div className="pl-legend-label">Coldest-month mean temperature</div>
        <div className="pl-legend-bar">
          <div className="pl-legend-grad" />
          <div className="pl-frost-band" title={`frost line ${band[0]}–${band[1]} °C`} />
        </div>
        <div className="pl-legend-ticks">
          <span>−15°</span><span className="pl-frost-tick">{band[0]}–{band[1]}° frost line</span><span>+30°C</span>
        </div>
        <div className="pl-derived">derived · WorldClim 2.1 × GBIF</div>
      </div>

      {/* renegades panel */}
      {reneg && (
        <aside className="pl-reneg-panel">
          <div className="pl-reneg-head">Renegades — palms past the line</div>
          <div className="pl-reneg-sub">
            Cold edge = the coldest-month mean across native occurrences (derived).
          </div>
          <div className="pl-reneg-list">
            {reneg.species.map((r) => (
              <button
                key={r.slug}
                className="pl-reneg-item"
                onMouseEnter={() => setFocus(r.slug)}
                onMouseLeave={() => setFocus(null)}
                onClick={() => setSelected(r.slug)}
              >
                <span className="pl-reneg-dot" style={{ background: r.color }} />
                <span className="pl-reneg-name">
                  <span className="pl-reneg-common">{r.common}</span>
                  <em className="pl-reneg-latin">{r.latin}</em>
                </span>
                <span className="pl-reneg-edge">
                  {r.cmmtMin != null ? `${r.cmmtMin > 0 ? '+' : ''}${r.cmmtMin.toFixed(1)}°` : '—'}
                </span>
              </button>
            ))}
          </div>
        </aside>
      )}

      {hover && (
        <div className="pl-tip" style={{ left: hover.x + 14, top: hover.y + 12 }}>
          <span className="pl-tip-cmmt" style={{ color: cmmtColor(hover.cmmt) }}>
            {hover.cmmt > 0 ? '+' : ''}{hover.cmmt.toFixed(1)} °C
          </span>
          <span className="pl-tip-label">coldest-month mean here</span>
        </div>
      )}

      {selected && (
        <aside className="pl-detail">
          <button className="pl-detail-close" onClick={() => setSelected(null)}>Close ✕</button>
          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}><Detail slug={selected} onSeeOnTree={onSeeOnTree} /></div>
        </aside>
      )}
    </div>
  )
}

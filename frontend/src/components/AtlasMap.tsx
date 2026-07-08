import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { api } from '../api/client'
import { RegionPanel } from './RegionPanel'
import { Detail } from './Catalogue'

interface Feature {
  type: string
  properties: { LEVEL3_COD: string; LEVEL3_NAM: string }
  geometry: GeoJSON.Geometry
}
interface Hover { name: string; code: string; richness: number; x: number; y: number }

/** World map of palm species richness by TDWG botanical country — the diversity
 *  reveal (Borneo, Colombia, New Guinea, Madagascar light up). */
export function AtlasMap({ onSeeOnTree }: { onSeeOnTree?: (slug: string) => void }) {
  const wrap = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [hover, setHover] = useState<Hover | null>(null)
  const [max, setMax] = useState(0)
  const [region, setRegion] = useState<{ code: string; name: string } | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      api.ranges(),
      fetch('/data/tdwg_level3.geojson').then((r) => r.json()),
    ]).then(([richness, geo]) => {
      if (cancelled || !wrap.current || !svgRef.current) return
      const byCode = new Map(richness.map((r) => [r.code, r.richness]))
      const maxR = d3.max(richness, (r) => r.richness) ?? 1
      setMax(maxR)

      const W = wrap.current.clientWidth
      const H = wrap.current.clientHeight
      const svg = d3.select(svgRef.current).attr('viewBox', `0 0 ${W} ${H}`)
      svg.selectAll('*').remove()

      const features = (geo.features as Feature[])
      const projection = d3.geoNaturalEarth1()
        .fitSize([W, H - 8], { type: 'FeatureCollection', features } as never)
      const path = d3.geoPath(projection)
      const color = d3.scaleSequentialSqrt<string>()
        .domain([0, maxR])
        .interpolator(d3.interpolateRgbBasis(['#1B2415', '#2E6B3E', '#7FB86A', '#E7C766']))

      const g = svg.append('g')
      g.selectAll('path')
        .data(features)
        .join('path')
        .attr('d', path as never)
        .attr('fill', (d) => {
          const r = byCode.get(d.properties.LEVEL3_COD) ?? 0
          return r > 0 ? color(r) : '#171C12'
        })
        .attr('stroke', '#0D110C')
        .attr('stroke-width', 0.4)
        .style('cursor', 'pointer')
        .on('mousemove', function (event, d) {
          const [x, y] = d3.pointer(event, wrap.current)
          d3.select(this).attr('stroke', '#D9B25A').attr('stroke-width', 1).raise()
          setHover({
            name: d.properties.LEVEL3_NAM, code: d.properties.LEVEL3_COD,
            richness: byCode.get(d.properties.LEVEL3_COD) ?? 0, x, y,
          })
        })
        .on('mouseleave', function () {
          d3.select(this).attr('stroke', '#0D110C').attr('stroke-width', 0.4)
          setHover(null)
        })
        .on('click', (_e, d) => setRegion({ code: d.properties.LEVEL3_COD, name: d.properties.LEVEL3_NAM }))

      // Final guard: drop any path whose RENDERED box spans nearly the whole frame —
      // antimeridian-crossing / degenerate polygons (Fiji, Aleutians, Tuamotu…) that
      // d3 smears. Deferred to after layout so getBBox returns real widths (it reads 0
      // if measured synchronously before paint).
      requestAnimationFrame(() => {
        g.selectAll<SVGPathElement, unknown>('path').each(function () {
          try { if (this.getBBox().width > W * 0.6) this.remove() } catch { /* detached */ }
        })
      })
    })
    return () => { cancelled = true }
  }, [])

  return (
    <div ref={wrap} style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height: '100%', display: 'block' }} />
      {hover && (
        <div style={{
          position: 'absolute', left: hover.x + 14, top: hover.y + 12, pointerEvents: 'none',
          background: 'var(--ground-raised)', border: '1px solid var(--hairline)',
          borderRadius: 8, padding: '8px 11px', fontSize: 12.5, maxWidth: 220, zIndex: 5,
        }}>
          <div style={{ fontWeight: 700 }}>{hover.name}</div>
          <div style={{ color: 'var(--ink-muted)', fontFamily: 'var(--font-mono)', fontSize: 11, marginTop: 3 }}>
            {hover.richness > 0
              ? `${hover.richness} native palm species`
              : 'no native palms'}
          </div>
        </div>
      )}
      <div style={{
        position: 'absolute', left: 18, bottom: 16, fontSize: 11,
        color: 'var(--ink-muted)', fontFamily: 'var(--font-mono)',
      }}>
        <div style={{ letterSpacing: '.14em', textTransform: 'uppercase', fontSize: 9, marginBottom: 5, color: 'var(--ink-faint)' }}>
          Native species per region
        </div>
        <div style={{
          width: 180, height: 9, borderRadius: 5,
          background: 'linear-gradient(90deg,#1B2415,#2E6B3E,#7FB86A,#E7C766)',
        }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', width: 180, marginTop: 3 }}>
          <span>0</span><span>{max}</span>
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

import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { api } from '../api/client'

interface Feature {
  type: string
  properties: { LEVEL3_COD: string; LEVEL3_NAM: string }
  geometry: GeoJSON.Geometry
}
type PathSel = d3.Selection<SVGPathElement, Feature, SVGGElement, unknown>

/** The map anchor. Base state = family richness; when the tree brushes a clade,
 *  `highlight` is the set of TDWG regions that clade occupies — they light up and
 *  the rest dims. */
export function LinkedMap({ highlight, onPick }: {
  highlight: Set<string> | null
  onPick?: (code: string, name: string) => void
}) {
  const wrap = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const st = useRef<{ paths: PathSel; byCode: Map<string, number>; color: (n: number) => string } | null>(null)
  const [hover, setHover] = useState<{ name: string; richness: number; x: number; y: number } | null>(null)

  // one-time setup
  useEffect(() => {
    let cancelled = false
    Promise.all([
      api.ranges(),
      fetch('/data/tdwg_level3.geojson').then((r) => r.json()),
    ]).then(([richness, geo]) => {
      if (cancelled || !wrap.current || !svgRef.current) return
      const byCode = new Map(richness.map((r) => [r.code, r.richness]))
      const maxR = d3.max(richness, (r) => r.richness) ?? 1
      const W = wrap.current.clientWidth
      const H = wrap.current.clientHeight
      const svg = d3.select(svgRef.current).attr('viewBox', `0 0 ${W} ${H}`)
      svg.selectAll('*').remove()
      const features = geo.features as Feature[]
      const projection = d3.geoNaturalEarth1().fitSize([W, H - 6], { type: 'FeatureCollection', features } as never)
      const path = d3.geoPath(projection)
      const color = d3.scaleSequentialSqrt<string>().domain([0, maxR])
        .interpolator(d3.interpolateRgbBasis(['#1B2415', '#2E6B3E', '#7FB86A', '#E7C766']))
      const g = svg.append('g')
      const paths = g.selectAll<SVGPathElement, Feature>('path').data(features).join('path')
        .attr('d', path as never).attr('stroke', '#0D110C').attr('stroke-width', 0.3)
        .style('cursor', onPick ? 'pointer' : 'default')
        .on('mouseover', function (event, d) {
          d3.select(this).attr('stroke', '#D9B25A').attr('stroke-width', 0.9).raise()
          const [x, y] = d3.pointer(event, wrap.current)
          setHover({ name: d.properties.LEVEL3_NAM, x, y, richness: byCode.get(d.properties.LEVEL3_COD) ?? 0 })
        })
        .on('mousemove', function (event, d) {
          const [x, y] = d3.pointer(event, wrap.current)
          setHover({ name: d.properties.LEVEL3_NAM, x, y, richness: byCode.get(d.properties.LEVEL3_COD) ?? 0 })
        })
        .on('mouseout', function () {
          d3.select(this).attr('stroke', '#0D110C').attr('stroke-width', 0.3)
          setHover(null)
        })
        .on('click', (_e, d) => onPick?.(d.properties.LEVEL3_COD, d.properties.LEVEL3_NAM))
      st.current = { paths, byCode, color }
      recolor()
      // drop antimeridian smears (see AtlasMap) after layout
      requestAnimationFrame(() => {
        paths.each(function () { try { if (this.getBBox().width > W * 0.6) this.remove() } catch { /* detached */ } })
      })
    })
    return () => { cancelled = true }
  }, [])

  // recolor whenever the brushed clade changes
  useEffect(recolor, [highlight])

  function recolor() {
    const s = st.current
    if (!s) return
    s.paths.attr('fill', (d) => {
      const r = s.byCode.get(d.properties.LEVEL3_COD) ?? 0
      if (!highlight) return r > 0 ? s.color(r) : '#171C12'
      if (highlight.has(d.properties.LEVEL3_COD)) return r > 0 ? s.color(r) : '#5A4A22'
      return r > 0 ? '#202a18' : '#141a11'
    })
  }

  return (
    <div ref={wrap} style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height: '100%', display: 'block' }} />
      {hover && (
        <div style={{
          position: 'absolute', left: hover.x + 14, top: hover.y + 12, pointerEvents: 'none',
          background: 'var(--ground-raised)', border: '1px solid var(--hairline)', borderRadius: 8,
          padding: '7px 11px', fontSize: 12.5, maxWidth: 220, zIndex: 6,
        }}>
          <div style={{ fontWeight: 700 }}>{hover.name}</div>
          <div style={{ color: 'var(--ink-muted)', fontFamily: 'var(--font-mono)', fontSize: 11, marginTop: 3 }}>
            {hover.richness > 0 ? `${hover.richness} native palm species` : 'no native palms'}
          </div>
        </div>
      )}
      <div style={{
        position: 'absolute', left: 16, bottom: 12, fontFamily: 'var(--font-mono)', fontSize: 10,
        color: 'var(--ink-faint)', letterSpacing: '.03em', maxWidth: 260, lineHeight: 1.4,
      }}>
        {highlight
          ? `${highlight.size} region${highlight.size === 1 ? '' : 's'} — where the selected clade lives`
          : 'Native species per region · hover the tree to light up a clade’s range'}
      </div>
    </div>
  )
}

import { useEffect, useMemo, useRef } from 'react'
import * as d3 from 'd3'
import type { TreeNode } from '../api/types'
import { SubfamilyRiskLegend } from './Legend'

const SUB_COLOR: Record<string, string> = {
  Arecoideae: '#4FB89A', Coryphoideae: '#E0A63C', Calamoideae: '#7F9CD6',
  Ceroxyloideae: '#A98BC0', Nypoideae: '#C15A4B',
}
const RISK_COLOR: Record<string, string> = {
  threatened: '#C1403C', 'not-threatened': '#6FBF73', 'not-evaluated': '#9AA0A6',
}
const subColor = (s: string | null | undefined) => (s && SUB_COLOR[s]) || '#4A5340'

type HN = d3.HierarchyPointNode<TreeNode>

/** A focused clade rendered as a legible, scrollable rectangular cladogram.
 *  Species mode: latin labels, subfamily dots, risk chips → click opens the card.
 *  Genera mode: genus labels with species counts → click opens the genus. */
export function CladeFocus({ data, kind = 'species', onSelect, onGenusClick }: {
  data: TreeNode; kind?: 'species' | 'genera'
  onSelect: (slug: string) => void; onGenusClick?: (genus: string) => void
}) {
  const wrap = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  // which subfamilies appear in this clade — so the legend shows only what's relevant
  const subs = useMemo(() => {
    const seen = new Set<string>()
    d3.hierarchy<TreeNode>(data).leaves().forEach((l) => {
      if (l.data.subfamily) seen.add(l.data.subfamily)
    })
    return [...seen].sort()
  }, [data])

  useEffect(() => {
    if (!wrap.current || !svgRef.current) return
    const root = d3.hierarchy<TreeNode>(data) as HN
    const leaves = root.leaves() as HN[]
    const row = 17
    const treeW = Math.min(260, 40 + root.height * 26)
    const labelW = 340
    const W = treeW + labelW
    const H = Math.max(leaves.length * row, 30) + 24
    d3.cluster<TreeNode>().size([H - 24, treeW])(root)

    const svg = d3.select(svgRef.current).attr('viewBox', `0 0 ${W} ${H}`)
      .attr('width', W).attr('height', H)
    svg.selectAll('*').remove()
    const g = svg.append('g').attr('transform', 'translate(8,12)')

    // right-angled elbows (matching the main tree's convention) rather than curved
    // Béziers: out from the parent's depth, down to the child's row, across to the child
    const elbow = (l: d3.HierarchyPointLink<TreeNode>) =>
      `M${l.source.y},${l.source.x}V${l.target.x}H${l.target.y}`
    g.selectAll('path').data(root.links()).join('path')
      .attr('fill', 'none').attr('stroke', '#33402A').attr('stroke-width', 1)
      .attr('d', elbow)

    const tip = g.selectAll('g.t').data(leaves).join('g').attr('class', 't')
      .attr('transform', (d) => `translate(${d.y},${d.x})`).style('cursor', 'pointer')
    const isGen = kind === 'genera'
    tip.append('circle').attr('r', 3).attr('fill', (d) => subColor(d.data.subfamily))
    tip.append('text').attr('x', 9).attr('dy', '0.32em').attr('font-size', 12.5)
      .attr('font-style', 'italic').attr('fill', '#EDF0E2').attr('class', 'lbl')
      .text((d) => (isGen ? d.data.genus : d.data.latin ?? d.data.sp) ?? '')
    if (isGen) {
      // right-aligned species count instead of a risk chip
      tip.append('text').attr('x', labelW - 14).attr('dy', '0.32em').attr('font-size', 11)
        .attr('text-anchor', 'end').attr('fill', '#8A9279')
        .text((d) => (d.data.nSpecies != null ? `${d.data.nSpecies} spp` : ''))
    } else {
      tip.append('rect').attr('x', labelW - 22).attr('y', -4).attr('width', 8).attr('height', 8).attr('rx', 2)
        .attr('fill', (d) => RISK_COLOR[d.data.risk ?? 'not-evaluated'])
    }
    tip.append('rect').attr('x', -6).attr('y', -row / 2).attr('width', labelW + treeW).attr('height', row)
      .attr('fill', 'transparent')
      .on('mouseover', function () { d3.select((this as SVGElement).parentNode as Element).select('text.lbl').attr('fill', '#E7C766') })
      .on('mouseout', function () { d3.select((this as SVGElement).parentNode as Element).select('text.lbl').attr('fill', '#EDF0E2') })
      .on('click', (_e, d) => {
        if (isGen) { if (d.data.genus) onGenusClick?.(d.data.genus) }
        else if (d.data.sp) onSelect(d.data.sp)
      })
  }, [data, kind, onSelect, onGenusClick])

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <SubfamilyRiskLegend subs={subs} showRisk={kind !== 'genera'} style={{ padding: '7px 12px 9px', borderBottom: '1px solid var(--hairline)' }} />
      <div ref={wrap} style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '4px 8px' }}>
        <svg ref={svgRef} style={{ display: 'block' }} />
      </div>
    </div>
  )
}

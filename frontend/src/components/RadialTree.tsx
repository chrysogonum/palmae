import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { api } from '../api/client'
import type { TreeNode } from '../api/types'

const SUB_COLOR: Record<string, string> = {
  Arecoideae: '#4FB89A', Coryphoideae: '#E0A63C', Calamoideae: '#7F9CD6',
  Ceroxyloideae: '#A98BC0', Nypoideae: '#C15A4B',
}
const NEUTRAL = '#4A5340'
const subColor = (s: string | null | undefined) => (s && SUB_COLOR[s]) || NEUTRAL

type HNode = d3.HierarchyPointNode<TreeNode> & { _sub?: string | null }
type LinkSel = d3.Selection<SVGPathElement, d3.HierarchyLink<TreeNode>, SVGGElement, unknown>
type TipSel = d3.Selection<SVGCircleElement, HNode, SVGGElement, unknown>

/** The phylogeny anchor: a radial cladogram.
 *  - source='species' → the Faurby 2016 all-species supertree (brush→slugs, click a
 *    branch→focus, click a tip→select, locate/highlight a species).
 *  - source='genera'  → the Yao 2023 plastid genus backbone (modern, bootstrap-
 *    supported): brush→regions, tips are genera, hover shows support. */
export function RadialTree({ source = 'species', onBrush, onBrushRegions, onSelect, onFocus, onGenusClick, locate, locateGenus, highlightSlugs }: {
  source?: 'species' | 'genera'
  onBrush: (slugs: string[] | null) => void
  onBrushRegions?: (codes: string[] | null) => void
  onSelect: (slug: string) => void
  onFocus: (clade: TreeNode, slugs: string[]) => void
  onGenusClick?: (genus: string) => void
  locate: string | null
  locateGenus?: { genus: string; n: number } | null
  highlightSlugs: Set<string> | null
}) {
  const wrap = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const store = useRef<{ root: HNode; links: LinkSel; tips: TipSel; reset: () => void } | null>(null)
  const [tip, setTip] = useState<{ label: string; x: number; y: number } | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    const isGenus = source === 'genera'
    const tipR = isGenus ? 2.4 : 1.4
    ;(isGenus ? api.treeGenera() : api.tree()).then((data) => {
      if (cancelled || !wrap.current || !svgRef.current) return
      const W = wrap.current.clientWidth
      const H = wrap.current.clientHeight
      const R = Math.min(W, H) / 2 - 16

      const root = d3.hierarchy<TreeNode>(data) as HNode
      d3.cluster<TreeNode>().size([2 * Math.PI, R])(root)
      root.each((n) => {
        const subs = new Set((n.leaves() as HNode[]).map((l) => l.data.subfamily).filter(Boolean))
        ;(n as HNode)._sub = subs.size === 1 ? ([...subs][0] as string) : null
      })

      const svg = d3.select(svgRef.current).attr('viewBox', `0 0 ${W} ${H}`)
      svg.selectAll('*').remove()
      const g = svg.append('g').attr('transform', `translate(${W / 2},${H / 2})`)
      const linkGen = d3.linkRadial<unknown, HNode>().angle((d) => d.x).radius((d) => d.y)

      const links: LinkSel = g.selectAll<SVGPathElement, d3.HierarchyLink<TreeNode>>('path.lk')
        .data(root.links()).join('path').attr('class', 'lk').attr('fill', 'none')
        .attr('stroke', (d) => subColor((d.target as HNode)._sub))
        .attr('stroke-width', 0.5).attr('stroke-opacity', 0.5).attr('d', linkGen as never)

      const hit = g.selectAll<SVGPathElement, d3.HierarchyLink<TreeNode>>('path.hit')
        .data(root.links()).join('path').attr('class', 'hit').attr('fill', 'none')
        .attr('stroke', 'transparent').attr('stroke-width', 6).style('cursor', 'pointer')
        .attr('d', linkGen as never)

      const tips: TipSel = g.selectAll<SVGCircleElement, HNode>('circle').data(root.leaves() as HNode[])
        .join('circle')
        .attr('transform', (d) => `rotate(${(d.x * 180) / Math.PI - 90}) translate(${d.y},0)`)
        .attr('r', tipR).attr('fill', (d) => subColor(d.data.subfamily)).style('cursor', 'pointer')

      const reset = () => {
        links.interrupt().attr('stroke-opacity', 0.5).attr('stroke-width', 0.5)
          .attr('stroke', (d) => subColor((d.target as HNode)._sub))
        tips.interrupt().attr('r', tipR).attr('fill', (d) => subColor(d.data.subfamily))
      }
      store.current = { root, links, tips, reset }
      setReady(true)  // signal the locate/highlight effect to (re)apply now the tree exists

      const highlightClade = (clade: HNode) => {
        const desc = new Set(clade.descendants())
        links.attr('stroke-opacity', (l) => (desc.has(l.target as HNode) ? 1 : 0.08))
          .attr('stroke-width', (l) => (desc.has(l.target as HNode) ? 1.3 : 0.5))
          .attr('stroke', (l) => (desc.has(l.target as HNode) ? '#E7C766' : subColor((l.target as HNode)._sub)))
      }

      const onBranch = (e: MouseEvent, d: d3.HierarchyLink<TreeNode>) => {
        const clade = d.target as HNode
        highlightClade(clade)
        const leaves = clade.leaves() as HNode[]
        const [x, y] = d3.pointer(e, wrap.current)
        if (isGenus) {
          // pop the clickable genus tips of this clade so it's clear where to click
          const leafSet = new Set(leaves)
          tips.attr('r', (t) => (leafSet.has(t) ? 4 : tipR))
          const codes = new Set<string>()
          leaves.forEach((l) => (l.data.regions ?? []).forEach((c) => codes.add(c)))
          onBrushRegions?.([...codes])
          const sup = clade.data.support
          const nG = leaves.length === 1 ? '1 genus' : `${leaves.length} genera`
          setTip({ label: `${nG}${clade._sub ? ' · ' + clade._sub : ''}`
            + (sup != null ? ` · ${sup}% bootstrap` : '') + ' — click a genus to open', x, y })
        } else {
          onBrush(leaves.map((l) => l.data.sp).filter(Boolean) as string[])
          setTip({ label: `${leaves.length} species${clade._sub ? ' · ' + clade._sub : ''} — click to open`, x, y })
        }
      }
      hit.on('mouseover', onBranch).on('mousemove', onBranch)
        .on('mouseout', () => { reset(); onBrush(null); onBrushRegions?.(null); setTip(null) })
        .on('click', (_e, d) => {
          if (isGenus) return
          const clade = d.target as HNode
          onFocus(clade.data, (clade.leaves() as HNode[]).map((l) => l.data.sp).filter(Boolean) as string[])
        })

      tips.on('mouseover', function (e, d) {
        d3.select(this).attr('r', isGenus ? 6 : 4).attr('fill', '#E7C766').raise()
        if (isGenus) onBrushRegions?.(d.data.regions ?? [])  // light this genus's native range
        const [x, y] = d3.pointer(e, wrap.current)
        const label = isGenus
          ? `${d.data.genus} · ${d.data.nSpecies} species — click to open`
          : (d.data.latin ?? d.data.sp ?? '')
        setTip({ label, x, y })
      }).on('mouseout', function (_e, d) {
        d3.select(this).attr('r', tipR).attr('fill', subColor(d.data.subfamily))
        if (isGenus) onBrushRegions?.(null)
        setTip(null)
      }).on('click', (_e, d) => {
        if (isGenus) { if (d.data.genus) onGenusClick?.(d.data.genus) }
        else if (d.data.sp) onSelect(d.data.sp)
      })
    })
    return () => { cancelled = true }
  }, [source, onBrush, onBrushRegions, onSelect, onFocus, onGenusClick])

  // search-to-locate (single species) and region → tree (many species): trace the
  // path(s) to the root and mark the tips. locate wins if both are set.
  useEffect(() => {
    const s = store.current
    if (!s) return
    s.reset()
    const leaves = s.root.leaves() as HNode[]

    if (locate) {
      const node = leaves.find((l) => l.data.sp === locate)
      if (!node) return
      const path = new Set(node.ancestors())
      s.links.attr('stroke-opacity', (l) => (path.has(l.target as HNode) ? 1 : 0.08))
        .attr('stroke-width', (l) => (path.has(l.target as HNode) ? 1.5 : 0.5))
        .attr('stroke', (l) => (path.has(l.target as HNode) ? '#E7C766' : subColor((l.target as HNode)._sub)))
      const pulse = () => s.tips.filter((t) => t === node).interrupt()
        .attr('r', 6).attr('fill', '#E7C766').transition().duration(900).attr('r', 3)
        .transition().duration(900).attr('r', 6).on('end', pulse)
      pulse()
      return
    }

    if (highlightSlugs && highlightSlugs.size) {
      const marked = new Set(leaves.filter((l) => l.data.sp && highlightSlugs.has(l.data.sp)))
      const onPath = new Set<HNode>()
      marked.forEach((l) => l.ancestors().forEach((a) => onPath.add(a as HNode)))
      s.links.attr('stroke-opacity', (l) => (onPath.has(l.target as HNode) ? 0.9 : 0.05))
        .attr('stroke-width', (l) => (onPath.has(l.target as HNode) ? 1 : 0.5))
        .attr('stroke', (l) => (onPath.has(l.target as HNode) ? '#E7C766' : subColor((l.target as HNode)._sub)))
      s.tips.attr('r', (t) => (marked.has(t) ? 3 : 1.4))
        .attr('fill', (t) => (marked.has(t) ? '#E7C766' : subColor(t.data.subfamily)))
    }
  }, [locate, highlightSlugs, ready, source])

  // genus tree: search-to-locate a genus — trace its path, pulse its tip, light its range
  useEffect(() => {
    const s = store.current
    if (source !== 'genera' || !s || !locateGenus) return
    s.reset()
    const node = (s.root.leaves() as HNode[]).find((l) => l.data.genus === locateGenus.genus)
    if (!node) return
    const path = new Set(node.ancestors())
    s.links.attr('stroke-opacity', (l) => (path.has(l.target as HNode) ? 1 : 0.08))
      .attr('stroke-width', (l) => (path.has(l.target as HNode) ? 1.5 : 0.5))
      .attr('stroke', (l) => (path.has(l.target as HNode) ? '#E7C766' : subColor((l.target as HNode)._sub)))
    const pulse = () => s.tips.filter((t) => t === node).interrupt()
      .attr('fill', '#E7C766').attr('r', 8).transition().duration(850).attr('r', 3.5)
      .transition().duration(850).attr('r', 8).on('end', pulse)
    pulse()
    onBrushRegions?.(node.data.regions ?? [])
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locateGenus?.n, ready, source])

  return (
    <div ref={wrap} style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height: '100%', display: 'block' }} />
      {tip && (() => {
        const cw = wrap.current?.clientWidth ?? 0
        const flipX = tip.x > cw - 230
        return (
          <div style={{
            position: 'absolute', left: tip.x + (flipX ? -14 : 14), top: tip.y + 14,
            transform: flipX ? 'translateX(-100%)' : 'none', pointerEvents: 'none',
            background: 'var(--ground-raised)', border: '1px solid var(--hairline)', borderRadius: 7,
            padding: '5px 9px', fontSize: 12, maxWidth: 260, zIndex: 5, fontFamily: 'var(--font-body)', whiteSpace: 'nowrap',
            fontStyle: /^[A-Z][a-z]+ [a-z]/.test(tip.label) ? 'italic' : 'normal',
          }}>{tip.label}</div>
        )
      })()}
    </div>
  )
}

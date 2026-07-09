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

export type BranchStyle = 'angled' | 'straight' | 'curved'

// Branch-shape carries no biological meaning (only topology + radius do), so we offer
// three renderings of the same tree. 'angled' is the systematics convention (radial
// spoke + arc at the node, as in iTOL/FigTree); 'straight' is a plain slanted spoke;
// 'curved' is the decorative Bézier. The link datum's source/target are laid-out nodes.
const P2 = Math.PI / 2
function branchPath(style: BranchStyle): (l: d3.HierarchyLink<TreeNode>) => string {
  if (style === 'curved') {
    const gen = d3.linkRadial<unknown, HNode>().angle((d) => d.x).radius((d) => d.y)
    return (l) => gen(l as never) as string
  }
  return (l) => {
    const s = l.source as HNode, t = l.target as HNode
    const a0 = s.x, r0 = s.y, a1 = t.x, r1 = t.y
    const c0 = Math.cos(a0 - P2), n0 = Math.sin(a0 - P2)
    const c1 = Math.cos(a1 - P2), n1 = Math.sin(a1 - P2)
    if (style === 'straight') return `M${r0 * c0},${r0 * n0}L${r1 * c1},${r1 * n1}`
    // angled: move to parent, arc along the parent radius to the child's angle, spoke out
    return `M${r0 * c0},${r0 * n0}`
      + (a1 === a0 ? '' : `A${r0},${r0} 0 0 ${a1 > a0 ? 1 : 0} ${r0 * c1},${r0 * n1}`)
      + `L${r1 * c1},${r1 * n1}`
  }
}

/** The phylogeny anchor: a radial cladogram.
 *  - source='species' → the Faurby 2016 all-species supertree (brush→slugs, click a
 *    branch→focus, click a tip→select, locate/highlight a species).
 *  - source='genera'  → the Yao 2023 plastid genus backbone (modern, bootstrap-
 *    supported): brush→regions, tips are genera, hover shows support. */
export function RadialTree({ source = 'species', branchStyle = 'angled', onBrush, onBrushRegions, onSelect, onFocus, onGenusClick, locate, locateGenus, highlightSlugs }: {
  source?: 'species' | 'genera'
  branchStyle?: BranchStyle
  onBrush: (slugs: string[] | null) => void
  onBrushRegions?: (codes: string[] | null) => void
  onSelect: (slug: string) => void
  onFocus: (clade: TreeNode, meta: { count: number; kind: 'species' | 'genera'; slugs?: string[]; codes?: string[] }) => void
  onGenusClick?: (genus: string) => void
  locate: string | null
  locateGenus?: { genus: string; n: number } | null
  highlightSlugs: Set<string> | null
}) {
  const wrap = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const store = useRef<{ root: HNode; links: LinkSel; hit: LinkSel; tips: TipSel; reset: () => void } | null>(null)
  const styleRef = useRef(branchStyle)
  styleRef.current = branchStyle
  const [tip, setTip] = useState<{
    x: number; y: number
    label?: string                              // simple one-liner (single tip hover)
    title?: string; titleColor?: string         // clade card: subfamily
    head?: string; genera?: string; threatened?: number; note?: string
  } | null>(null)
  const [ready, setReady] = useState(false)
  // What the tree should fall back to on mouse-out: a selected region's species
  // (highlightSlugs) or a located species path. Kept in a ref so reset() restores
  // the standing selection instead of wiping to base colours.
  const persistRef = useRef<{ hl: Set<string> | null; loc: string | null }>({ hl: highlightSlugs, loc: locate })
  persistRef.current = { hl: highlightSlugs, loc: locate }

  useEffect(() => {
    let cancelled = false
    store.current = null   // invalidate the old tree while the new one loads
    setReady(false)        // so the locate/highlight effects re-apply once it's built
    const isGenus = source === 'genera'
    const tipR = isGenus ? 2.4 : 1.4
    ;(isGenus ? api.treeGenera() : api.tree()).then((data) => {
      if (cancelled || !wrap.current || !svgRef.current) return
      const W = wrap.current.clientWidth
      const H = wrap.current.clientHeight
      // reserve headroom at the top so the crown of the tree clears the floating
      // title + All-species/Genera toggle + search that overlay the panel
      const TOP = 52
      const R = Math.min(W, H - TOP) / 2 - 16
      const CY = TOP + (H - TOP) / 2

      const root = d3.hierarchy<TreeNode>(data) as HNode
      d3.cluster<TreeNode>().size([2 * Math.PI, R])(root)
      root.each((n) => {
        const subs = new Set((n.leaves() as HNode[]).map((l) => l.data.subfamily).filter(Boolean))
        ;(n as HNode)._sub = subs.size === 1 ? ([...subs][0] as string) : null
      })

      const svg = d3.select(svgRef.current).attr('viewBox', `0 0 ${W} ${H}`)
      svg.selectAll('*').remove()
      const g = svg.append('g').attr('transform', `translate(${W / 2},${CY})`)
      const linkGen = branchPath(styleRef.current)

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

      const leaves = root.leaves() as HNode[]
      const reset = () => {
        links.interrupt().attr('stroke-opacity', 0.5).attr('stroke-width', 0.5)
          .attr('stroke', (d) => subColor((d.target as HNode)._sub))
        tips.interrupt().attr('r', tipR).attr('fill', (d) => subColor(d.data.subfamily))
        // restore the standing selection (a region's species, or a located species)
        // so hovering the tree explores on top of it rather than erasing it
        const { hl, loc } = persistRef.current
        if (hl && hl.size) {
          const marked = new Set(leaves.filter((l) => l.data.sp && hl.has(l.data.sp)))
          const onPath = new Set<HNode>()
          marked.forEach((l) => l.ancestors().forEach((a) => onPath.add(a as HNode)))
          links.attr('stroke-opacity', (l) => (onPath.has(l.target as HNode) ? 0.9 : 0.05))
            .attr('stroke-width', (l) => (onPath.has(l.target as HNode) ? 1 : 0.5))
            .attr('stroke', (l) => (onPath.has(l.target as HNode) ? '#E7C766' : subColor((l.target as HNode)._sub)))
          tips.attr('r', (t) => (marked.has(t) ? 3 : tipR))
            .attr('fill', (t) => (marked.has(t) ? '#E7C766' : subColor(t.data.subfamily)))
        } else if (loc) {
          const node = leaves.find((l) => l.data.sp === loc)
          if (node) {
            const path = new Set(node.ancestors())
            links.attr('stroke-opacity', (l) => (path.has(l.target as HNode) ? 1 : 0.08))
              .attr('stroke-width', (l) => (path.has(l.target as HNode) ? 1.5 : 0.5))
              .attr('stroke', (l) => (path.has(l.target as HNode) ? '#E7C766' : subColor((l.target as HNode)._sub)))
            tips.filter((t) => t === node).attr('r', 5).attr('fill', '#E7C766')
          }
        }
      }
      store.current = { root, links, hit, tips, reset }
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
        const top5 = (names: string[]) =>
          names.slice(0, 5).join(', ') + (names.length > 5 ? ` +${names.length - 5}` : '')
        const cladeCard = { x, y, title: clade._sub || 'mixed clade',
          titleColor: clade._sub ? subColor(clade._sub) : undefined } as const
        if (isGenus) {
          // pop the clickable genus tips of this clade so it's clear where to click
          const leafSet = new Set(leaves)
          tips.attr('r', (t) => (leafSet.has(t) ? 4 : tipR))
          const codes = new Set<string>()
          leaves.forEach((l) => (l.data.regions ?? []).forEach((c) => codes.add(c)))
          onBrushRegions?.([...codes])
          const sup = clade.data.support
          const totalSp = leaves.reduce((s, l) => s + (l.data.nSpecies ?? 0), 0)
          // genera ordered by species richness — the recognisable names first
          const genera = [...leaves].sort((a, b) => (b.data.nSpecies ?? 0) - (a.data.nSpecies ?? 0))
            .map((l) => l.data.genus).filter(Boolean) as string[]
          setTip({ ...cladeCard,
            head: `${leaves.length} genera · ${totalSp} species` + (sup != null ? ` · ${sup}% bootstrap` : ''),
            genera: top5(genera), note: 'click to zoom in' })
        } else {
          onBrush(leaves.map((l) => l.data.sp).filter(Boolean) as string[])
          const count = new Map<string, number>()
          leaves.forEach((l) => { const g = l.data.genus; if (g) count.set(g, (count.get(g) ?? 0) + 1) })
          const genera = [...count.entries()].sort((a, b) => b[1] - a[1]).map((e) => e[0])
          const threatened = leaves.filter((l) => l.data.risk === 'threatened').length
          setTip({ ...cladeCard,
            head: `${leaves.length} species · ${genera.length} ${genera.length === 1 ? 'genus' : 'genera'}`,
            genera: top5(genera), threatened, note: 'click to open' })
        }
      }
      hit.on('mouseover', onBranch).on('mousemove', onBranch)
        .on('mouseout', () => { reset(); onBrush(null); onBrushRegions?.(null); setTip(null) })
        .on('click', (_e, d) => {
          const clade = d.target as HNode
          const cladeLeaves = clade.leaves() as HNode[]
          if (isGenus) {
            const codes = new Set<string>()
            cladeLeaves.forEach((l) => (l.data.regions ?? []).forEach((c) => codes.add(c)))
            onFocus(clade.data, { count: cladeLeaves.length, kind: 'genera', codes: [...codes] })
          } else {
            onFocus(clade.data, { count: cladeLeaves.length, kind: 'species',
              slugs: cladeLeaves.map((l) => l.data.sp).filter(Boolean) as string[] })
          }
        })

      tips.on('mouseover', function (e, d) {
        d3.select(this).attr('r', isGenus ? 6 : 4).attr('fill', '#E7C766').raise()
        if (isGenus) onBrushRegions?.(d.data.regions ?? [])  // light this genus's native range
        const [x, y] = d3.pointer(e, wrap.current)
        const label = isGenus
          ? `${d.data.genus} · ${d.data.nSpecies} species — click to open`
          : (d.data.latin ?? d.data.sp ?? '')
        setTip({ label, x, y })
      }).on('mouseout', () => {
        reset()  // restores base + any standing region/located selection
        if (isGenus) onBrushRegions?.(null)
        setTip(null)
      }).on('click', (_e, d) => {
        if (isGenus) { if (d.data.genus) onGenusClick?.(d.data.genus) }
        else if (d.data.sp) onSelect(d.data.sp)
      })
    })
    return () => { cancelled = true }
  }, [source, onBrush, onBrushRegions, onSelect, onFocus, onGenusClick])

  // restyle branches in place (no rebuild) when the shape toggle changes
  useEffect(() => {
    const s = store.current
    if (!s) return
    const gen = branchPath(branchStyle)
    s.links.attr('d', gen as never)
    s.hit.attr('d', gen as never)
  }, [branchStyle, ready])

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
        const flipX = tip.x > cw - 260
        const box: React.CSSProperties = {
          position: 'absolute', left: tip.x + (flipX ? -14 : 14), top: tip.y + 14,
          transform: flipX ? 'translateX(-100%)' : 'none', pointerEvents: 'none',
          background: 'var(--ground-raised)', border: '1px solid var(--hairline)', borderRadius: 8,
          padding: '7px 11px', zIndex: 5, fontFamily: 'var(--font-body)', maxWidth: 268,
        }
        if (tip.title) return (
          <div style={box}>
            <div style={{ fontSize: 13, fontWeight: 700, color: tip.titleColor ?? 'var(--ink)' }}>{tip.title}</div>
            {tip.head && <div style={{ fontSize: 11.5, color: 'var(--ink-muted)', marginTop: 1 }}>{tip.head}</div>}
            {tip.genera && <div style={{ fontSize: 11.5, fontStyle: 'italic', color: 'var(--ink)', marginTop: 4, lineHeight: 1.35 }}>{tip.genera}</div>}
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 5 }}>
              {tip.threatened != null && tip.threatened > 0 && (
                <span style={{ fontSize: 11, color: '#D46B63', fontWeight: 600 }}>{tip.threatened} threatened</span>
              )}
              {tip.note && <span style={{ fontSize: 10, letterSpacing: '.04em', color: 'var(--ink-faint)', fontFamily: 'var(--font-mono)' }}>{tip.note}</span>}
            </div>
          </div>
        )
        return (
          <div style={{ ...box, fontSize: 12, whiteSpace: 'nowrap',
            fontStyle: /^[A-Z][a-z]+ [a-z]/.test(tip.label ?? '') ? 'italic' : 'normal',
          }}>{tip.label}</div>
        )
      })()}
    </div>
  )
}

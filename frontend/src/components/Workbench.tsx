import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { RadialTree } from './RadialTree'
import { CladeFocus } from './CladeFocus'
import { LinkedMap } from './LinkedMap'
import { RegionPanel } from './RegionPanel'
import { Detail } from './Catalogue'
import { SubfamilyRiskLegend, SUBFAMILIES_ALL } from './Legend'
import { api } from '../api/client'
import type { SearchResult, TreeNode } from '../api/types'

function Head({ title, meta, children }: { title: string; meta?: string; children?: React.ReactNode }) {
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, zIndex: 4, padding: '10px 14px',
      display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10,
      background: 'linear-gradient(180deg, var(--ground) 55%, transparent)',
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
        <h2 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: 17, fontWeight: 600 }}>{title}</h2>
        {meta && <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-faint)', letterSpacing: '.06em' }}>{meta}</span>}
      </div>
      {children}
    </div>
  )
}

/** The workbench: the palm tree of life and the world map, brushed against each
 *  other. Hover a clade → its range lights up. Click a clade → drill into a labeled
 *  subtree. Search → locate a species on the tree. Click a tip → its card. */
export function Workbench({ locateReq, onSeeOnTree, onGenusClick }: {
  locateReq?: { slug: string; n: number } | null
  onSeeOnTree?: (slug: string) => void
  onGenusClick?: (genus: string) => void
} = {}) {
  const regions = useRef<Record<string, string[]>>({})
  const [highlight, setHighlight] = useState<Set<string> | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [focus, setFocus] = useState<{ data: TreeNode; label: string; kind: 'species' | 'genera' } | null>(null)
  const [locate, setLocate] = useState<string | null>(null)
  const [region, setRegion] = useState<{ code: string; name: string } | null>(null)
  // mirror of `region` in a ref so the stable brush callbacks can restore the
  // region's map highlight on tree mouse-out without rebuilding the tree
  const regionRef = useRef(region)
  regionRef.current = region
  const [treeHighlight, setTreeHighlight] = useState<Set<string> | null>(null)
  const [treeSource, setTreeSource] = useState<'species' | 'genera'>('species')
  const [genera, setGenera] = useState<{ genus: string; nSpecies: number }[]>([])
  const [locateGenus, setLocateGenus] = useState<{ genus: string; n: number } | null>(null)

  // load the genus list (for the genus-tree search) the first time genus mode opens
  useEffect(() => {
    if (treeSource !== 'genera' || genera.length) return
    api.treeGenera().then((tree) => {
      const out: { genus: string; nSpecies: number }[] = []
      const walk = (n: TreeNode) => {
        if (n.genus) out.push({ genus: n.genus, nSpecies: n.nSpecies ?? 0 })
        n.children?.forEach(walk)
      }
      walk(tree)
      setGenera(out.sort((a, b) => a.genus.localeCompare(b.genus)))
    }).catch(() => {})
  }, [treeSource, genera.length])

  useEffect(() => { api.speciesRegions().then((m) => { regions.current = m }).catch(() => {}) }, [])

  const regionsFor = useCallback((slugs: string[]) => {
    const codes = new Set<string>()
    for (const s of slugs) for (const c of regions.current[s] ?? []) codes.add(c)
    return codes
  }, [])

  // on mouse-out (null) fall back to the standing region highlight, not blank,
  // so exploring the tree doesn't erase a selected region on the map
  const restoreRegion = () => (regionRef.current ? new Set([regionRef.current.code]) : null)
  const onBrush = useCallback((slugs: string[] | null) => {
    setHighlight(slugs ? regionsFor(slugs) : restoreRegion())
  }, [regionsFor])
  // genus tree brushes the map by region codes directly (no per-species slugs)
  const onBrushRegions = useCallback((codes: string[] | null) => {
    setHighlight(codes ? new Set(codes) : restoreRegion())
  }, [])
  // Toggle trees while KEEPING the selected species: re-trace it on the species tree,
  // or highlight its genus on the genus tree. The selection (card) persists across
  // toggles; clearSelection is the explicit way out.
  const switchTree = useCallback((src: 'species' | 'genera') => {
    setTreeSource(src)
    setFocus(null); setRegion(null); setTreeHighlight(null)
    if (selected && src === 'genera') {
      const g = selected.split('-')[0]              // slug = "genus-epithet"
      const genus = g.charAt(0).toUpperCase() + g.slice(1)
      setLocate(null)
      setLocateGenus((prev) => ({ genus, n: (prev?.n ?? 0) + 1 }))
    } else if (selected) {
      setLocateGenus(null); setLocate(selected); setHighlight(regionsFor([selected]))
    } else {
      setLocate(null); setLocateGenus(null); setHighlight(null)
    }
  }, [selected, regionsFor])
  const clearSelection = useCallback(() => {
    setSelected(null); setLocate(null); setLocateGenus(null)
    setHighlight(null); setTreeHighlight(null); setRegion(null); setFocus(null)
  }, [])
  const locateGenusByName = useCallback((genus: string) => {
    setLocateGenus((g) => ({ genus, n: (g?.n ?? 0) + 1 }))
  }, [])
  const onSelect = useCallback((slug: string) => setSelected(slug), [])
  // Focus a clade into a legible sub-tree with the map showing its combined range.
  // Species clades resolve regions per-species; genus clades carry region codes directly.
  const onFocus = useCallback((data: TreeNode, meta:
    { count: number; kind: 'species' | 'genera'; slugs?: string[]; codes?: string[] }) => {
    const codes = meta.codes ? new Set(meta.codes) : regionsFor(meta.slugs ?? [])
    const noun = meta.kind === 'genera' ? (meta.count === 1 ? 'genus' : 'genera') : 'species'
    setFocus({ data, kind: meta.kind, label: `${meta.count} ${noun}${data.subfamily ? ' · ' + data.subfamily : ''}` })
    setHighlight(codes); setLocate(null); setSelected(null); setRegion(null)
  }, [regionsFor])

  const locateBySlug = useCallback((slug: string) => {
    setFocus(null); setRegion(null); setTreeHighlight(null); setLocateGenus(null)
    setLocate(slug); setSelected(slug); setHighlight(regionsFor([slug]))
  }, [regionsFor])
  const locateSpecies = useCallback((r: SearchResult) => locateBySlug(r.slug), [locateBySlug])

  // an external "see on the tree" request (from a species card on another surface)
  useEffect(() => {
    if (locateReq) locateBySlug(locateReq.slug)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locateReq?.n])

  // click a map region → light up the tree tips that live there + list its species
  const onPickRegion = useCallback((code: string, name: string) => {
    const slugs: string[] = []
    for (const [slug, codes] of Object.entries(regions.current)) if (codes.includes(code)) slugs.push(slug)
    setFocus(null); setLocate(null)
    setRegion({ code, name }); setTreeHighlight(new Set(slugs)); setHighlight(new Set([code]))
  }, [])
  const clearRegion = useCallback(() => {
    setRegion(null); setTreeHighlight(null); setHighlight(null)
  }, [])

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', width: '100%', minHeight: 0, position: 'relative' }}>
      <section style={{ position: 'relative', borderRight: '1px solid var(--hairline)', minHeight: 0 }}>
        {focus ? (
          <>
            <Head title="Clade" meta={focus.label}>
              <button onClick={() => { setFocus(null); setHighlight(null) }} style={btn}>← full tree</button>
            </Head>
            <div style={{ position: 'absolute', inset: 0, paddingTop: 42 }}>
              <CladeFocus data={focus.data} kind={focus.kind} onSelect={onSelect} onGenusClick={onGenusClick} />
            </div>
          </>
        ) : (
          <>
            <Head
              title={treeSource === 'genera' ? 'Palm genera' : 'Palm tree of life'}
              meta={treeSource === 'genera' ? 'Yao 2023 · 177 genera · bootstrap support' : 'Faurby 2016 · 2,539 tips'}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, pointerEvents: 'auto' }}>
                <div className="seg" style={{ fontSize: 11 }}>
                  <button className={treeSource === 'species' ? 'active' : ''} onClick={() => switchTree('species')}>All species</button>
                  <button className={treeSource === 'genera' ? 'active' : ''} onClick={() => switchTree('genera')}>Genera</button>
                </div>
                {treeSource === 'species'
                  ? <SearchBox onPick={locateSpecies} />
                  : <GenusSearchBox genera={genera} onPick={locateGenusByName} />}
              </div>
            </Head>
            <RadialTree source={treeSource} onBrush={onBrush} onBrushRegions={onBrushRegions}
              onSelect={onSelect} onFocus={onFocus} onGenusClick={onGenusClick}
              locate={locate} locateGenus={locateGenus} highlightSlugs={treeHighlight} />
            <div style={{
              position: 'absolute', left: 14, bottom: 12, zIndex: 3, maxWidth: 300,
              background: 'rgba(13,17,12,.6)', borderRadius: 8, padding: '6px 10px', backdropFilter: 'blur(2px)',
            }}>
              <SubfamilyRiskLegend subs={SUBFAMILIES_ALL} showRisk={false} />
            </div>
          </>
        )}
      </section>

      <section style={{ position: 'relative', minHeight: 0 }}>
        <Head title="World map" meta={region ? 'click a region · showing ' + region.name : 'native range · click a region'} />
        <LinkedMap highlight={highlight} onPick={onPickRegion} />
        {region && (
          <RegionPanel code={region.code} name={region.name} onSelect={onSelect} onClose={clearRegion} />
        )}
      </section>

      {selected && (
        <aside style={{
          position: 'absolute', top: 0, right: 0, bottom: 0, width: 460, zIndex: 20,
          background: 'var(--ground)', borderLeft: '1px solid var(--hairline)',
          boxShadow: '-18px 0 40px rgba(0,0,0,.5)', display: 'flex', flexDirection: 'column',
        }}>
          <button onClick={clearSelection} title="Clear selection" style={{ ...btn, alignSelf: 'flex-end', margin: 10 }}>Clear selection ✕</button>
          <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}><Detail slug={selected} onSeeOnTree={onSeeOnTree} /></div>
        </aside>
      )}
    </div>
  )
}

const btn: React.CSSProperties = {
  background: 'var(--panel)', color: 'var(--ink-muted)', border: '1px solid var(--hairline)',
  borderRadius: 7, padding: '5px 11px', cursor: 'pointer', fontSize: 12.5, pointerEvents: 'auto',
}

function SearchBox({ onPick }: { onPick: (r: SearchResult) => void }) {
  const [q, setQ] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  useEffect(() => {
    if (q.trim().length < 2) { setResults([]); return }
    let live = true
    const id = setTimeout(() => { api.search(q).then((r) => { if (live) setResults(r) }).catch(() => {}) }, 160)
    return () => { live = false; clearTimeout(id) }
  }, [q])
  return (
    <div style={{ position: 'relative', pointerEvents: 'auto' }}>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Find a species…"
        style={{
          width: 210, background: 'var(--panel)', border: '1px solid var(--hairline)', borderRadius: 8,
          color: 'var(--ink)', padding: '7px 11px', fontSize: 13, fontFamily: 'var(--font-body)',
        }} />
      {results.length > 0 && (
        <div style={{
          position: 'absolute', top: 38, right: 0, width: 300, maxHeight: 320, overflowY: 'auto',
          background: 'var(--ground-raised)', border: '1px solid var(--hairline)', borderRadius: 8, zIndex: 10,
          boxShadow: '0 12px 30px rgba(0,0,0,.5)',
        }}>
          {results.map((r) => (
            <button key={r.slug} onClick={() => { onPick(r); setQ(''); setResults([]) }}
              style={{
                display: 'flex', alignItems: 'center', gap: 9, width: '100%', textAlign: 'left',
                background: 'transparent', border: 0, borderBottom: '1px solid var(--hairline)',
                padding: '8px 11px', cursor: 'pointer', color: 'var(--ink)',
              }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: r.color, flex: '0 0 auto' }} />
              <span style={{ minWidth: 0 }}>
                <span style={{ fontStyle: 'italic', fontSize: 13.5 }}>{r.latin}</span>
                {r.sub && <span style={{ display: 'block', fontSize: 10.5, color: 'var(--ink-faint)', fontFamily: 'var(--font-mono)' }}>{r.sub}</span>}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// Genus-tree search: filters the ~177 genera client-side; picking one locates it on
// the genus tree (traces its path, pulses the tip, lights its range).
function GenusSearchBox({ genera, onPick }: {
  genera: { genus: string; nSpecies: number }[]
  onPick: (genus: string) => void
}) {
  const [q, setQ] = useState('')
  const results = useMemo(() => {
    const like = q.trim().toLowerCase()
    if (!like) return []
    return genera.filter((g) => g.genus.toLowerCase().includes(like)).slice(0, 14)
  }, [q, genera])
  return (
    <div style={{ position: 'relative', pointerEvents: 'auto' }}>
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Find a genus…"
        style={{
          width: 210, background: 'var(--panel)', border: '1px solid var(--hairline)', borderRadius: 8,
          color: 'var(--ink)', padding: '7px 11px', fontSize: 13, fontFamily: 'var(--font-body)',
        }} />
      {results.length > 0 && (
        <div style={{
          position: 'absolute', top: 38, right: 0, width: 260, maxHeight: 320, overflowY: 'auto',
          background: 'var(--ground-raised)', border: '1px solid var(--hairline)', borderRadius: 8, zIndex: 10,
          boxShadow: '0 12px 30px rgba(0,0,0,.5)',
        }}>
          {results.map((g) => (
            <button key={g.genus} onClick={() => { onPick(g.genus); setQ('') }}
              style={{
                display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 9, width: '100%',
                textAlign: 'left', background: 'transparent', border: 0, borderBottom: '1px solid var(--hairline)',
                padding: '8px 11px', cursor: 'pointer', color: 'var(--ink)',
              }}>
              <span style={{ fontStyle: 'italic', fontSize: 13.5 }}>{g.genus}</span>
              <span style={{ fontSize: 10.5, color: 'var(--ink-faint)', fontFamily: 'var(--font-mono)' }}>{g.nSpecies} spp</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

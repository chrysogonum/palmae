import { useCallback, useEffect, useState } from 'react'
import { Workbench } from './components/Workbench'
import { AtlasMap } from './components/AtlasMap'
import { Catalogue } from './components/Catalogue'
import { PalmLine } from './components/PalmLine'
import { About, Sources } from './components/Pages'
import { api } from './api/client'
import type { Coverage } from './api/types'

type Surface = 'palmline' | 'workbench' | 'atlas' | 'guide' | 'about' | 'sources'

export default function App() {
  const [surface, setSurface] = useState<Surface>('workbench')
  const [cov, setCov] = useState<Coverage | null>(null)
  const [treeLocate, setTreeLocate] = useState<{ slug: string; n: number } | null>(null)
  const [guideFilter, setGuideFilter] = useState<{ q: string; n: number } | null>(null)
  useEffect(() => { api.coverage().then(setCov).catch(() => {}) }, [])

  // cross-link: "see on the tree" from any species card → Workbench, traced on the tree
  const seeOnTree = useCallback((slug: string) => {
    setTreeLocate((t) => ({ slug, n: (t?.n ?? 0) + 1 }))
    setSurface('workbench')
  }, [])
  // cross-link: click a genus on the genus tree → Field Guide filtered to that genus
  const seeGenus = useCallback((genus: string) => {
    setGuideFilter((g) => ({ q: genus, n: (g?.n ?? 0) + 1 }))
    setSurface('guide')
  }, [])

  return (
    <div className="app">
      <header className="topbar">
        <button className="brand" onClick={() => setSurface('workbench')}>
          <span className="mark">Palmae</span>
          <span className="sub">a living atlas of the palms</span>
        </button>
        <div className="spacer" />
        {cov && (
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-faint)',
            letterSpacing: '.04em', marginRight: 4,
          }}>
            {cov.total_species.toLocaleString()} species · {cov.tree_pct}% on the tree ·{' '}
            {cov.threatened_of_assessed.toLocaleString()} threatened
          </span>
        )}
        <nav className="seg" style={{ marginLeft: 14 }}>
          <button className={surface === 'workbench' ? 'active' : ''} onClick={() => setSurface('workbench')}>
            Workbench
          </button>
          <button className={surface === 'atlas' ? 'active' : ''} onClick={() => setSurface('atlas')}>
            World Atlas
          </button>
          <button className={surface === 'palmline' ? 'active' : ''} onClick={() => setSurface('palmline')}>
            Palm Line
          </button>
          <button className={surface === 'guide' ? 'active' : ''} onClick={() => setSurface('guide')}>
            Field Guide
          </button>
        </nav>
        <div className="meta-nav">
          <button className={surface === 'about' ? 'active' : ''} onClick={() => setSurface('about')}>About</button>
          <span className="meta-dot">·</span>
          <button className={surface === 'sources' ? 'active' : ''} onClick={() => setSurface('sources')}>Sources</button>
        </div>
      </header>
      <main style={{ flex: '1 1 auto', minHeight: 0, position: 'relative', display: 'flex' }}>
        {surface === 'palmline' ? <PalmLine onSeeOnTree={seeOnTree} />
          : surface === 'workbench' ? <Workbench locateReq={treeLocate} onSeeOnTree={seeOnTree} onGenusClick={seeGenus} />
          : surface === 'atlas' ? <AtlasMap onSeeOnTree={seeOnTree} />
          : surface === 'guide' ? <Catalogue onSeeOnTree={seeOnTree} filter={guideFilter} />
          : surface === 'about' ? <About go={setSurface} />
          : <Sources go={setSurface} />}
      </main>
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { RegionSpecies } from '../api/types'
import { SubfamilyRiskLegend } from './Legend'

/** Slide-over listing every palm native to a clicked TDWG region, coloured by
 *  subfamily with risk chips; click one → its species card. */
export function RegionPanel({ code, name, onSelect, onClose }: {
  code: string; name: string; onSelect: (slug: string) => void; onClose: () => void
}) {
  const [species, setSpecies] = useState<RegionSpecies[] | null>(null)
  useEffect(() => {
    setSpecies(null)
    api.regionSpecies(code).then(setSpecies).catch(() => setSpecies([]))
  }, [code])
  const subs = useMemo(
    () => [...new Set((species ?? []).map((s) => s.subfamily).filter(Boolean) as string[])].sort(),
    [species])

  return (
    <aside style={{
      position: 'absolute', top: 0, right: 0, bottom: 0, width: 380, zIndex: 15,
      background: 'var(--ground)', borderLeft: '1px solid var(--hairline)',
      boxShadow: '-18px 0 40px rgba(0,0,0,.5)', display: 'flex', flexDirection: 'column', minHeight: 0,
    }}>
      <header style={{ padding: '16px 18px 12px', borderBottom: '1px solid var(--hairline)', flex: '0 0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <h2 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 600 }}>{name}</h2>
          <button onClick={onClose} style={{
            background: 'var(--panel)', color: 'var(--ink-muted)', border: '1px solid var(--hairline)',
            borderRadius: 7, padding: '4px 9px', cursor: 'pointer', fontSize: 12,
          }}>✕</button>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-faint)', marginTop: 4 }}>
          {species == null ? 'loading…' : `${species.length} native palm species`}
        </div>
        {species && species.length > 0 && <SubfamilyRiskLegend subs={subs} style={{ marginTop: 10 }} />}
      </header>
      <div style={{ overflowY: 'auto', minHeight: 0 }}>
        {(species ?? []).map((s) => (
          <button key={s.slug} onClick={() => onSelect(s.slug)} style={{
            display: 'flex', alignItems: 'center', gap: 10, width: '100%', textAlign: 'left',
            background: 'transparent', border: 0, borderBottom: '1px solid var(--hairline)',
            padding: '9px 18px', cursor: 'pointer', color: 'var(--ink)',
          }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: s.color, flex: '0 0 auto' }} />
            <span style={{ flex: 1, minWidth: 0, fontStyle: 'italic', fontSize: 13.5 }}>{s.latin}</span>
            <span title={s.risk} style={{ width: 8, height: 8, borderRadius: 2, background: s.riskColor, flex: '0 0 auto' }} />
          </button>
        ))}
      </div>
    </aside>
  )
}

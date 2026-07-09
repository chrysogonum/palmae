import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import type { TaxonListItem, TaxonDetail } from '../api/types'
import { SubfamilyRiskLegend } from './Legend'
import { RangeMap } from './RangeMap'

const SUBFAMILIES = ['Arecoideae', 'Coryphoideae', 'Calamoideae', 'Ceroxyloideae', 'Nypoideae']

export function Catalogue({ onSeeOnTree, filter }: {
  onSeeOnTree?: (slug: string) => void
  filter?: { q: string; n: number } | null
}) {
  const [taxa, setTaxa] = useState<TaxonListItem[]>([])
  const [q, setQ] = useState('')
  const [sub, setSub] = useState<string | null>(null)
  const [genus, setGenus] = useState<string | null>(null)  // exact-genus filter (from a genus-tree click)
  const [slug, setSlug] = useState<string | null>(null)
  const [brokenThumbs, setBrokenThumbs] = useState<Set<string>>(new Set())

  useEffect(() => { api.taxa().then(setTaxa).catch(() => {}) }, [])
  // an external filter request (clicking a genus on the tree) → filter to exactly that genus
  useEffect(() => {
    if (filter) { setGenus(filter.q); setQ(''); setSub(null); setSlug(null) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter?.n])

  const filtered = useMemo(() => {
    const like = q.toLowerCase()
    return taxa.filter((t) =>
      (!genus || t.genus === genus) &&
      (!sub || t.subfamily === sub) &&
      (!like || t.latin.toLowerCase().includes(like) || (t.genus ?? '').toLowerCase().includes(like)),
    )
  }, [taxa, q, sub, genus])
  const legendSubs = useMemo(
    () => [...new Set(filtered.map((t) => t.subfamily).filter(Boolean) as string[])].sort(),
    [filtered])

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', width: '100%', minHeight: 0 }}>
      <aside style={{ borderRight: '1px solid var(--hairline)', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--hairline)' }}>
          <input
            value={q} onChange={(e) => { setQ(e.target.value); setGenus(null) }} placeholder="Search 2,591 palm species…"
            style={{
              width: '100%', background: 'var(--panel)', border: '1px solid var(--hairline)',
              borderRadius: 8, color: 'var(--ink)', padding: '9px 12px', fontSize: 14, fontFamily: 'var(--font-body)',
            }}
          />
          {genus && (
            <button onClick={() => setGenus(null)} title="Clear genus filter" style={{
              display: 'inline-flex', alignItems: 'center', gap: 7, marginTop: 9, cursor: 'pointer',
              background: 'var(--panel)', border: '1px solid var(--gold)', borderRadius: 999,
              padding: '4px 10px', fontSize: 12.5, color: 'var(--ink)',
            }}>
              <span style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '.06em', textTransform: 'uppercase' }}>genus</span>
              <em style={{ fontStyle: 'italic' }}>{genus}</em>
              <span style={{ color: 'var(--gold)' }}>✕</span>
            </button>
          )}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 9 }}>
            <Chip on={!sub} onClick={() => { setSub(null); setGenus(null) }}>All</Chip>
            {SUBFAMILIES.map((s) => <Chip key={s} on={sub === s} onClick={() => { setSub(sub === s ? null : s); setGenus(null) }}>{s}</Chip>)}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--ink-faint)', marginTop: 9 }}>
            {filtered.length.toLocaleString()} species
          </div>
          <SubfamilyRiskLegend subs={legendSubs} style={{ marginTop: 10 }} />
        </div>
        <div style={{ overflowY: 'auto', minHeight: 0 }}>
          {filtered.slice(0, 600).map((t) => (
            <button key={t.slug} onClick={() => setSlug(t.slug)}
              style={{
                display: 'flex', alignItems: 'center', gap: 11, width: '100%', textAlign: 'left',
                background: slug === t.slug ? 'var(--ground-raised)' : 'transparent', border: 0,
                borderBottom: '1px solid var(--hairline)', padding: '8px 14px', cursor: 'pointer', color: 'var(--ink)',
              }}>
              <span style={{
                width: 30, height: 30, flex: '0 0 auto', borderRadius: 6, overflow: 'hidden',
                display: 'grid', placeItems: 'center',
                boxShadow: t.thumb && !brokenThumbs.has(t.slug) ? `0 0 0 1.5px ${t.color}` : 'none',
              }}>
                {t.thumb && !brokenThumbs.has(t.slug)
                  ? <img src={t.thumb} alt="" loading="lazy"
                      onError={() => setBrokenThumbs((b) => new Set(b).add(t.slug))}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : <span style={{ width: 9, height: 9, borderRadius: '50%', background: t.color }} />}
              </span>
              <span style={{ flex: 1, minWidth: 0 }}>
                <span style={{ fontStyle: 'italic', fontSize: 14 }}>{t.latin}</span>
                <span style={{ display: 'block', fontSize: 11, color: 'var(--ink-faint)', fontFamily: 'var(--font-mono)' }}>
                  {t.subfamily ?? '—'}{t.endemic ? ' · endemic' : ''}
                </span>
              </span>
              <span title={t.risk} style={{ width: 8, height: 8, borderRadius: 2, background: t.riskColor, flex: '0 0 auto' }} />
            </button>
          ))}
          {filtered.length > 600 && (
            <div style={{ padding: 14, fontSize: 12, color: 'var(--ink-faint)' }}>
              …refine your search to see the remaining {(filtered.length - 600).toLocaleString()}.
            </div>
          )}
        </div>
      </aside>
      <Detail slug={slug} onSeeOnTree={onSeeOnTree} />
    </div>
  )
}

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick} className={on ? 'lens-tab active' : 'lens-tab'} style={{ fontSize: 11, padding: '4px 10px' }}>
      {children}
    </button>
  )
}

export function Detail({ slug, onSeeOnTree }: {
  slug: string | null
  onSeeOnTree?: (slug: string) => void
}) {
  const [d, setD] = useState<TaxonDetail | null>(null)
  const [photoOk, setPhotoOk] = useState(true)
  useEffect(() => {
    setPhotoOk(true)
    if (!slug) { setD(null); return }
    api.taxon(slug).then(setD).catch(() => setD(null))
  }, [slug])

  if (!slug) return (
    <div style={{ display: 'grid', placeItems: 'center', color: 'var(--ink-faint)', fontSize: 14 }}>
      Select a species to see its card.
    </div>
  )
  if (!d) return <div style={{ padding: 30, color: 'var(--ink-faint)' }}>Loading…</div>

  const c = d.conservation
  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '26px 32px', maxWidth: 720 }}>
      {d.photo && photoOk && (() => {
        const img = (
          <img src={d.photo.url} alt={d.latin} loading="lazy" onError={() => setPhotoOk(false)} style={{
            width: '100%', maxHeight: 300, objectFit: 'cover', borderRadius: 10, display: 'block',
            border: '1px solid var(--hairline)', cursor: d.photo.sourceUrl ? 'pointer' : 'default',
          }} />
        )
        const onObs = (d.photo.sourceUrl ?? '').includes('/observations/')
        return (
          <figure style={{ margin: '0 0 20px' }}>
            {d.photo.sourceUrl
              ? <a href={d.photo.sourceUrl} target="_blank" rel="noreferrer"
                  title={onObs ? 'See this observation on iNaturalist' : 'See this species on iNaturalist'}
                  style={{ display: 'block' }}>{img}</a>
              : img}
            <figcaption style={{ fontSize: 10.5, color: 'var(--ink-faint)', fontFamily: 'var(--font-mono)', marginTop: 6, lineHeight: 1.4 }}>
              {d.photo.attribution || `${d.photo.license ?? 'CC'} licensed`}
              {' · '}
              {d.photo.sourceUrl
                ? <a href={d.photo.sourceUrl} target="_blank" rel="noreferrer"
                    style={{ color: 'var(--gold)', textDecoration: 'none', borderBottom: '1px solid rgba(217,178,90,.4)' }}>
                    {onObs ? 'observation on iNaturalist ↗' : 'iNaturalist ↗'}
                  </a>
                : 'iNaturalist'}
            </figcaption>
          </figure>
        )
      })()}
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '.18em', textTransform: 'uppercase', color: 'var(--ink-faint)' }}>
        {d.subfamily} · {d.tribe ?? '—'}
      </div>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 34, margin: '4px 0 2px', fontStyle: 'italic' }}>{d.latin}</h1>
      <div style={{ color: 'var(--ink-muted)', fontSize: 13 }}>
        {d.authority}{d.common ? ` · ${d.common}` : ''}
      </div>

      <div style={{ display: 'flex', gap: 10, margin: '18px 0', flexWrap: 'wrap' }}>
        {c.basis === 'assessed' ? (
          <>
            <Badge color={c.iucnColor ?? c.riskColor}>{c.iucnLabel ?? c.riskLabel}</Badge>
            <Badge muted>IUCN{c.assessmentYear ? ` · ${c.assessmentYear}` : ''}</Badge>
          </>
        ) : (
          <>
            <Badge color={c.riskColor}>{c.riskLabel}{c.basis === 'predicted' ? ' (predicted)' : ''}</Badge>
            {c.probability != null && <Badge muted>p = {c.probability}</Badge>}
          </>
        )}
        {d.onTree && (onSeeOnTree
          ? (
            <button onClick={() => onSeeOnTree(d.slug)} title="Trace this species on the phylogeny"
              style={{
                fontSize: 12, fontWeight: 600, padding: '4px 11px', borderRadius: 999, cursor: 'pointer',
                background: 'transparent', color: 'var(--gold)', border: '1px solid var(--gold)',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--gold)'; e.currentTarget.style.color = 'var(--ground)' }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--gold)' }}
            >on the phylogeny →</button>
          )
          : <Badge muted>on the phylogeny</Badge>)}
        {d.nativeRegions.length === 1 && <Badge muted>single-region endemic</Badge>}
      </div>

      <dl style={{ display: 'grid', gridTemplateColumns: '150px 1fr', rowGap: 9, columnGap: 16, margin: '20px 0' }}>
        {d.glance.filter((g) => g.v).map((g) => (
          <div key={g.k} style={{ display: 'contents' }}>
            <dt style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-mono)', fontSize: 11.5, letterSpacing: '.03em' }}>{g.k}</dt>
            <dd style={{ margin: 0, fontSize: 14 }}>{g.v}</dd>
          </div>
        ))}
      </dl>

      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '.16em', textTransform: 'uppercase', color: 'var(--ink-faint)', marginBottom: 7 }}>
        Native range · {d.nativeRegions.length} region{d.nativeRegions.length === 1 ? '' : 's'}
        {d.introducedRegions.length > 0 && ` · ${d.introducedRegions.length} introduced`}
      </div>
      {(d.nativeRegions.length > 0 || d.introducedRegions.length > 0) && (
        <div style={{ marginBottom: 9 }}>
          <RangeMap
            native={d.nativeRegions.map((r) => r.code)}
            introduced={d.introducedRegions.map((r) => r.code)}
            color={d.color}
          />
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9.5, color: 'var(--ink-faint)', marginTop: 4 }}>
            filled = native{d.introducedRegions.length > 0 ? ' · dashed = introduced' : ''} · WGSRPD level-3 · hover for names
          </div>
        </div>
      )}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
        {d.nativeRegions.map((r) => (
          <span key={r.code} title={`${r.code} · native`} style={{ fontSize: 11.5, padding: '3px 8px', border: '1px solid var(--hairline)', borderRadius: 5, color: 'var(--ink-muted)' }}>{r.name}</span>
        ))}
        {d.introducedRegions.map((r) => (
          <span key={r.code} title={`${r.code} · introduced`} style={{ fontSize: 11.5, padding: '3px 8px', border: '1px dashed var(--hairline)', borderRadius: 5, color: 'var(--ink-faint)' }}>{r.name}</span>
        ))}
      </div>

      {d.climate && (
        <div style={{ marginTop: 22, padding: '13px 15px', border: '1px solid var(--hairline)', borderRadius: 9, background: 'var(--panel)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '.16em', textTransform: 'uppercase', color: 'var(--ink-faint)', marginBottom: 8 }}>
            Coldest-month climate · <span style={{ color: '#8AA9CE' }}>derived</span>
          </div>
          <div style={{ display: 'flex', gap: 22, alignItems: 'baseline' }}>
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 30, lineHeight: 1, color: d.climate.belowFrostLine ? '#7FB0DD' : '#E0A63C' }}>
                {d.climate.cmmtMin > 0 ? '+' : ''}{d.climate.cmmtMin.toFixed(1)}°C
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--ink-faint)', marginTop: 3 }}>cold edge (coldest month, min)</div>
            </div>
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 30, lineHeight: 1, color: 'var(--ink-muted)' }}>
                {d.climate.cmmtMean > 0 ? '+' : ''}{d.climate.cmmtMean.toFixed(1)}°C
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--ink-faint)', marginTop: 3 }}>range mean · n={d.climate.n}</div>
            </div>
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--ink-muted)', marginTop: 11, lineHeight: 1.5 }}>
            {d.climate.belowFrostLine
              ? `Its cold edge sits below the ${d.climate.frostBand[0]}–${d.climate.frostBand[1]} °C frost line — a palm that holds on where most cannot.`
              : `Holds to the warm side of the ${d.climate.frostBand[0]}–${d.climate.frostBand[1]} °C frost line.`}
            {' '}Coldest-month mean at native occurrences (WorldClim × GBIF), not a measured cold tolerance.
          </div>
        </div>
      )}

      {c.source && (
        <div style={{ marginTop: 22, fontSize: 11.5, color: 'var(--ink-faint)' }}>
          Risk: {c.basis === 'assessed' ? 'Formal IUCN Red List assessment' : `Model prediction · ${c.source}`}
        </div>
      )}
    </div>
  )
}

function Badge({ children, color, muted }: { children: React.ReactNode; color?: string; muted?: boolean }) {
  return (
    <span style={{
      fontSize: 12, fontWeight: 600, padding: '4px 11px', borderRadius: 999,
      background: color ? color : 'transparent',
      color: color ? '#0D110C' : 'var(--ink-muted)',
      border: color ? 'none' : '1px solid var(--hairline)',
      opacity: muted ? 0.9 : 1,
    }}>{children}</span>
  )
}

import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Coverage, DataSource } from '../api/types'

export type PageNav = (s: 'workbench' | 'atlas' | 'guide' | 'palmline' | 'about' | 'sources') => void

/* ================================================================== */
/* About / How it works                                                */
/* ================================================================== */
// `ref` is the data_source id to jump to on the Sources page (omit for the
// infrastructure steps, which aren't cited datasets).
const PIPELINE: { k: string; v: string; ref?: string }[] = [
  { k: 'WCVP', v: 'names & synonymy', ref: 'wcvp' },
  { k: 'PalmTraits 1.0', v: 'morphology', ref: 'palmtraits' },
  { k: 'GBIF × WorldClim', v: 'points & climate', ref: 'gbif' },
  { k: 'Faurby 2016', v: 'phylogeny', ref: 'faurby2016' },
  { k: 'Bellot 2022', v: 'extinction risk', ref: 'bellot2022' },
  { k: 'PostGIS', v: 'spatial database' },
  { k: 'the atlas', v: 'the view you use' },
]

const CAVEATS = [
  {
    t: 'Extinction risk is mostly a model prediction, not an assessment',
    d: `Only about a fifth of palms carry a formal IUCN Red List assessment. The rest are covered by the
        peer-reviewed machine-learning model of Bellot et al. (2022), which predicts threatened /
        not-threatened from range, traits and environment. Every card says which it is — "Threatened
        (IUCN)" vs "Threatened (predicted)" — and the model's own two published scenarios put the
        threatened share of covered species between 50% (high-precision) and 72% (high-sensitivity). We
        report that as a range, never a single tidy number. Species with neither an assessment nor a
        prediction are shown as "not evaluated," which is not the same as "safe."`,
  },
  {
    t: 'The coldest-month temperature layer is derived, not measured on the palm',
    d: `The palm line is built by sampling WorldClim's coldest-month mean temperature at cleaned native
        GBIF occurrence points and aggregating per species. It describes the climate a species is found
        in — not a physiological cold-tolerance measured in a lab. It is flagged [derived] throughout.
        Occurrence records are also presence, not abundance: where botanists collect shapes the map.`,
  },
  {
    t: 'Native vs. introduced is decided by the range authority, not the dot',
    d: `Palms are among the most-planted ornamentals on Earth, so a raw occurrence map is full of gardens.
        Cultivated and managed records are dropped at the source, and every remaining point is tagged
        native or introduced by testing which TDWG botanical country it falls in against the species'
        WCVP native range. The frost line is drawn from native points only; the renegades are the palms
        that hold on past it.`,
  },
  {
    t: 'The tree has no branch support, and 14% of the family is off it',
    d: `The phylogeny is the Faurby et al. (2016) complete family supertree — 2,539 tips, 86% of accepted
        species reconciled onto it. The remaining ~14% are mostly genera described since 2015. The tree
        file carries branch lengths but no node-support values, so we do not display confidence we cannot
        source; closing that gap would need the PAFTOL backbone.`,
  },
  {
    t: 'Leaf architecture — fan vs. feather — is not in the trait data',
    d: `PalmTraits 1.0 records growth form, stem, armature and fruit, but has no pinnate/palmate field.
        Rather than guess it, we leave it out until it can be brought in from Genera Palmarum. Where a
        figure is quoted from a source rather than computed here, it is marked in place.`,
  },
]

export function About({ go, onSource }: { go: PageNav; onSource?: (id: string) => void }) {
  const [cov, setCov] = useState<Coverage | null>(null)
  useEffect(() => { api.coverage().then(setCov).catch(() => {}) }, [])
  const offTree = cov ? 100 - cov.tree_pct : 14

  return (
    <div className="page-wrap">
      <div className="page">
        <div className="page-eyebrow">About</div>
        <h1 className="page-title">How this atlas works</h1>

        <p className="page-lede">
          Palmae is a workbench for the whole palm family — where the {cov ? cov.total_species.toLocaleString() : '2,591'}{' '}
          species grow, how they are related, which are at risk, and the climate they live in. Nothing here
          is illustrative filler: every point, branch and status traces to a published dataset, and every
          approximation is labelled as one.
        </p>

        <h2 className="page-h2">The data pipeline</h2>
        <p className="page-p">
          Six authority datasets flow into one spatial database, are served over a small set of typed
          endpoints, and are drawn in the linked tree-and-map workbench. No figures are written by a model;
          predicted extinction risk is the one modelled layer, and it is always named as the Bellot et al.
          2022 prediction, never presented as ground truth.
        </p>
        <p className="page-note" style={{ border: 0, padding: 0, margin: '0 0 12px' }}>
          Each dataset step links to its full citation.
        </p>
        <div className="pipe">
          {PIPELINE.map((s, i) => (
            <div className="pipe-cell" key={s.k}>
              {s.ref
                ? (
                  <button className="pipe-step link" onClick={() => onSource?.(s.ref!)}
                    title={`See the citation for ${s.k}`}>
                    <div className="pipe-k">{s.k}</div>
                    <div className="pipe-v">{s.v}</div>
                  </button>
                )
                : (
                  <div className="pipe-step">
                    <div className="pipe-k">{s.k}</div>
                    <div className="pipe-v">{s.v}</div>
                  </div>
                )}
              {i < PIPELINE.length - 1 && <span className="pipe-arrow" aria-hidden>→</span>}
            </div>
          ))}
        </div>

        <h2 className="page-h2">The palm line, in plain language</h2>
        <p className="page-p">
          Palms are a tropical family that mostly cannot take a hard freeze, so where they grow traces the
          world's frost line with surprising fidelity. The paleoclimate literature makes this quantitative:
          fossil palms are read as a thermometer, indicating a coldest-month mean temperature of roughly
          2–8&nbsp;°C or warmer (Reichgelt, West &amp; Greenwood 2018). Below that, the family thins out.
        </p>
        <p className="page-p">
          Open the <button className="inline-link" onClick={() => go('palmline')}>Palm&nbsp;Line</button>{' '}
          and every native occurrence is coloured by the coldest-month mean temperature where it sits. The
          family snaps to the warm side of that line — and then a handful of <em>renegades</em> light up
          where they hold on past it: the windmill palm through European winters, the needle palm and dwarf
          palmetto into the American South, the Chilean wine palm and Nannorrhops on the cold margins. The
          same view is the grower's question turned around: <em>will it grow where I live?</em>
        </p>

        <h2 className="page-h2">What to trust, and what's approximate</h2>
        <div className="caveats">
          {CAVEATS.map((c) => (
            <div className="caveat" key={c.t}>
              <div className="caveat-t">{c.t}</div>
              <p className="caveat-d">{c.d}</p>
            </div>
          ))}
          <p className="page-note">
            {cov ? `${offTree}% of accepted species are off the tree; ` : ''}
            names, morphology, ranges and the phylogeny are family-complete; the derived climate layer and
            the predicted risk are the two places to read with care. All of it is cited on the{' '}
            <button className="inline-link" onClick={() => go('sources')}>sources page</button>.
          </p>
        </div>

        <h2 className="page-h2">On the name</h2>
        <p className="page-p">
          Botanically the family is <em>Arecaceae</em> — the type-based name (after the genus <em>Areca</em>),
          and the name used throughout the taxonomy and data here. <em>Palmae</em>, the wordmark, is not an
          oversight: it is one of just eight families whose traditional name the{' '}
          <em>International Code of Nomenclature</em> (Art. 18.5) conserves as an equally valid alternative to
          the standard <em>-aceae</em> form (alongside Gramineae/Poaceae and Compositae/Asteraceae). Arecaceae
          holds nomenclatural priority; Palmae is the name the palm world has always kept close — Dransfield
          and colleagues' <em>Genera Palmarum</em>, and the International Palm Society's journal{' '}
          <em>PALMS</em> — so we fly it as a deliberate nod to that tradition, not a lapse of it.
        </p>

        <h2 className="page-h2">Under the hood</h2>
        <p className="page-p">
          What you are using is a fully static site — there is no application server in the request path.
          The interface is React&nbsp;19 and TypeScript, bundled by Vite&nbsp;6 and served from Cloudflare&nbsp;Pages.
          The linked tree-and-map workbench is D3: the phylogenies are radial cluster layouts
          (<code className="mono">d3-hierarchy</code>) drawn straight from the Faurby and Yao topologies, and every
          map is a Natural&nbsp;Earth projection (<code className="mono">d3-geo</code>) over the TDWG WGSRPD level-3
          polygons, so a species range, a region click and a clade's footprint are all the same geometry.
        </p>
        <p className="page-p">
          The data spine is built ahead of time, not live. A Python pipeline loads the six datasets into
          PostgreSQL&nbsp;17 with the PostGIS extension (SQLAlchemy&nbsp;2 and GeoAlchemy2 over psycopg&nbsp;3,
          hosted on Supabase for the build), and a FastAPI layer defines the typed endpoints. At deploy time a
          bake step calls those route handlers <em>in-process</em> — no HTTP, no running server — and writes the
          entire API to static JSON under the site. The database therefore exists only while the site is being
          built; production is just files on a CDN. Photographs are hot-linked from iNaturalist under their
          Creative&nbsp;Commons licences rather than re-hosted, which keeps attribution intact and the payload small.
        </p>
        <div className="mono" style={{
          fontSize: 12.5, lineHeight: 1.9, color: 'var(--ink-muted)', margin: '2px 0 4px',
          padding: '12px 15px', border: '1px solid var(--hairline)', borderRadius: 9, overflowX: 'auto',
        }}>
          <div><span style={{ color: 'var(--gold)' }}>client&nbsp;&nbsp;</span> React 19 · TypeScript · D3 7 (d3-hierarchy, d3-geo) · Vite 6</div>
          <div><span style={{ color: 'var(--gold)' }}>build&nbsp;&nbsp;&nbsp;</span> Python ETL · FastAPI · SQLAlchemy 2 + GeoAlchemy2 · PostgreSQL 17 / PostGIS</div>
          <div><span style={{ color: 'var(--gold)' }}>serve&nbsp;&nbsp;&nbsp;</span> route handlers baked in-process → static JSON → Cloudflare Pages</div>
        </div>

        <h2 className="page-h2">Built for the palm community</h2>
        <p className="page-p">
          Attribution is a first-class surface here, not a footnote. The underlying datasets carry their own
          licences: WCVP is CC-BY, PalmTraits 1.0 and the Faurby tree are open (CC0), GBIF records are CC0 or
          CC-BY, WorldClim is CC-BY 4.0, and the Bellot risk model is CC-BY 4.0 from the authors' own release
          rather than a paywalled supplement. The IUCN Red List overlay is used non-commercially. Every one
          is credited in full, with its DOI, on the sources page.
        </p>
        <p className="page-p" style={{ marginTop: 22 }}>
          Built by{' '}
          <a href="https://bsky.app/profile/monstera999.bsky.social" target="_blank" rel="noreferrer"
            style={{ color: 'var(--gold)', textDecoration: 'none', borderBottom: '1px solid rgba(217,178,90,.4)' }}>
            Peter&nbsp;Repetti
          </a>.
        </p>
        <button className="page-cta" onClick={() => go('sources')}>
          Sources &amp; bibliography →
        </button>
      </div>
    </div>
  )
}

/* ================================================================== */
/* Sources & bibliography                                               */
/* ================================================================== */
function formatCitation(s: DataSource): string {
  const parts: string[] = []
  if (s.authors) parts.push(s.authors)
  if (s.year) parts.push(`(${s.year})`)
  if (s.title) parts.push(`${s.title}.`)
  if (s.venue) parts.push(s.venue + '.')
  return parts.join(' ')
}

export function Sources({ go, focus }: { go: PageNav; focus?: { id: string; n: number } | null }) {
  const [sources, setSources] = useState<DataSource[]>([])
  const [hl, setHl] = useState<string | null>(null)
  useEffect(() => { api.sources().then(setSources).catch(() => {}) }, [])
  // arriving from an About pipeline link → flash that citation and scroll to it.
  // Set the highlight immediately (it applies the moment the <li> renders); the
  // list loads async, so retry only the scroll until the target is in the DOM.
  useEffect(() => {
    if (!focus) return
    setHl(focus.id)
    const timers: number[] = [window.setTimeout(() => setHl(null), 2800)]
    let tries = 0
    const tick = () => {
      const el = document.getElementById(`ref-${focus.id}`)
      if (el) el.scrollIntoView({ block: 'center' })
      else if (tries++ < 30) timers.push(window.setTimeout(tick, 70))
    }
    timers.push(window.setTimeout(tick, 60))
    return () => timers.forEach(clearTimeout)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focus?.n])

  return (
    <div className="page-wrap">
      <div className="page">
        <div className="page-eyebrow">Data reference</div>
        <h1 className="page-title">Sources &amp; bibliography</h1>
        <p className="page-lede">
          Every dataset behind the atlas, with its full citation, licence, and the role it plays. Where the
          app shows a value quoted from a source rather than computed here, it points back to one of these.
        </p>

        <ol className="biblio">
          {sources.map((s) => (
            <li className={`bib${hl === s.id ? ' bib-hl' : ''}`} key={s.id} id={`ref-${s.id}`}>
              <div className="bib-head">
                <span className="bib-name">{s.name}</span>
                {s.role && <span className="bib-role">{s.role}</span>}
              </div>
              {formatCitation(s) && <div className="bib-cite">{formatCitation(s)}</div>}
              {s.note && <p className="bib-note">{s.note}</p>}
              <div className="bib-meta">
                {s.license && <span className="bib-lic">{s.license}</span>}
                {s.doi && (
                  <a className="bib-link" href={`https://doi.org/${s.doi}`} target="_blank" rel="noreferrer">
                    doi:{s.doi}
                  </a>
                )}
                {!s.doi && s.url && (
                  <a className="bib-link" href={s.url} target="_blank" rel="noreferrer">
                    {s.url.replace(/^https?:\/\//, '').replace(/\/$/, '')} →
                  </a>
                )}
              </div>
            </li>
          ))}
        </ol>

        <button className="page-cta ghost" onClick={() => go('about')}>← Back to about</button>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Coverage, DataSource } from '../api/types'

export type PageNav = (s: 'workbench' | 'atlas' | 'guide' | 'palmline' | 'about' | 'sources') => void

/* ================================================================== */
/* About / How it works                                                */
/* ================================================================== */
const PIPELINE = [
  { k: 'WCVP', v: 'names & synonymy' },
  { k: 'PalmTraits 1.0', v: 'morphology' },
  { k: 'GBIF × WorldClim', v: 'points & climate' },
  { k: 'Faurby 2016', v: 'phylogeny' },
  { k: 'Bellot 2022', v: 'extinction risk' },
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

export function About({ go }: { go: PageNav }) {
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
        <div className="pipe">
          {PIPELINE.map((s, i) => (
            <div className="pipe-cell" key={s.k}>
              <div className="pipe-step">
                <div className="pipe-k">{s.k}</div>
                <div className="pipe-v">{s.v}</div>
              </div>
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

        <h2 className="page-h2">Built for the palm community</h2>
        <p className="page-p">
          Attribution is a first-class surface here, not a footnote. The underlying datasets carry their own
          licences: WCVP is CC-BY, PalmTraits 1.0 and the Faurby tree are open (CC0), GBIF records are CC0 or
          CC-BY, WorldClim is CC-BY 4.0, and the Bellot risk model is CC-BY 4.0 from the authors' own release
          rather than a paywalled supplement. The IUCN Red List overlay is used non-commercially. Every one
          is credited in full, with its DOI, on the sources page.
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

export function Sources({ go }: { go: PageNav }) {
  const [sources, setSources] = useState<DataSource[]>([])
  useEffect(() => { api.sources().then(setSources).catch(() => {}) }, [])

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
            <li className="bib" key={s.id} id={`ref-${s.id}`}>
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

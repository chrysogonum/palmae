// Typed palm API client.
// - Dev: '/api/*' is proxied to the FastAPI server on :8001 (vite.config.ts).
// - Prod: the API is baked to static JSON under /api/*.json (etl/export_static.py).
//   Query-parameter endpoints can't be a single file, so in prod they map to
//   path-based baked files (ranges/{slug}.json, palm-line-introduced.json) and
//   /search is served from a client-side index. Keep these paths in lockstep with
//   export_static.py.
import type {
  Conservation, ConservationLens, Coverage, DataSource, PalmLineData, RegionRichness,
  RegionSpecies, RenegadeData, SearchResult, SpeciesRange, TaxonDetail, TaxonListItem, TreeNode,
} from './types'

const BASE = import.meta.env.VITE_API_BASE ?? '/api'
const PROD = import.meta.env.PROD

async function raw<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`API ${res.status} on ${url}`)
  return res.json() as Promise<T>
}

// Dev hits the live path; prod hits the baked file (path minus query, + .json).
function get<T>(path: string): Promise<T> {
  return raw<T>(PROD ? `${BASE}${path.split('?')[0]}.json` : `${BASE}${path}`)
}

// --- prod client-side search over the baked name index ---------------------- #
interface IndexRow { slug: string; latin: string; common: string | null; raw: string; status: string; color: string }
let _index: Promise<IndexRow[]> | null = null
function searchIndex(): Promise<IndexRow[]> {
  if (!_index) _index = raw<IndexRow[]>(`${BASE}/search-index.json`)
  return _index
}
async function searchProd(q: string): Promise<SearchResult[]> {
  const like = q.toLowerCase()
  const rows = (await searchIndex())
    .filter((r) => r.raw.toLowerCase().includes(like))
    .sort((a, b) => Number(b.status === 'accepted') - Number(a.status === 'accepted')
      || a.raw.length - b.raw.length || a.raw.localeCompare(b.raw))
  const seen = new Set<string>()
  const out: SearchResult[] = []
  for (const r of rows) {
    if (seen.has(r.slug)) continue
    seen.add(r.slug)
    const sub = r.status === 'synonym' ? `≡ synonym "${r.raw}"`
      : r.status === 'vernacular' ? `common name "${r.raw}"` : null
    out.push({ slug: r.slug, latin: r.latin, common: r.common, color: r.color, sub })
    if (out.length >= 14) break
  }
  return out
}

export const api = {
  sources: () => get<DataSource[]>('/sources'),
  search: (q: string) =>
    PROD ? searchProd(q) : get<SearchResult[]>(`/search?q=${encodeURIComponent(q)}`),
  ranges: () => get<RegionRichness[]>('/ranges'),
  speciesRange: (slug: string) =>
    raw<SpeciesRange[]>(PROD ? `${BASE}/ranges/${slug}.json` : `${BASE}/ranges?species=${slug}`),
  speciesRegions: () => get<Record<string, string[]>>('/species-regions'),
  regionSpecies: (code: string) => get<RegionSpecies[]>(`/regions/${code}/species`),
  taxa: () => get<TaxonListItem[]>('/taxa'),
  coverage: () => get<Coverage>('/taxa/coverage'),
  taxon: (slug: string) => get<TaxonDetail>(`/taxa/${slug}`),
  tree: () => get<TreeNode>('/tree'),
  treeGenera: () => get<TreeNode>('/tree/genera'),
  lensConservation: () => get<ConservationLens>('/lens/conservation'),
  palmLine: (introduced = false) =>
    raw<PalmLineData>(PROD
      ? `${BASE}/palm-line${introduced ? '-introduced' : ''}.json`
      : `${BASE}/palm-line${introduced ? '?introduced=1' : ''}`),
  renegades: () => get<RenegadeData>('/renegades'),
}

export type { Conservation }

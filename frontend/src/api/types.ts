// Types mirroring the palm API's response shapes.

export type Slug = string

export interface DataSource {
  id: string; name: string; role: string | null; license: string | null
  note: string | null; authors: string | null; year: number | null
  title: string | null; venue: string | null; doi: string | null; url: string | null
}

export interface SearchResult {
  slug: Slug; latin: string; common: string | null; color: string; sub: string | null
}

export interface RegionRichness { code: string; richness: number }
export interface RegionSpecies {
  slug: Slug; latin: string; subfamily: string | null
  risk: string; color: string; riskColor: string
}
export interface SpeciesRange { code: string; origin: 'native' | 'introduced' }

export interface TaxonListItem {
  slug: Slug; latin: string; common: string | null
  genus: string | null; tribe: string | null; subfamily: string | null
  color: string; risk: string; riskBasis: string | null; riskColor: string
  nRegions: number; endemic: boolean; hasTraits: boolean; onTree: boolean
  thumb: string | null
}
export interface Photo {
  url: string; attribution: string | null; license: string | null; sourceUrl: string | null
}

export interface Coverage {
  total_species: number; traits_pct: number; ranges_pct: number
  conservation_pct: number; tree_pct: number; threatened_of_assessed: number; note: string
}

export interface GlanceRow { k: string; v: string | null }
export interface Conservation {
  risk: string; riskLabel: string | null; riskColor: string; basis: string | null
  probability: number | null; iucn: string | null; iucnLabel: string | null; source: string | null
}
export interface ClimateProfile {
  cmmtMean: number; cmmtMin: number; n: number
  belowFrostLine: boolean; frostBand: [number, number]; note: string
}
export interface TaxonDetail {
  slug: Slug; latin: string; authority: string | null; common: string | null
  genus: string | null; tribe: string | null; subfamily: string | null; isHybrid: boolean
  color: string; glance: GlanceRow[]; conservation: Conservation
  climate: ClimateProfile | null; photo: Photo | null
  nativeRegions: RegionRef[]; introducedRegions: RegionRef[]; onTree: boolean
  traits: Record<string, string | number>
}
export interface RegionRef { code: string; name: string }

export interface PalmLinePoint {
  sp: Slug; lon: number; lat: number; cmmt: number; sub: string | null; native: boolean
}
export interface PalmLineData {
  points: PalmLinePoint[]
  frostLine: { band: [number, number]; pivot: number }
  renegadeSlugs: Slug[]
  note: string
}
export interface Renegade {
  slug: Slug; latin: string; common: string; subfamily: string | null; color: string
  note: string; cmmtMin: number | null; cmmtMean: number | null; n: number | null
}
export interface RenegadeData {
  frostLine: { band: [number, number]; pivot: number }
  species: Renegade[]
}

export interface TreeNode {
  children: TreeNode[]; len?: number; support?: number
  sp?: Slug; latin?: string; subfamily?: string | null; genus?: string | null
  color?: string; risk?: string; basis?: string | null
  // genus-tree (Yao 2023) tips only
  nSpecies?: number; regions?: string[]
}

export interface ConservationLens {
  bySubfamily: { subfamily: string; threatened: number; total: number; color: string }[]
  assessed: number; predicted: number; threatened: number; covered: number; note: string
}

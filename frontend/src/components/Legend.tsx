/** Shared key for the subfamily dot + conservation-risk chip encoding used in the
 *  clade view, the region panel, and the field guide. Pass the subfamilies to show
 *  (usually only those present in the current list) to keep it compact. */
const SUB_COLOR: Record<string, string> = {
  Arecoideae: '#4FB89A', Coryphoideae: '#E0A63C', Calamoideae: '#7F9CD6',
  Ceroxyloideae: '#A98BC0', Nypoideae: '#C15A4B',
}
const RISK_COLOR: Record<string, string> = {
  threatened: '#C1403C', 'not-threatened': '#6FBF73', 'not-evaluated': '#9AA0A6',
}
const RISK_LABEL: Record<string, string> = {
  threatened: 'threatened', 'not-threatened': 'not threatened', 'not-evaluated': 'not evaluated',
}
const subColor = (s: string | null | undefined) => (s && SUB_COLOR[s]) || '#4A5340'

function item(color: string, label: string, square: boolean) {
  return (
    <span key={label} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      <span style={{
        width: square ? 8 : 9, height: square ? 8 : 9, borderRadius: square ? 2 : '50%',
        background: color, flex: '0 0 auto',
      }} />
      <span style={{ color: 'var(--ink-muted)' }}>{label}</span>
    </span>
  )
}

const eyebrow: React.CSSProperties = {
  fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '.08em',
  textTransform: 'uppercase', color: 'var(--ink-faint)',
}

export function SubfamilyRiskLegend({ subs, style }: { subs: string[]; style?: React.CSSProperties }) {
  return (
    <div style={{
      display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '6px 16px',
      fontSize: 11.5, fontFamily: 'var(--font-body)', ...style,
    }}>
      {subs.length > 0 && (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={eyebrow}>● subfamily</span>
          {subs.map((s) => item(subColor(s), s, false))}
        </span>
      )}
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span style={eyebrow}>■ risk</span>
        {(['threatened', 'not-threatened', 'not-evaluated'] as const).map((r) => item(RISK_COLOR[r], RISK_LABEL[r], true))}
      </span>
    </div>
  )
}

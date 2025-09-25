import type { GraphSummary } from '../types';

interface GraphSummaryPanelProps {
  summary?: GraphSummary;
}

const severityLabelMap: Record<string, string> = {
  major: '重大风险',
  moderate: '中度风险',
  minor: '轻微风险',
  unknown: '未分级',
};

const GraphSummaryPanel = ({ summary }: GraphSummaryPanelProps) => {
  if (!summary) {
    return null;
  }

  const canonicalLevels = ['major', 'moderate', 'minor', 'unknown'];
  const seen = new Set<string>();
  const canonicalEntries = canonicalLevels.map((level) => {
    seen.add(level);
    return [level, summary.severity_breakdown[level] ?? 0] as const;
  });
  const additionalEntries = Object.entries(summary.severity_breakdown).filter(([level]) => {
    const normalized = level.toLowerCase();
    if (seen.has(normalized)) {
      return false;
    }
    seen.add(normalized);
    return true;
  });
  const severityEntries = [...canonicalEntries, ...additionalEntries];

  return (
    <div className="graph-summary">
      <div className="graph-summary__metrics">
        <div className="graph-summary__metric">
          <span className="graph-summary__metric-label">总节点</span>
          <strong className="graph-summary__metric-value">{summary.total_nodes}</strong>
        </div>
        <div className="graph-summary__metric">
          <span className="graph-summary__metric-label">总连线</span>
          <strong className="graph-summary__metric-value">{summary.total_links}</strong>
        </div>
        <div className="graph-summary__metric">
          <span className="graph-summary__metric-label">适应症</span>
          <strong className="graph-summary__metric-value">{summary.condition_count}</strong>
        </div>
        <div className="graph-summary__metric">
          <span className="graph-summary__metric-label">联用药物</span>
          <strong className="graph-summary__metric-value">{summary.partner_count}</strong>
        </div>
        <div className="graph-summary__metric">
          <span className="graph-summary__metric-label">相互作用</span>
          <strong className="graph-summary__metric-value">{summary.interaction_count}</strong>
        </div>
      </div>
      {severityEntries.length > 0 && (
        <div className="graph-summary__severity">
          {severityEntries.map(([level, count]) => {
            const normalized = level.toLowerCase();
            const label = severityLabelMap[normalized] ?? level;
            return (
              <span key={level} className={`severity-pill severity-pill--${normalized}`}>
                <span>{label}</span>
                <strong>{count}</strong>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default GraphSummaryPanel;

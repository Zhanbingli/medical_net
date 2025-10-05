import type { DrugDetail } from '../types';

interface DetailPanelProps {
  detail: DrugDetail | undefined;
  isLoading: boolean;
  errorMessage?: string;
}

const severityMap: Record<string, string> = {
  minor: 'severity-tag--minor',
  moderate: 'severity-tag--moderate',
  major: 'severity-tag--major',
};

const DetailPanel = ({ detail, isLoading, errorMessage }: DetailPanelProps) => {
  if (isLoading) {
    return (
      <div className="detail-panel card" role="status" aria-live="polite">
        <p className="panel-hint">药品信息加载中…</p>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="detail-panel card" role="alert" aria-live="assertive">
        <p className="panel-error">{errorMessage}</p>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="detail-panel card">
        <p className="panel-hint">请选择药品查看适应症与相互作用。</p>
      </div>
    );
  }

  return (
    <div className="detail-panel card" role="region" aria-label="药品详细信息">
      <header className="detail-panel__header">
        <div>
          <h2>{detail.name}</h2>
          {detail.atc_code && <span className="chip chip--muted">ATC {detail.atc_code}</span>}
        </div>
      </header>
      {detail.description && <p className="detail-panel__description">{detail.description}</p>}

      <section className="detail-section" aria-labelledby="indications-heading">
        <div className="detail-section__header">
          <h3 id="indications-heading">适应症</h3>
          <span className="detail-section__count" aria-label={`${detail.indications.length}项适应症`}>
            {detail.indications.length}
          </span>
        </div>
        {detail.indications.length === 0 ? (
          <p className="panel-hint">暂无关联记录。</p>
        ) : (
          <ul className="detail-list" aria-label="适应症列表">
            {detail.indications.map((item) => (
              <li key={item.id}>
                <div className="detail-list__title">{item.name}</div>
                <div className="detail-list__meta">
                  {item.evidence_level && (
                    <span className="chip chip--outline">证据 {item.evidence_level}</span>
                  )}
                </div>
                {item.usage_note && <p className="detail-list__note">{item.usage_note}</p>}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="detail-section" aria-labelledby="interactions-heading">
        <div className="detail-section__header">
          <h3 id="interactions-heading">相互作用</h3>
          <span className="detail-section__count" aria-label={`${detail.interactions.length}项相互作用`}>
            {detail.interactions.length}
          </span>
        </div>
        {detail.interactions.length === 0 ? (
          <p className="panel-hint">尚未记录交互风险。</p>
        ) : (
          <ul className="detail-list" aria-label="相互作用列表">
            {detail.interactions.map((item) => {
              const severityClass = item.severity
                ? severityMap[item.severity.toLowerCase()] ?? 'severity-tag--default'
                : 'severity-tag--default';
              return (
                <li key={item.id}>
                  <div className="detail-list__title">{item.interacting_drug_name ?? item.interacting_drug_id}</div>
                  <div className="detail-list__meta">
                    <span className={`severity-tag ${severityClass}`}>{item.severity ?? '未知'}</span>
                  </div>
                  {item.management && <p className="detail-list__note">{item.management}</p>}
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
};

export default DetailPanel;

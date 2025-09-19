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
      <div className="detail-panel card">
        <p className="panel-hint">药品信息加载中…</p>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="detail-panel card">
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
    <div className="detail-panel card">
      <header className="detail-panel__header">
        <div>
          <h2>{detail.name}</h2>
          {detail.atc_code && <span className="chip chip--muted">ATC {detail.atc_code}</span>}
        </div>
      </header>
      {detail.description && <p className="detail-panel__description">{detail.description}</p>}

      <section className="detail-section">
        <div className="detail-section__header">
          <h3>适应症</h3>
          <span className="detail-section__count">{detail.indications.length}</span>
        </div>
        {detail.indications.length === 0 ? (
          <p className="panel-hint">暂无关联记录。</p>
        ) : (
          <ul className="detail-list">
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

      <section className="detail-section">
        <div className="detail-section__header">
          <h3>相互作用</h3>
          <span className="detail-section__count">{detail.interactions.length}</span>
        </div>
        {detail.interactions.length === 0 ? (
          <p className="panel-hint">尚未记录交互风险。</p>
        ) : (
          <ul className="detail-list">
            {detail.interactions.map((item) => {
              const severityClass = severityMap[item.severity.toLowerCase()] ?? 'severity-tag--default';
              return (
                <li key={item.id}>
                  <div className="detail-list__title">{item.interacting_drug_name ?? item.interacting_drug_id}</div>
                  <div className="detail-list__meta">
                    <span className={`severity-tag ${severityClass}`}>{item.severity}</span>
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

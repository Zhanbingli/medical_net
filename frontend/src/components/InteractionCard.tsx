import { useState } from 'react';
import type { Interaction, Severity } from '../types';

const SEVERITY_LABEL: Record<Severity, string> = {
  major: '严重',
  moderate: '中等',
  minor: '轻度',
  theoretical: '理论',
};

const DIRECTION_LABEL: Record<string, string> = {
  increase: '↑ 西药效应增强',
  decrease: '↓ 西药效应减弱',
  variable: '⇅ 双向 / 个体差异',
};

const SOURCE_LABEL: Record<string, string> = {
  rct: 'RCT',
  cohort: '队列',
  case_report: '病例报告',
  case_series: '病例系列',
  pk_study: 'PK 研究',
  preclinical: '体外/动物',
  monograph: '说明书/指南',
  review: '综述',
};

export default function InteractionCard({ item }: { item: Interaction }) {
  const [expanded, setExpanded] = useState(false);
  const target = item.herb?.name_cn || item.formula?.name_cn || '?';
  const sub = item.herb?.name_latin || item.formula?.composition_text;

  return (
    <article className={`card-int card-int--${item.severity}`}>
      <header className="card-int__head">
        <span className={`pill pill--${item.severity}`}>
          {SEVERITY_LABEL[item.severity]}
        </span>
        <div className="card-int__title">
          <h3>
            {item.drug.name_cn}
            <span className="card-int__sep"> + </span>
            {target}
          </h3>
          {sub && <p className="card-int__sub">{sub}</p>}
        </div>
        <span className="card-int__ev">证据 {item.evidence_level}</span>
      </header>

      <p className="card-int__effect">
        <span className="card-int__direction">
          {DIRECTION_LABEL[item.direction] ?? item.direction}
        </span>
        {item.effect_cn}
      </p>

      <div className="card-int__action">
        <span className="card-int__action-label">临床建议</span>
        <p>{item.clinical_action}</p>
      </div>

      {(item.monitoring.length > 0 || item.high_risk_groups.length > 0) && (
        <div className="card-int__rows">
          {item.monitoring.length > 0 && (
            <div className="card-int__row">
              <span className="card-int__row-label">监测</span>
              <div className="chips">
                {item.monitoring.map((m) => (
                  <span key={m} className="chip">{m}</span>
                ))}
              </div>
            </div>
          )}
          {item.high_risk_groups.length > 0 && (
            <div className="card-int__row">
              <span className="card-int__row-label">高危人群</span>
              <div className="chips">
                {item.high_risk_groups.map((g) => (
                  <span key={g} className="chip chip--warn">{g}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <button
        type="button"
        className="card-int__toggle"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        {expanded ? '收起机制与证据 ▴' : '查看机制与证据 ▾'}
      </button>

      {expanded && (
        <div className="card-int__detail">
          <div className="card-int__row">
            <span className="card-int__row-label">机制</span>
            <p className="card-int__mech">{item.mechanism_summary_cn}</p>
          </div>

          {item.mechanisms.length > 0 && (
            <div className="card-int__row">
              <span className="card-int__row-label">机制节点</span>
              <ul className="mech-list">
                {item.mechanisms.map((m, idx) => (
                  <li key={idx}>
                    <span className="tag tag--mech">{m.type}</span>
                    <strong>{m.target}</strong>
                    {m.detail && <span className="mech-list__detail">{m.detail}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {item.evidences.length > 0 && (
            <div className="card-int__row">
              <span className="card-int__row-label">
                证据 ({item.evidences.length})
              </span>
              <ul className="evi-list">
                {item.evidences.map((ev, idx) => (
                  <li key={idx}>
                    <span className="tag tag--ev">
                      {SOURCE_LABEL[ev.source_type] ?? ev.source_type}
                    </span>
                    <span className="evi-list__cite">
                      {ev.citation || ev.evidence_keywords}
                    </span>
                    {ev.pmid && (
                      <a
                        href={`https://pubmed.ncbi.nlm.nih.gov/${ev.pmid}/`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        PMID {ev.pmid}
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {item.notes && (
            <div className="card-int__row">
              <span className="card-int__row-label">备注</span>
              <p className="card-int__notes">{item.notes}</p>
            </div>
          )}
        </div>
      )}
    </article>
  );
}

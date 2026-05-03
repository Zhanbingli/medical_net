import { useMemo, useState } from 'react';
import { useTcmInteractions, useTcmStats } from '../hooks/useTcmInteractions';
import type { TcmInteraction, TcmSeverity } from '../types';

const SEVERITY_LABEL: Record<TcmSeverity, string> = {
  major: '严重',
  moderate: '中等',
  minor: '轻度',
  theoretical: '理论',
};

const DIRECTION_LABEL: Record<string, string> = {
  increase: '↑ 西药效应增强',
  decrease: '↓ 西药效应减弱',
  variable: '⇅ 双向 / 个体差异大',
};

const DRUG_PRESETS = [
  '华法林',
  '阿司匹林',
  '氯吡格雷',
  '替格瑞洛',
  '达比加群',
  '利伐沙班',
  '阿哌沙班',
  '艾多沙班',
];

const SEVERITY_FILTERS: Array<{ value: TcmSeverity | 'all'; label: string }> = [
  { value: 'all', label: '全部' },
  { value: 'major', label: '仅严重' },
  { value: 'moderate', label: '仅中等' },
  { value: 'minor', label: '仅轻度' },
];

function severityClass(s: TcmSeverity): string {
  return `tcm-sev tcm-sev--${s}`;
}

function InteractionCard({ item }: { item: TcmInteraction }) {
  const [expanded, setExpanded] = useState(false);
  const target =
    item.herb?.name_cn || item.formula?.name_cn || '?';
  const targetSubtitle =
    item.herb?.name_latin || item.formula?.composition_text || '';

  return (
    <div className="tcm-card">
      <div className="tcm-card__head">
        <span className={severityClass(item.severity)}>
          {SEVERITY_LABEL[item.severity]}
        </span>
        <div className="tcm-card__title">
          <strong>
            {item.drug.name_cn} <span className="tcm-card__plus">+</span> {target}
          </strong>
          {targetSubtitle && (
            <small className="tcm-card__sub">{targetSubtitle}</small>
          )}
        </div>
        <div className="tcm-card__tags">
          <span className="tcm-tag">证据 {item.evidence_level}</span>
          {item.documentation && (
            <span className="tcm-tag tcm-tag--muted">{item.documentation}</span>
          )}
        </div>
      </div>

      <div className="tcm-card__effect">
        <span className="tcm-card__direction">
          {DIRECTION_LABEL[item.direction] ?? item.direction}
        </span>
        <p>{item.effect_cn}</p>
      </div>

      <div className="tcm-card__action">
        <span className="tcm-card__action-label">临床建议</span>
        <p>{item.clinical_action}</p>
      </div>

      {item.monitoring && item.monitoring.length > 0 && (
        <div className="tcm-card__row">
          <span className="tcm-card__row-label">监测</span>
          <div className="tcm-chips">
            {item.monitoring.map((m) => (
              <span key={m} className="tcm-chip">
                {m}
              </span>
            ))}
          </div>
        </div>
      )}

      {item.high_risk_groups && item.high_risk_groups.length > 0 && (
        <div className="tcm-card__row">
          <span className="tcm-card__row-label">高危人群</span>
          <div className="tcm-chips">
            {item.high_risk_groups.map((g) => (
              <span key={g} className="tcm-chip tcm-chip--warn">
                {g}
              </span>
            ))}
          </div>
        </div>
      )}

      <button
        type="button"
        className="tcm-card__toggle"
        onClick={() => setExpanded((v) => !v)}
      >
        {expanded ? '收起机制与证据 ▲' : '展开机制与证据 ▼'}
      </button>

      {expanded && (
        <div className="tcm-card__expanded">
          <div className="tcm-card__row">
            <span className="tcm-card__row-label">机制概述</span>
            <p className="tcm-card__mech">{item.mechanism_summary_cn}</p>
          </div>

          {item.mechanisms.length > 0 && (
            <div className="tcm-card__row">
              <span className="tcm-card__row-label">机制节点</span>
              <ul className="tcm-mech-list">
                {item.mechanisms.map((m, idx) => (
                  <li key={idx}>
                    <span className="tcm-tag tcm-tag--mech">{m.type}</span>
                    <strong>{m.target}</strong>
                    {m.detail && <span className="tcm-mech-detail">{m.detail}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {item.evidences.length > 0 && (
            <div className="tcm-card__row">
              <span className="tcm-card__row-label">
                证据 ({item.evidences.length})
              </span>
              <ul className="tcm-evi-list">
                {item.evidences.map((ev, idx) => (
                  <li key={idx}>
                    <span className="tcm-tag tcm-tag--ev">{ev.source_type}</span>
                    <span>{ev.citation || ev.evidence_keywords}</span>
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
            <div className="tcm-card__row">
              <span className="tcm-card__row-label">备注</span>
              <p className="tcm-card__notes">{item.notes}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function TcmInteractionsPanel() {
  const [drug, setDrug] = useState('华法林');
  const [severity, setSeverity] = useState<TcmSeverity | 'all'>('all');

  const params = useMemo(
    () => ({
      drug: drug.trim() || undefined,
      severity: severity === 'all' ? undefined : severity,
    }),
    [drug, severity]
  );

  const { data, isLoading, isError, error } = useTcmInteractions(params);
  const { data: stats } = useTcmStats();

  return (
    <section className="card tcm-panel">
      <div className="section-heading">
        <div>
          <h2>中药 × 西药相互作用</h2>
          <p className="section-subtitle">
            以心血管抗凝/抗血小板药物为核心, 30 条经过分级的循证条目.
            所有 'major' 条目应作为处方提示, 'theoretical' 仅供参考.
          </p>
        </div>
        {stats && (
          <div className="tcm-stats">
            <span className="tcm-stat">
              总计 <strong>{stats.total_interactions}</strong>
            </span>
            <span className="tcm-stat tcm-stat--major">
              严重 <strong>{stats.by_severity.major ?? 0}</strong>
            </span>
            <span className="tcm-stat tcm-stat--moderate">
              中等 <strong>{stats.by_severity.moderate ?? 0}</strong>
            </span>
            <span className="tcm-stat tcm-stat--minor">
              轻度 <strong>{stats.by_severity.minor ?? 0}</strong>
            </span>
          </div>
        )}
      </div>

      <div className="tcm-controls">
        <label className="tcm-control">
          <span>西药</span>
          <input
            type="text"
            list="tcm-drug-presets"
            value={drug}
            onChange={(e) => setDrug(e.target.value)}
            placeholder="例: 华法林 / B01AA03"
          />
          <datalist id="tcm-drug-presets">
            {DRUG_PRESETS.map((d) => (
              <option key={d} value={d} />
            ))}
          </datalist>
        </label>
        <div className="tcm-control">
          <span>严重度</span>
          <div className="tcm-seg">
            {SEVERITY_FILTERS.map((f) => (
              <button
                key={f.value}
                type="button"
                className={`tcm-seg__btn ${severity === f.value ? 'is-active' : ''}`}
                onClick={() => setSeverity(f.value)}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="tcm-results">
        {isLoading && <p className="tcm-empty">加载中…</p>}
        {isError && (
          <p className="tcm-empty tcm-empty--error">
            查询失败: {error instanceof Error ? error.message : '未知错误'}
          </p>
        )}
        {!isLoading && !isError && data && data.items.length === 0 && (
          <p className="tcm-empty">未找到相关互作.</p>
        )}
        {!isLoading && data && data.items.length > 0 && (
          <>
            <p className="tcm-summary">
              共 <strong>{data.total}</strong> 条 (按严重度排序)
            </p>
            <div className="tcm-list">
              {data.items.map((item) => (
                <InteractionCard key={item.id} item={item} />
              ))}
            </div>
          </>
        )}
      </div>

      <p className="tcm-disclaimer">
        ⚠️ 本工具为临床<strong>参考</strong>用途, 不替代医生判断.
        所有条目须结合患者具体情况评估; 标注 D 级证据的条目为机制推测,
        缺乏 robust 临床数据.
      </p>
    </section>
  );
}

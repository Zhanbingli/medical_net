import { useMemo } from 'react';
import InteractionCard from './InteractionCard';
import type { BatchCheckResult, Severity } from '../types';

const SEVERITY_ORDER: Severity[] = ['major', 'moderate', 'minor', 'theoretical'];
const SEVERITY_TITLE: Record<Severity, string> = {
  major: '严重 · 避免合用',
  moderate: '中等 · 谨慎合用',
  minor: '轻度 · 留意',
  theoretical: '理论 · 仅参考',
};

interface Props {
  result: BatchCheckResult;
  onBack: () => void;
}

export default function RiskReport({ result, onBack }: Props) {
  const groups = useMemo(() => {
    const g: Partial<Record<Severity, typeof result.interactions>> = {};
    for (const item of result.interactions) {
      const arr = g[item.severity] ?? [];
      arr.push(item);
      g[item.severity] = arr;
    }
    return g;
  }, [result.interactions]);

  const involved = useMemo(() => {
    const ids = new Set<string>();
    for (const i of result.interactions) {
      ids.add(i.drug.id);
      if (i.herb) ids.add(i.herb.id);
      if (i.formula) ids.add(i.formula.id);
    }
    return ids;
  }, [result.interactions]);

  const cleared = result.items.filter(
    (it) => it.type !== 'unknown' && it.matched_id && !involved.has(it.matched_id)
  );
  const unknowns = result.items.filter((it) => it.type === 'unknown');

  const total = result.interactions.length;
  const summary = result.summary;

  return (
    <div className="report">
      <header className="report__head">
        <button type="button" className="btn-back" onClick={onBack}>
          ← 修改药单
        </button>
        <div>
          <h2>风险报告</h2>
          <p className="report__sub">
            共 <strong>{total}</strong> 条互作 · 检索 {result.items.length} 项药物
          </p>
        </div>
      </header>

      <div className="report__counts">
        {SEVERITY_ORDER.map((s) => (
          <div key={s} className={`count count--${s}`}>
            <span className="count__num">{summary[s] ?? 0}</span>
            <span className="count__label">{SEVERITY_TITLE[s].split(' · ')[0]}</span>
          </div>
        ))}
      </div>

      {total === 0 ? (
        <div className="report__empty">
          <p>✅ 未发现录入数据库的互作</p>
          <p className="report__empty-note">
            注意: 本工具仅覆盖心血管抗凝/抗血小板药 × 中药.
            其他药物组合 (如普通西药 DDI) 暂不在范围, 请同时咨询用药助手或药师.
          </p>
        </div>
      ) : (
        <div className="report__sections">
          {SEVERITY_ORDER.map((sev) => {
            const items = groups[sev] ?? [];
            if (items.length === 0) return null;
            return (
              <section key={sev} className={`section section--${sev}`}>
                <h3 className={`section__title section__title--${sev}`}>
                  {SEVERITY_TITLE[sev]}
                  <span className="section__count">{items.length}</span>
                </h3>
                <div className="section__cards">
                  {items.map((it) => (
                    <InteractionCard key={it.id} item={it} />
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}

      {(cleared.length > 0 || unknowns.length > 0) && (
        <footer className="report__footer">
          {cleared.length > 0 && (
            <div className="report__group">
              <span className="report__group-label">✓ 无明确互作</span>
              <div className="chips">
                {cleared.map((c, i) => (
                  <span key={i} className="chip chip--clean">
                    {c.matched_name}
                  </span>
                ))}
              </div>
            </div>
          )}
          {unknowns.length > 0 && (
            <div className="report__group">
              <span className="report__group-label">⚠ 未识别</span>
              <div className="chips">
                {unknowns.map((c, i) => (
                  <span key={i} className="chip chip--unknown">
                    {c.raw}
                  </span>
                ))}
              </div>
              <p className="report__group-note">
                这些项目不在数据库中. 可能是: 药名拼写、罕用药、或暂未收录.
                请单独核查.
              </p>
            </div>
          )}
        </footer>
      )}
    </div>
  );
}

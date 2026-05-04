import { useEffect, useRef, useState } from 'react';
import { useDebouncedValue } from '../hooks/useDebouncedValue';
import { useLookup } from '../hooks/useLookup';
import type { LookupResult } from '../types';

const TYPE_LABEL: Record<LookupResult['type'], string> = {
  drug: '西药',
  herb: '中药',
  formula: '中成药/方剂',
};

const PRESET_EXAMPLES = [
  ['华法林', '复方丹参滴丸', '阿托伐他汀'],
  ['阿司匹林', '氯吡格雷', '银杏叶'],
  ['利伐沙班', '丹参', '三七'],
  ['达比加群', '贯叶连翘 (圣约翰草)'],
];

interface Props {
  medications: string[];
  onAdd: (item: string) => void;
  onRemove: (idx: number) => void;
  onClear: () => void;
  onSubmit: () => void;
  isSubmitting?: boolean;
}

export default function MedicationInput({
  medications,
  onAdd,
  onRemove,
  onClear,
  onSubmit,
  isSubmitting,
}: Props) {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounced = useDebouncedValue(query, 200);
  const { data: suggestions = [] } = useLookup(debounced);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (debounced.length >= 1) setShowSuggestions(true);
  }, [debounced]);

  function pick(name: string) {
    const trimmed = name.trim();
    if (!trimmed) return;
    if (medications.includes(trimmed)) {
      setQuery('');
      setShowSuggestions(false);
      return;
    }
    onAdd(trimmed);
    setQuery('');
    setShowSuggestions(false);
    inputRef.current?.focus();
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (suggestions.length > 0) {
        pick(suggestions[0].name_cn);
      } else if (query.trim()) {
        pick(query);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  }

  const canSubmit = medications.length > 0 && !isSubmitting;

  return (
    <div className="med-input">
      <div className="med-input__field">
        <label className="med-input__label" htmlFor="med-input-q">
          病人正在使用的药物
        </label>
        <div className="med-input__box">
          <input
            id="med-input-q"
            ref={inputRef}
            type="text"
            placeholder="输入药名 (如: 华法林 / 丹参 / 复方丹参滴丸)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => debounced && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            onKeyDown={onKeyDown}
            autoComplete="off"
          />
          {query && (
            <button
              type="button"
              className="med-input__clear"
              onClick={() => {
                setQuery('');
                inputRef.current?.focus();
              }}
              aria-label="清空"
            >
              ✕
            </button>
          )}
          {showSuggestions && suggestions.length > 0 && (
            <ul className="med-input__suggestions" role="listbox">
              {suggestions.map((s) => (
                <li
                  key={`${s.type}-${s.id}`}
                  role="option"
                  aria-selected={false}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    pick(s.name_cn);
                  }}
                >
                  <span className={`tag tag--${s.type}`}>{TYPE_LABEL[s.type]}</span>
                  <span className="med-input__sugg-name">{s.name_cn}</span>
                  {s.extra && <span className="med-input__sugg-extra">{s.extra}</span>}
                </li>
              ))}
            </ul>
          )}
        </div>
        <p className="med-input__hint">
          回车选第一条 · 没有匹配时直接回车按原文添加 (会标"未识别")
        </p>
      </div>

      {medications.length > 0 ? (
        <div className="med-list">
          <div className="med-list__head">
            <span>当前药单 · {medications.length} 项</span>
            <button type="button" className="med-list__clear" onClick={onClear}>
              全部清空
            </button>
          </div>
          <ul className="med-list__items">
            {medications.map((m, i) => (
              <li key={`${m}-${i}`} className="med-chip">
                <span className="med-chip__name">{m}</span>
                <button
                  type="button"
                  className="med-chip__remove"
                  onClick={() => onRemove(i)}
                  aria-label={`移除 ${m}`}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="med-presets">
          <span className="med-presets__label">或试试这些场景:</span>
          <div className="med-presets__grid">
            {PRESET_EXAMPLES.map((example, i) => (
              <button
                key={i}
                type="button"
                className="med-presets__btn"
                onClick={() => example.forEach((m) => onAdd(m))}
              >
                {example.join(' · ')}
              </button>
            ))}
          </div>
        </div>
      )}

      <button
        type="button"
        className="btn-primary"
        onClick={onSubmit}
        disabled={!canSubmit}
      >
        {isSubmitting ? '检查中…' : '检查风险'}
      </button>
    </div>
  );
}

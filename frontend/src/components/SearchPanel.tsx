import type { FormEvent } from 'react';
import type { DrugSummary } from '../types';

interface SearchPanelProps {
  value: string;
  onChange: (value: string) => void;
  suggestions: DrugSummary[];
  onSelect: (drug: DrugSummary) => void;
  selectedId: string | null;
  isLoading: boolean;
}

const SearchPanel = ({ value, onChange, suggestions, onSelect, selectedId, isLoading }: SearchPanelProps) => {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (suggestions.length > 0) {
      onSelect(suggestions[0]);
    }
  };

  return (
    <div className="search-panel">
      <form className="search-panel__form" onSubmit={handleSubmit}>
        <label className="search-panel__label" htmlFor="drug-search">
          搜索药品
        </label>
        <div className="search-panel__input">
          <input
            id="drug-search"
            value={value}
            onChange={(event) => onChange(event.target.value)}
            placeholder="输入药品名称或 ATC 编码"
            autoComplete="off"
          />
          <button type="submit">快速定位</button>
        </div>
      </form>
      <div className="search-panel__suggestions">
        {isLoading && <p className="search-panel__hint">检索中…</p>}
        {!isLoading && suggestions.length === 0 && (
          <p className="search-panel__hint">暂无匹配药品，尝试调整关键字。</p>
        )}
        {!isLoading && suggestions.length > 0 && (
          <ul>
            {suggestions.slice(0, 8).map((drug) => {
              const isActive = drug.id === selectedId;
              return (
                <li key={drug.id}>
                  <button
                    type="button"
                    className={isActive ? 'is-active' : ''}
                    onClick={() => onSelect(drug)}
                  >
                    <span className="search-panel__drug-name">{drug.name}</span>
                    {drug.atc_code && <span className="search-panel__badge">ATC {drug.atc_code}</span>}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
};

export default SearchPanel;

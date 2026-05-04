import { useState } from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import MedicationInput from './components/MedicationInput';
import RiskReport from './components/RiskReport';
import { useBatchCheck } from './hooks/useBatchCheck';

function App() {
  const [medications, setMedications] = useState<string[]>([]);
  const check = useBatchCheck();

  const result = check.data;
  const showReport = !!result;

  function add(item: string) {
    setMedications((prev) => (prev.includes(item) ? prev : [...prev, item]));
  }

  function remove(idx: number) {
    setMedications((prev) => prev.filter((_, i) => i !== idx));
  }

  function clear() {
    setMedications([]);
  }

  function submit() {
    if (medications.length === 0) return;
    check.mutate(medications);
  }

  function back() {
    check.reset();
  }

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__brand">
          <span className="app__logo">⚕</span>
          <div>
            <h1>掌上抗凝-中药速查</h1>
            <p>心血管抗凝/抗血小板药 × 中药相互作用风险检查</p>
          </div>
        </div>
      </header>

      <main className="app__main">
        <ErrorBoundary>
          {!showReport ? (
            <MedicationInput
              medications={medications}
              onAdd={add}
              onRemove={remove}
              onClear={clear}
              onSubmit={submit}
              isSubmitting={check.isPending}
            />
          ) : (
            <RiskReport result={result} onBack={back} />
          )}
        </ErrorBoundary>

        {check.isError && !showReport && (
          <div className="error-banner">
            查询失败:
            {check.error instanceof Error
              ? ` ${check.error.message}`
              : ' 未知错误'}
          </div>
        )}
      </main>

      <footer className="app__footer">
        <p>
          <strong>免责声明:</strong> 本工具为临床<strong>参考</strong>用途,
          基于公开循证数据 + 临床判断, 不替代医师决策.
          标注 D 级证据的条目为机制推测, 缺乏稳健临床数据.
        </p>
        <p className="app__footer-meta">
          Phase 1 · 心血管抗凝 30 条 · 仅供执业医师使用
        </p>
      </footer>
    </div>
  );
}

export default App;

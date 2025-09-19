import { useMemo, useState } from 'react';
import GraphCanvas from './components/GraphCanvas';
import SearchPanel from './components/SearchPanel';
import DetailPanel from './components/DetailPanel';
import StatusMessage from './components/StatusMessage';
import { useDrugDetail } from './hooks/useDrugDetail';
import { useDrugGraph } from './hooks/useDrugGraph';
import { useDrugSearch } from './hooks/useDrugSearch';
import { useDrugCatalog } from './hooks/useDrugCatalog';
import type { DrugSummary } from './types';

const DEFAULT_DRUG_ID = 'drug_001';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDrugId, setSelectedDrugId] = useState<string | null>(DEFAULT_DRUG_ID);

  const { data: catalog, isLoading: catalogLoading } = useDrugCatalog();
  const { data: searchResults, isFetching: searchLoading } = useDrugSearch(searchTerm);
  const {
    data: graph,
    isLoading: graphLoading,
    isError: graphError,
    error: graphErrorObj,
  } = useDrugGraph(selectedDrugId);
  const {
    data: detail,
    isLoading: detailLoading,
    isError: detailError,
    error: detailErrorObj,
  } = useDrugDetail(selectedDrugId);

  const normalizedTerm = searchTerm.trim();
  const suggestions = useMemo(() => {
    if (normalizedTerm.length >= 2) {
      return searchResults ?? [];
    }
    return catalog ?? [];
  }, [catalog, searchResults, normalizedTerm]);

  const suggestionLoading = normalizedTerm.length >= 2 ? searchLoading : catalogLoading;

  const handleSelect = (drug: DrugSummary) => {
    setSelectedDrugId(drug.id);
    setSearchTerm(drug.name);
  };

  const graphErrorMessage = graphError
    ? graphErrorObj instanceof Error
      ? graphErrorObj.message
      : '图谱数据暂时不可用，请稍后再试。'
    : undefined;

  const detailErrorMessage = detailError
    ? detailErrorObj instanceof Error
      ? detailErrorObj.message
      : '无法获取药品详情。'
    : undefined;

  const hasGraphData = graph && graph.nodes.length > 0;

  return (
    <div className="app-shell">
      <header className="hero-card card">
        <div className="hero-text">
          <span className="badge">临床试运行</span>
          <h1>药物知识图谱与用药风险雷达</h1>
          <p>
            快速对照药物适应症、识别潜在联用风险，并追踪证据来源，帮助医师在秒级完成用药交叉验证。
          </p>
        </div>
        <SearchPanel
          value={searchTerm}
          onChange={setSearchTerm}
          suggestions={suggestions}
          onSelect={handleSelect}
          selectedId={selectedDrugId}
          isLoading={suggestionLoading}
        />
      </header>

      <main className="content-grid">
        <section className="graph-card card">
          <div className="section-heading">
            <div>
              <h2>用药关联图谱</h2>
              <p className="section-subtitle">拖拽节点查看药物、适应症与联用风险之间的连接。</p>
            </div>
          </div>
          <div className="graph-area">
            {graphLoading && (
              <StatusMessage tone="info" title="图谱构建中…" description="正在载入节点与关系数据。" />
            )}
            {graphError && (
              <StatusMessage tone="error" title="图谱加载失败" description={graphErrorMessage} />
            )}
            {!graphLoading && !graphError && !hasGraphData && (
              <StatusMessage tone="empty" title="暂无图谱" description="尚未找到可视化数据，尝试搜索其他药品。" />
            )}
            {hasGraphData && <GraphCanvas graph={graph} className="graph-canvas" />}
          </div>
        </section>

        <DetailPanel detail={detail} isLoading={detailLoading} errorMessage={detailErrorMessage} />
      </main>
    </div>
  );
}

export default App;

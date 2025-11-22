import { useCallback, useEffect, useMemo, useState } from 'react';
import GraphCanvas from './components/GraphCanvas';
import SearchPanel from './components/SearchPanel';
import DetailPanel from './components/DetailPanel';
import StatusMessage from './components/StatusMessage';
import GraphSummaryPanel from './components/GraphSummaryPanel';
import GraphLegend from './components/GraphLegend';
import ErrorBoundary from './components/ErrorBoundary';
import { useDrugDetail } from './hooks/useDrugDetail';
import { useDrugGraph } from './hooks/useDrugGraph';
import { useDrugSearch } from './hooks/useDrugSearch';
import { useDrugCatalog } from './hooks/useDrugCatalog';
import { useDebouncedValue } from './hooks/useDebouncedValue';
import { getErrorMessage } from './utils/errorHandling';
import type { DrugSummary, GraphNode } from './types';

const DEFAULT_DRUG_ID = 'drug_001';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDrugId, setSelectedDrugId] = useState<string | null>(DEFAULT_DRUG_ID);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);

  const { data: catalog, isLoading: catalogLoading } = useDrugCatalog();
  const debouncedSearchTerm = useDebouncedValue(searchTerm, 220);
  const { data: searchResults, isFetching: searchLoading } = useDrugSearch(debouncedSearchTerm);
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

  const normalizedTerm = useMemo(() => searchTerm.trim(), [searchTerm]);
  const suggestions = useMemo(() => {
    if (normalizedTerm.length >= 2) {
      return searchResults ?? [];
    }
    return catalog ?? [];
  }, [catalog, searchResults, normalizedTerm]);

  const suggestionLoading = normalizedTerm.length >= 2 ? searchLoading : catalogLoading;

  useEffect(() => {
    if (!catalog || catalog.length === 0) return;
    const first = catalog[0];
    // 如果当前选中的药物不存在于目录中，默认选中第一条，避免空白界面
    if (!selectedDrugId || !catalog.some((item) => item.id === selectedDrugId)) {
      setSelectedDrugId(first.id);
      setSearchTerm(first.name);
    }
  }, [catalog, selectedDrugId]);

  const handleSelect = (drug: DrugSummary) => {
    setSelectedDrugId(drug.id);
    setSearchTerm(drug.name);
  };

  const handleClearSearch = useCallback(() => {
    setSearchTerm('');
  }, []);

  const handleNodeSelect = useCallback(
    (node: GraphNode) => {
      if (node.type === 'drug') {
        setSelectedDrugId(node.id);
        setSearchTerm(node.label);
      }
    },
    []
  );

  const handleNodeHover = useCallback((node: GraphNode | null) => {
    setHoveredNode(node);
  }, []);

  useEffect(() => {
    if (graphLoading || graphError) {
      setHoveredNode(null);
    }
  }, [graphLoading, graphError]);

  const graphErrorMessage = useMemo(
    () => (graphError ? getErrorMessage(graphErrorObj, '图谱数据暂时不可用，请稍后再试。') : undefined),
    [graphError, graphErrorObj]
  );

  const detailErrorMessage = useMemo(
    () => (detailError ? getErrorMessage(detailErrorObj, '无法获取药品详情。') : undefined),
    [detailError, detailErrorObj]
  );

  const hasGraphData = useMemo(() => graph && graph.nodes.length > 0, [graph]);

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
          onClear={handleClearSearch}
        />
      </header>

      <main className="content-grid">
        <section className="graph-card card">
          <div className="section-heading">
            <div>
              <h2>用药关联图谱</h2>
              <p className="section-subtitle">拖拽节点查看药物、适应症与联用风险之间的连接。</p>
            </div>
            <GraphLegend />
          </div>
          {graph?.summary && <GraphSummaryPanel summary={graph.summary} />}
          {hoveredNode && (
            <div className="graph-hover-card">
              <span className={`graph-hover-card__badge graph-hover-card__badge--${hoveredNode.type}`}>
                {hoveredNode.type === 'drug' ? '药品' : '适应症'}
              </span>
              <strong className="graph-hover-card__title">{hoveredNode.label}</strong>
              {hoveredNode.description && <p>{hoveredNode.description}</p>}
            </div>
          )}
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
            {hasGraphData && graph && (
              <ErrorBoundary>
                <GraphCanvas
                  graph={graph}
                  className="graph-canvas"
                  selectedNodeId={selectedDrugId}
                  onNodeSelect={handleNodeSelect}
                  onNodeHover={handleNodeHover}
                />
              </ErrorBoundary>
            )}
          </div>
        </section>

        <ErrorBoundary>
          <DetailPanel detail={detail} isLoading={detailLoading} errorMessage={detailErrorMessage} />
        </ErrorBoundary>
      </main>
    </div>
  );
}

export default App;

const GraphLegend = () => {
  return (
    <div className="graph-legend" aria-hidden="true">
      <div className="graph-legend__item">
        <span className="graph-legend__swatch graph-legend__swatch--drug" />
        <span className="graph-legend__label">药品节点</span>
      </div>
      <div className="graph-legend__item">
        <span className="graph-legend__swatch graph-legend__swatch--condition" />
        <span className="graph-legend__label">适应症节点</span>
      </div>
    </div>
  );
};

export default GraphLegend;

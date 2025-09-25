import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { DrugGraph, GraphNode } from '../types';

interface GraphCanvasProps {
  graph: DrugGraph;
  className?: string;
  selectedNodeId?: string | null;
  onNodeSelect?: (node: GraphNode) => void;
  onNodeHover?: (node: GraphNode | null) => void;
}

const GraphCanvas = ({ graph, className, selectedNodeId, onNodeSelect, onNodeHover }: GraphCanvasProps) => {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const selectHandlerRef = useRef(onNodeSelect);
  const hoverHandlerRef = useRef(onNodeHover);

  useEffect(() => {
    selectHandlerRef.current = onNodeSelect;
  }, [onNodeSelect]);

  useEffect(() => {
    hoverHandlerRef.current = onNodeHover;
  }, [onNodeHover]);

  useEffect(() => {
    if (!svgRef.current) {
      return;
    }

    const svgElement = svgRef.current;
    const svg = d3.select(svgElement);
    svg.selectAll('*').remove();

    const width = svgElement.clientWidth || 800;
    const height = svgElement.clientHeight || 480;

    const nodes = graph.nodes.map((node) => ({ ...node }));
    const links = graph.links.map((link) => ({ ...link }));

    const adjacency = new Map<string, Set<string>>();
    for (const link of links) {
      const sourceId = typeof link.source === 'string' ? link.source : String((link.source as any).id ?? link.source);
      const targetId = typeof link.target === 'string' ? link.target : String((link.target as any).id ?? link.target);
      if (!adjacency.has(sourceId)) {
        adjacency.set(sourceId, new Set());
      }
      if (!adjacency.has(targetId)) {
        adjacency.set(targetId, new Set());
      }
      adjacency.get(sourceId)!.add(targetId);
      adjacency.get(targetId)!.add(sourceId);
    }

    const simulation = d3
      .forceSimulation(nodes as any)
      .force('link', d3.forceLink(links as any).id((d: any) => d.id).distance(150))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const link = svg
      .append('g')
      .attr('class', 'graph-links')
      .attr('stroke', '#d1d5db')
      .attr('stroke-width', 1.5)
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('class', 'graph-link');

    link.append('title').text((d) => d.label ?? '');

    const node = svg
      .append('g')
      .attr('class', 'graph-nodes')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('class', (d) => `graph-node graph-node--${d.type}`)
      .attr('r', 20)
      .attr('fill', (d) => (d.type === 'drug' ? '#2563eb' : '#10b981'));

    node.append('title').text((d) => d.description ?? d.label);

    const labels = svg
      .append('g')
      .attr('class', 'graph-labels')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .attr('class', 'graph-label')
      .attr('text-anchor', 'middle')
      .attr('dy', 4)
      .text((d) => d.label)
      .attr('fill', '#111827')
      .attr('font-size', '0.75rem');

    const updateFocus = (focusedId: string | null) => {
      if (!focusedId) {
        node.classed('is-focused', false).classed('is-dimmed', false);
        labels.classed('is-focused', false).classed('is-dimmed', false);
        link.classed('is-focused', false).classed('is-dimmed', false);
        return;
      }

      const connected = new Set<string>([focusedId]);
      const adjacent = adjacency.get(focusedId);
      if (adjacent) {
        adjacent.forEach((id) => connected.add(id));
      }

      node
        .classed('is-focused', (d: any) => d.id === focusedId)
        .classed('is-dimmed', (d: any) => !connected.has(d.id));

      labels
        .classed('is-focused', (d: any) => d.id === focusedId)
        .classed('is-dimmed', (d: any) => !connected.has(d.id));

      link
        .classed('is-focused', (d: any) => {
          const sourceId = typeof d.source === 'object' ? (d.source as any).id : d.source;
          const targetId = typeof d.target === 'object' ? (d.target as any).id : d.target;
          return sourceId === focusedId || targetId === focusedId;
        })
        .classed('is-dimmed', (d: any) => {
          const sourceId = typeof d.source === 'object' ? (d.source as any).id : d.source;
          const targetId = typeof d.target === 'object' ? (d.target as any).id : d.target;
          return !connected.has(sourceId) && !connected.has(targetId);
        });
    };

    const dragBehaviour = d3
      .drag<SVGCircleElement, any>()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    node
      .call(dragBehaviour as any)
      .on('click', (_event, d: GraphNode & { id: string }) => {
        selectHandlerRef.current?.(d);
      })
      .on('mouseenter', (_event, d: GraphNode & { id: string }) => {
        updateFocus(d.id);
        hoverHandlerRef.current?.(d);
      })
      .on('mouseleave', () => {
        updateFocus(selectedNodeId ?? null);
        hoverHandlerRef.current?.(null);
      });

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => (d.source as any).x)
        .attr('y1', (d: any) => (d.source as any).y)
        .attr('x2', (d: any) => (d.target as any).x)
        .attr('y2', (d: any) => (d.target as any).y);

      node.attr('cx', (d: any) => d.x).attr('cy', (d: any) => d.y);
      labels.attr('x', (d: any) => d.x).attr('y', (d: any) => d.y - 30);
    });

    updateFocus(selectedNodeId ?? null);

    return () => {
      simulation.stop();
      hoverHandlerRef.current?.(null);
    };
  }, [graph, selectedNodeId]);

  return <svg ref={svgRef} className={className} role="img" aria-label="药物关联图" />;
};

export default GraphCanvas;

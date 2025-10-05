import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { DrugGraph, GraphNode, D3SimulationNode, D3SimulationLink } from '../types';

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

    const nodes: D3SimulationNode[] = graph.nodes.map((node) => ({ ...node }));
    const links: D3SimulationLink[] = graph.links.map((link) => ({ ...link }));

    // Helper function to get node ID from link source/target
    const getNodeId = (node: string | D3SimulationNode): string => {
      return typeof node === 'string' ? node : node.id;
    };

    const adjacency = new Map<string, Set<string>>();
    for (const link of links) {
      const sourceId = getNodeId(link.source);
      const targetId = getNodeId(link.target);
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
      .forceSimulation<D3SimulationNode>(nodes)
      .force(
        'link',
        d3.forceLink<D3SimulationNode, D3SimulationLink>(links)
          .id((d) => d.id)
          .distance(150)
      )
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
        .classed('is-focused', (d) => d.id === focusedId)
        .classed('is-dimmed', (d) => !connected.has(d.id));

      labels
        .classed('is-focused', (d) => d.id === focusedId)
        .classed('is-dimmed', (d) => !connected.has(d.id));

      link
        .classed('is-focused', (d) => {
          const sourceId = getNodeId(d.source);
          const targetId = getNodeId(d.target);
          return sourceId === focusedId || targetId === focusedId;
        })
        .classed('is-dimmed', (d) => {
          const sourceId = getNodeId(d.source);
          const targetId = getNodeId(d.target);
          return !connected.has(sourceId) && !connected.has(targetId);
        });
    };

    const dragBehaviour = d3
      .drag<SVGCircleElement, D3SimulationNode>()
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
      .call(dragBehaviour as any) // D3 drag typing is complex with generics
      .on('click', (_event, d) => {
        selectHandlerRef.current?.(d);
      })
      .on('mouseenter', (_event, d) => {
        updateFocus(d.id);
        hoverHandlerRef.current?.(d);
      })
      .on('mouseleave', () => {
        updateFocus(selectedNodeId ?? null);
        hoverHandlerRef.current?.(null);
      });

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => {
          const source = typeof d.source === 'object' ? d.source : nodes.find(n => n.id === d.source);
          return source?.x ?? 0;
        })
        .attr('y1', (d) => {
          const source = typeof d.source === 'object' ? d.source : nodes.find(n => n.id === d.source);
          return source?.y ?? 0;
        })
        .attr('x2', (d) => {
          const target = typeof d.target === 'object' ? d.target : nodes.find(n => n.id === d.target);
          return target?.x ?? 0;
        })
        .attr('y2', (d) => {
          const target = typeof d.target === 'object' ? d.target : nodes.find(n => n.id === d.target);
          return target?.y ?? 0;
        });

      node.attr('cx', (d) => d.x ?? 0).attr('cy', (d) => d.y ?? 0);
      labels.attr('x', (d) => d.x ?? 0).attr('y', (d) => (d.y ?? 0) - 30);
    });

    updateFocus(selectedNodeId ?? null);

    // Cleanup function to prevent memory leaks
    return () => {
      simulation.stop();

      // Remove all event listeners
      node.on('.drag', null);
      node.on('click', null);
      node.on('mouseenter', null);
      node.on('mouseleave', null);

      // Clear D3 selections
      svg.selectAll('*').remove();

      // Reset hover state
      hoverHandlerRef.current?.(null);
    };
  }, [graph, selectedNodeId]);

  return <svg ref={svgRef} className={className} role="img" aria-label="药物关联图" />;
};

export default GraphCanvas;

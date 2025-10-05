import { useCallback } from 'react';
import type * as d3 from 'd3';
import type { D3SimulationNode, D3SimulationLink } from '../types';

interface UseGraphFocusParams {
  adjacency: Map<string, Set<string>>;
  nodeSelection: d3.Selection<SVGCircleElement, D3SimulationNode, SVGGElement, unknown>;
  labelSelection: d3.Selection<SVGTextElement, D3SimulationNode, SVGGElement, unknown>;
  linkSelection: d3.Selection<SVGLineElement, D3SimulationLink, SVGGElement, unknown>;
}

export const useGraphFocus = ({
  adjacency,
  nodeSelection,
  labelSelection,
  linkSelection,
}: UseGraphFocusParams) => {
  const updateFocus = useCallback(
    (focusedId: string | null) => {
      if (!focusedId) {
        nodeSelection.classed('is-focused', false).classed('is-dimmed', false);
        labelSelection.classed('is-focused', false).classed('is-dimmed', false);
        linkSelection.classed('is-focused', false).classed('is-dimmed', false);
        return;
      }

      const connected = new Set<string>([focusedId]);
      const adjacent = adjacency.get(focusedId);
      if (adjacent) {
        adjacent.forEach((id) => connected.add(id));
      }

      // Helper to get node ID from link source/target
      const getNodeId = (node: string | D3SimulationNode): string => {
        return typeof node === 'string' ? node : node.id;
      };

      nodeSelection
        .classed('is-focused', (d) => d.id === focusedId)
        .classed('is-dimmed', (d) => !connected.has(d.id));

      labelSelection
        .classed('is-focused', (d) => d.id === focusedId)
        .classed('is-dimmed', (d) => !connected.has(d.id));

      linkSelection
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
    },
    [adjacency, nodeSelection, labelSelection, linkSelection]
  );

  return { updateFocus };
};

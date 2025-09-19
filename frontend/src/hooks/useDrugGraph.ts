import { useQuery } from '@tanstack/react-query';
import { fetchDrugGraph } from '../api/client';
import type { DrugGraph } from '../types';

export const useDrugGraph = (drugId: string | null) => {
  return useQuery<DrugGraph>({
    queryKey: ['drug-graph', drugId],
    queryFn: () => fetchDrugGraph(drugId as string),
    enabled: Boolean(drugId),
  });
};

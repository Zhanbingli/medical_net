import { useQuery } from '@tanstack/react-query';
import { searchDrugs } from '../api/client';
import type { DrugSummary } from '../types';

export const useDrugSearch = (query: string) => {
  const normalized = query.trim();

  return useQuery<DrugSummary[]>({
    queryKey: ['drug-search', normalized],
    queryFn: () => searchDrugs(normalized),
    enabled: normalized.length >= 2,
    staleTime: 2 * 60 * 1000,
  });
};

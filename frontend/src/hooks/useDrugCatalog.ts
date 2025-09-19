import { useQuery } from '@tanstack/react-query';
import { searchDrugs } from '../api/client';
import type { DrugSummary } from '../types';

export const useDrugCatalog = () => {
  return useQuery<DrugSummary[]>({
    queryKey: ['drug-catalog'],
    queryFn: () => searchDrugs(),
    staleTime: 10 * 60 * 1000,
  });
};

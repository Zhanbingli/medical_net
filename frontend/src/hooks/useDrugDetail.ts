import { useQuery } from '@tanstack/react-query';
import { fetchDrugDetail } from '../api/client';
import type { DrugDetail } from '../types';

export const useDrugDetail = (drugId: string | null) => {
  return useQuery<DrugDetail>({
    queryKey: ['drug-detail', drugId],
    queryFn: () => fetchDrugDetail(drugId as string),
    enabled: Boolean(drugId),
    staleTime: 5 * 60 * 1000,
  });
};

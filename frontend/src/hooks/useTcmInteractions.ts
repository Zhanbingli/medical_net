import { useQuery } from '@tanstack/react-query';
import { fetchTcmInteractions, fetchTcmStats, FetchTcmInteractionsParams } from '../api/tcm';

export const useTcmInteractions = (params: FetchTcmInteractionsParams) =>
  useQuery({
    queryKey: ['tcm-interactions', params],
    queryFn: () => fetchTcmInteractions(params),
    staleTime: 60 * 1000,
  });

export const useTcmStats = () =>
  useQuery({
    queryKey: ['tcm-stats'],
    queryFn: fetchTcmStats,
    staleTime: 5 * 60 * 1000,
  });

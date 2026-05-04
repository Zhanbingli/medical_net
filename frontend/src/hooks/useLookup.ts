import { useQuery } from '@tanstack/react-query';
import { lookup } from '../api/tcm';

export const useLookup = (q: string) =>
  useQuery({
    queryKey: ['tcm-lookup', q],
    queryFn: () => lookup(q),
    enabled: q.trim().length >= 1,
    staleTime: 60 * 1000,
  });

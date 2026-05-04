import { useMutation } from '@tanstack/react-query';
import { batchCheck } from '../api/tcm';

export const useBatchCheck = () =>
  useMutation({
    mutationFn: (items: string[]) => batchCheck(items),
  });

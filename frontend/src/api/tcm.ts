import axios from 'axios';
import type { BatchCheckResult, LookupResult } from '../types';

const client = axios.create({ baseURL: '/api/v1' });

export async function lookup(q: string): Promise<LookupResult[]> {
  const query = q.trim();
  if (!query) return [];
  const { data } = await client.get<LookupResult[]>('/tcm/lookup', {
    params: { q: query, limit: 8 },
  });
  return data;
}

export async function batchCheck(items: string[]): Promise<BatchCheckResult> {
  const { data } = await client.post<BatchCheckResult>('/tcm/batch-check', { items });
  return data;
}

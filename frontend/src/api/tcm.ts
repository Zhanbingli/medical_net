import axios from 'axios';
import type { TcmInteractionList, TcmStats, TcmSeverity } from '../types';

const client = axios.create({ baseURL: '/api/v1' });

export interface FetchTcmInteractionsParams {
  drug?: string;
  herb?: string;
  severity?: TcmSeverity;
}

export async function fetchTcmInteractions(
  params: FetchTcmInteractionsParams = {}
): Promise<TcmInteractionList> {
  const cleaned: Record<string, string> = {};
  if (params.drug?.trim()) cleaned.drug = params.drug.trim();
  if (params.herb?.trim()) cleaned.herb = params.herb.trim();
  if (params.severity) cleaned.severity = params.severity;

  const { data } = await client.get<TcmInteractionList>('/tcm/interactions', {
    params: cleaned,
  });
  return data;
}

export async function fetchTcmStats(): Promise<TcmStats> {
  const { data } = await client.get<TcmStats>('/tcm/stats');
  return data;
}

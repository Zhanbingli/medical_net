import axios from 'axios';
import type { DrugDetail, DrugGraph, DrugSummary } from '../types';

const client = axios.create({
  baseURL: '/api/v1',
});

export async function fetchDrugDetail(drugId: string): Promise<DrugDetail> {
  const { data } = await client.get<DrugDetail>(`/drugs/${drugId}`);
  return data;
}

export async function fetchDrugGraph(drugId: string): Promise<DrugGraph> {
  const { data } = await client.get<DrugGraph>(`/drugs/${drugId}/graph`);
  return data;
}

export async function searchDrugs(query?: string): Promise<DrugSummary[]> {
  const params = query?.trim() ? { q: query.trim() } : undefined;
  const { data } = await client.get<DrugSummary[]>('/drugs/', { params });
  return data;
}

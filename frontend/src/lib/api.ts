import { SearchParams, Drug, DrugDetails, SearchResponse } from '@/types';

const API_BASE_URL = typeof window !== 'undefined'
  ? (process.env.NEXT_PUBLIC_API_URL || window.location.origin)
  : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

interface SearchRequest {
  query: string;
  query_type: 'disease' | 'gene' | 'sequence';
  max_results?: number;
}

export async function searchDrugs(params: SearchParams): Promise<SearchResponse> {
  const request: SearchRequest = {
    query: params.query,
    query_type: params.queryType,
    max_results: params.maxResults,
  };

  const response = await fetch(`${API_BASE_URL}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Search failed' }));
    throw new Error(error.detail || 'Search failed');
  }

  return response.json();
}

export async function getDrugDetails(chemblId: string): Promise<DrugDetails> {
  const response = await fetch(`${API_BASE_URL}/api/drug/${chemblId}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Drug not found' }));
    throw new Error(error.detail || 'Drug not found');
  }

  return response.json();
}

export async function getStats(): Promise<{
  total_drugs: number;
  total_targets: number;
  predictions_made: number;
}> {
  const response = await fetch(`${API_BASE_URL}/api/stats`);

  if (!response.ok) {
    throw new Error('Failed to fetch stats');
  }

  return response.json();
}

export async function healthCheck(): Promise<{
  status: string;
  message: string;
  version: string;
}> {
  const response = await fetch(`${API_BASE_URL}/`);

  if (!response.ok) {
    throw new Error('Health check failed');
  }

  return response.json();
}


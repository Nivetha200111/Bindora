export type QueryType = 'disease' | 'gene' | 'sequence';

export interface SearchParams {
  query: string;
  queryType: QueryType;
  maxResults: number;
}

export interface Drug {
  chembl_id: string;
  name: string | null;
  smiles: string;
  binding_score: number;
  molecular_weight: number;
  logp: number;
  hbd: number;  // H-bond donors
  hba: number;  // H-bond acceptors
  tpsa: number; // Topological polar surface area
  is_drug_like: boolean;
  clinical_phase: number;
}

export interface DrugDetails extends Drug {
  description?: string;
  inchi_key?: string;
  properties: {
    [key: string]: number;
  };
  similar_drugs: string[];
  clinical_trials?: ClinicalTrial[];
}

export interface ClinicalTrial {
  nct_id: string;
  title: string;
  phase: string;
  status: string;
}

export interface SearchFilters {
  clinicalPhase?: number[];
  molecularWeightRange?: [number, number];
  bindingScoreRange?: [number, number];
  drugLikeOnly?: boolean;
}

export interface SearchResponse {
  results: Drug[];
  total: number;
  query: string;
  query_type: string;
}


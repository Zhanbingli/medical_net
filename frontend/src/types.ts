export interface GraphNode {
  id: string;
  label: string;
  type: 'drug' | 'condition';
  description?: string | null;
}

export interface GraphLink {
  source: string;
  target: string;
  label?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface DrugGraph {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface DrugConditionSummary {
  id: string;
  name: string;
  description?: string | null;
  evidence_level?: string | null;
  usage_note?: string | null;
}

export interface DrugInteractionSummary {
  id: string;
  interacting_drug_id: string;
  interacting_drug_name?: string | null;
  severity: string;
  mechanism?: string | null;
  management?: string | null;
}

export interface DrugDetail {
  id: string;
  name: string;
  description?: string | null;
  atc_code?: string | null;
  indications: DrugConditionSummary[];
  interactions: DrugInteractionSummary[];
}

export interface DrugSummary {
  id: string;
  name: string;
  description?: string | null;
  atc_code?: string | null;
}

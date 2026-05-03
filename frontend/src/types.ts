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

export interface GraphSummary {
  total_nodes: number;
  total_links: number;
  condition_count: number;
  interaction_count: number;
  partner_count: number;
  severity_breakdown: Record<string, number>;
}

export interface DrugGraph {
  nodes: GraphNode[];
  links: GraphLink[];
  summary: GraphSummary;
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

// ===== TCM × Western drug interactions =====

export interface TcmDrugBrief {
  id: string;
  name_cn: string;
  atc_code?: string | null;
}

export interface TcmHerbBrief {
  id: string;
  name_cn: string;
  name_pinyin?: string | null;
  name_latin?: string | null;
}

export interface TcmFormulaBrief {
  id: string;
  name_cn: string;
  composition_text?: string | null;
}

export interface TcmEvidenceBrief {
  source_type: string;
  citation: string;
  pmid?: string | null;
  doi?: string | null;
  summary_cn?: string | null;
  evidence_keywords?: string | null;
}

export interface TcmMechanism {
  type?: string | null;
  target?: string | null;
  detail?: string | null;
}

export type TcmSeverity = 'major' | 'moderate' | 'minor' | 'theoretical';

export interface TcmInteraction {
  id: string;
  drug: TcmDrugBrief;
  herb?: TcmHerbBrief | null;
  formula?: TcmFormulaBrief | null;
  severity: TcmSeverity;
  direction: 'increase' | 'decrease' | 'variable';
  onset?: string | null;
  documentation?: string | null;
  evidence_level: string;
  effect_cn: string;
  mechanism_summary_cn: string;
  mechanisms: TcmMechanism[];
  clinical_action: string;
  monitoring: string[];
  high_risk_groups: string[];
  notes?: string | null;
  evidences: TcmEvidenceBrief[];
}

export interface TcmInteractionList {
  total: number;
  items: TcmInteraction[];
}

export interface TcmStats {
  total_interactions: number;
  by_severity: Record<string, number>;
  by_evidence_level: Record<string, number>;
  by_direction: Record<string, number>;
}

// D3 Force Simulation Types
export interface D3SimulationNode extends GraphNode {
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  index?: number;
}

export interface D3SimulationLink {
  source: string | D3SimulationNode;
  target: string | D3SimulationNode;
  label?: string | null;
  metadata?: Record<string, unknown> | null;
  index?: number;
}

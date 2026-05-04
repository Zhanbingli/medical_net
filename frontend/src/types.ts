// 中药 × 西药相互作用 - 前端类型

export type Severity = 'major' | 'moderate' | 'minor' | 'theoretical';
export type Direction = 'increase' | 'decrease' | 'variable';
export type EntityType = 'drug' | 'herb' | 'formula' | 'unknown';

export interface DrugBrief {
  id: string;
  name_cn: string;
  atc_code?: string | null;
}

export interface HerbBrief {
  id: string;
  name_cn: string;
  name_pinyin?: string | null;
  name_latin?: string | null;
}

export interface FormulaBrief {
  id: string;
  name_cn: string;
  composition_text?: string | null;
}

export interface Mechanism {
  type?: string | null;
  target?: string | null;
  detail?: string | null;
}

export interface Evidence {
  source_type: string;
  citation: string;
  pmid?: string | null;
  doi?: string | null;
  summary_cn?: string | null;
  evidence_keywords?: string | null;
}

export interface Interaction {
  id: string;
  drug: DrugBrief;
  herb?: HerbBrief | null;
  formula?: FormulaBrief | null;
  severity: Severity;
  direction: Direction;
  onset?: string | null;
  documentation?: string | null;
  evidence_level: string;
  effect_cn: string;
  mechanism_summary_cn: string;
  mechanisms: Mechanism[];
  clinical_action: string;
  monitoring: string[];
  high_risk_groups: string[];
  notes?: string | null;
  evidences: Evidence[];
}

export interface LookupResult {
  type: 'drug' | 'herb' | 'formula';
  id: string;
  name_cn: string;
  extra?: string | null;
}

export interface ClassifiedItem {
  raw: string;
  type: EntityType;
  matched_id?: string | null;
  matched_name?: string | null;
}

export interface BatchCheckResult {
  items: ClassifiedItem[];
  interactions: Interaction[];
  summary: Partial<Record<Severity, number>>;
}

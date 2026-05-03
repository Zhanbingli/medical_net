// =============================================================================
// 中药-西药相互作用知识图谱 - Neo4j Schema
// 范围: 心血管抗凝/抗血小板药物 + 中药 (Phase 1)
// =============================================================================
//
// 设计原则:
// 1. 互作不是直接 Drug→Herb 的扁平边, 而是经由 Mechanism (机制节点) 产生:
//    Drug --[METABOLIZED_BY]--> Enzyme <--[INHIBITS]-- Component <--[CONTAINS]-- Herb
//    这样系统能**解释**互作, 而不是死记硬背.
// 2. 每条临床相关边 (Interaction) 必须挂证据 (Evidence). 没有证据的边不入库.
// 3. 同一 Herb 可有多 Component, 不同方剂中比例不同 → Formula 节点处理复方.
// 4. 中药/西药命名都用稳定 ID, 显示名通过别名节点 (Alias) 关联.
// =============================================================================


// ----- Constraints (确保唯一性) -----

CREATE CONSTRAINT drug_id IF NOT EXISTS
  FOR (d:Drug) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT herb_id IF NOT EXISTS
  FOR (h:Herb) REQUIRE h.id IS UNIQUE;

CREATE CONSTRAINT formula_id IF NOT EXISTS
  FOR (f:Formula) REQUIRE f.id IS UNIQUE;

CREATE CONSTRAINT component_id IF NOT EXISTS
  FOR (c:Component) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT enzyme_id IF NOT EXISTS
  FOR (e:Enzyme) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT transporter_id IF NOT EXISTS
  FOR (t:Transporter) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT target_id IF NOT EXISTS
  FOR (tg:Target) REQUIRE tg.id IS UNIQUE;

CREATE CONSTRAINT pathway_id IF NOT EXISTS
  FOR (p:Pathway) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT interaction_id IF NOT EXISTS
  FOR (i:Interaction) REQUIRE i.id IS UNIQUE;

CREATE CONSTRAINT evidence_id IF NOT EXISTS
  FOR (ev:Evidence) REQUIRE ev.id IS UNIQUE;


// ----- Indexes (查询性能) -----

CREATE INDEX drug_atc IF NOT EXISTS FOR (d:Drug) ON (d.atc_code);
CREATE INDEX drug_rxcui IF NOT EXISTS FOR (d:Drug) ON (d.rxcui);
CREATE INDEX herb_pinyin IF NOT EXISTS FOR (h:Herb) ON (h.name_pinyin);
CREATE INDEX herb_latin IF NOT EXISTS FOR (h:Herb) ON (h.name_latin);
CREATE INDEX interaction_severity IF NOT EXISTS FOR (i:Interaction) ON (i.severity);


// =============================================================================
// 节点定义 (示例 - 实际数据通过 ingest pipeline 写入)
// =============================================================================

// --- Drug (西药) ---
// MERGE (d:Drug {
//   id: "DRUG-WARFARIN",
//   name_en: "Warfarin",
//   name_cn: "华法林",
//   atc_code: "B01AA03",
//   rxcui: "11289",
//   drug_class: "Vitamin K antagonist",
//   therapeutic_index: "narrow"     // narrow / wide
// });

// --- Herb (中药材) ---
// MERGE (h:Herb {
//   id: "HERB-DANSHEN",
//   name_cn: "丹参",
//   name_pinyin: "danshen",
//   name_latin: "Salvia miltiorrhiza",
//   parts_used: ["root", "rhizome"],
//   pharmacopoeia: "ChP2020"        // 中国药典版本
// });

// --- Formula (方剂) ---
// MERGE (f:Formula {
//   id: "FORMULA-FUFANG-DANSHEN",
//   name_cn: "复方丹参滴丸",
//   composition_text: "丹参、三七、冰片"
// });

// --- Component (活性成分) ---
// MERGE (c:Component {
//   id: "COMP-TANSHINONE-IIA",
//   name_en: "Tanshinone IIA",
//   name_cn: "丹参酮IIA",
//   chembl_id: "CHEMBL...",
//   pubchem_cid: "164676"
// });

// --- Enzyme (代谢酶) ---
// MERGE (e:Enzyme {
//   id: "ENZ-CYP2C9",
//   name: "CYP2C9",
//   family: "Cytochrome P450",
//   ec_number: "1.14.14.1"
// });

// --- Transporter (转运体) ---
// MERGE (t:Transporter {
//   id: "TR-PGP",
//   name: "P-glycoprotein",
//   gene: "ABCB1"
// });

// --- Pathway (生物通路) ---
// MERGE (p:Pathway {
//   id: "PW-COAGULATION-CASCADE",
//   name_en: "Coagulation cascade",
//   name_cn: "凝血级联"
// });

// --- Interaction (互作记录, 顶层临床条目) ---
// MERGE (i:Interaction {
//   id: "INT-WF-DS-001",
//   severity: "major",                     // major / moderate / minor / theoretical
//   direction: "increase",                 // increase / decrease / variable
//   effect_cn: "INR 升高、出血风险增加",
//   effect_en: "Increased INR, bleeding risk",
//   evidence_level: "B",                   // A / B / C / D (类 ACCP/Oxford CEBM)
//   onset: "delayed",                      // rapid / delayed
//   documentation: "established",          // established / probable / suspected / theoretical
//   clinical_action: "避免合用; 已合用者 1-2 周内复测 INR",
//   monitoring: ["INR", "出血体征"],
//   high_risk_groups: ["老年", "肝功能不全", "INR 不稳定"],
//   created_at: datetime(),
//   curator: "user@example.com",
//   reviewed: false
// });

// --- Evidence (证据条目, 必须挂在 Interaction 上) ---
// MERGE (ev:Evidence {
//   id: "EV-PMID-9131309",
//   source_type: "case_report",            // rct / cohort / case_report / pk_study / preclinical / monograph
//   citation: "Yu CM et al. Aust N Z J Med 1997;27:175",
//   pmid: "9131309",
//   doi: null,
//   url: null,
//   summary_cn: "62岁女性, 服用华法林+丹参出现 INR 8.4 与皮下血肿"
// });


// =============================================================================
// 关系定义
// =============================================================================
//
// (Drug)        -[METABOLIZED_BY]->        (Enzyme)            // 底物
// (Drug)        -[INHIBITS]->              (Enzyme|Transporter) {ki, ic50}
// (Drug)        -[INDUCES]->               (Enzyme|Transporter)
// (Drug)        -[SUBSTRATE_OF]->          (Transporter)
// (Drug)        -[BINDS]->                 (Target) {affinity}
// (Drug)        -[AFFECTS]->               (Pathway) {direction}
//
// (Herb)        -[CONTAINS]->              (Component) {abundance}
// (Herb)        -[USED_IN]->               (Formula)
// (Component)   -[INHIBITS|INDUCES]->      (Enzyme|Transporter)
// (Component)   -[BINDS]->                 (Target)
// (Component)   -[AFFECTS]->               (Pathway)
//
// (Interaction) -[INVOLVES_DRUG]->         (Drug)
// (Interaction) -[INVOLVES_HERB]->         (Herb)
// (Interaction) -[INVOLVES_FORMULA]->      (Formula)
// (Interaction) -[VIA_MECHANISM]->         (Enzyme|Transporter|Pathway|Target)
// (Interaction) -[SUPPORTED_BY]->          (Evidence)
// (Interaction) -[ALTERNATIVE_TO]->        (Interaction)         // 推荐替代方案


// =============================================================================
// 关键查询示例 (这些就是临床医生想要的"问题")
// =============================================================================

// Q1: 我开了华法林, 病人在吃哪些中药需要警惕?
// MATCH (d:Drug {name_cn: "华法林"})<-[:INVOLVES_DRUG]-(i:Interaction)-[:INVOLVES_HERB]->(h:Herb)
// WHERE i.severity IN ["major", "moderate"]
// RETURN h.name_cn, i.severity, i.effect_cn, i.clinical_action
// ORDER BY i.severity DESC;

// Q2: 丹参为什么和华法林互作? (机制溯源)
// MATCH path = (h:Herb {name_cn: "丹参"})-[:CONTAINS]->(c:Component)
//              -[:INHIBITS|INDUCES|BINDS]->(target)
//              <-[:METABOLIZED_BY|SUBSTRATE_OF|BINDS]-(d:Drug {name_cn: "华法林"})
// RETURN path;

// Q3: 这条互作的证据强度?
// MATCH (i:Interaction {id: "INT-WF-DS-001"})-[:SUPPORTED_BY]->(ev:Evidence)
// RETURN ev.source_type, ev.citation, ev.summary_cn
// ORDER BY CASE ev.source_type
//   WHEN "rct" THEN 1 WHEN "cohort" THEN 2 WHEN "case_report" THEN 3
//   WHEN "pk_study" THEN 4 WHEN "preclinical" THEN 5 ELSE 6 END;

// Q4: 同样通过 CYP2C9 抑制与华法林互作的中药有哪些?
// MATCH (d:Drug {name_cn: "华法林"})-[:METABOLIZED_BY]->(e:Enzyme {name: "CYP2C9"})
//       <-[:INHIBITS]-(c:Component)<-[:CONTAINS]-(h:Herb)
// RETURN DISTINCT h.name_cn, collect(DISTINCT c.name_cn) AS via_components;

# Clause dataset

`clauses.csv` has 266 clauses: 141 employment, 125 tenancy.

| column | meaning |
|---|---|
| id | C001... |
| doc_type | `employment` or `tenancy` |
| text | one clause |
| labels | the LegalAudit rule ID the clause addresses (E001-E020, T001-T018), or empty if it addresses none of the 38 topics |
| style | `standard`, `paraphrase`, `none`, `near_miss` (see below) |

**Labelling rule.** A clause gets rule X if it states, restricts or provides for the topic of rule X
(for presence rules: the clause would satisfy the rule; for risk rules E010, E012, E015, T012: the clause is the
risky provision). Every clause has at most one label.

**Styles.**
- `standard`: 3 per rule. Conventional legal wording, the kind a keyword list is written for.
- `paraphrase`: 3 per rule. Same obligation in plain or unusual wording.
- `none`: boilerplate (parties, signatures, entire agreement).
- `near_miss`: looks close to a rule but addresses none of them (for example "inform the Company in writing of any change of address").

**Origin and limits.**
- The clauses were written for this study, not taken from real contracts. They were drafted with AI assistance.
  Author review: PENDING (change this line once you have read and corrected every label).
- Written by one person (plus the AI) who knew the keyword lists, so the standard/paraphrase split is a stress test,
  not a measurement of how often real contracts use unusual wording.
- 6 clauses per rule is small. Treat per-rule numbers as indicative only.
- Single annotator, so there is no inter-annotator agreement figure yet.

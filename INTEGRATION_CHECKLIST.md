# THE MOON — Integration Checklist

**Owner:** Project Lead / AI-ML Integration  
**Deadline:** 27 October 2026

## A. Project Lead — Member 1

- [ ] Finalize architecture and user interaction flow.
- [ ] Publish `PROJECT_CONTRACT.md` Draft v0.1.
- [ ] Share JSON examples with all members.
- [ ] Confirm module input/output formats with each member.
- [ ] Assign component deadlines and track progress.
- [ ] Verify that scientific claims can be traced to evidence.

## B. Member Deliverables and Handoffs

| Owner | Required deliverable | Deadline |
|---|---|---|
| Member 1: Project Lead | Architecture, schema, API contracts, integration checklist | 27 Oct |
| Member 2: Frontend | Five connected dashboard screens using mock JSON | 27 Oct |
| Member 3: Backend | FastAPI skeleton, mock endpoints, validated response models | 27 Oct |
| Member 4: Scientific Data | Mock records, processing functions, comparison prototype, tests | 27 Oct |
| Member 5: Humna, Research/RAG | Source register, research notes, evidence-linked response format | 27 Oct |
| Member 6: Computer Vision | Image-processing prototype, module interface, limitations note | 27 Oct |

## C. Integration Tests

- [ ] Backend returns an experiment list in the agreed format.
- [ ] Frontend displays experiment records from the API or the agreed mock JSON.
- [ ] Experiment details load using a valid experiment ID.
- [ ] Invalid IDs produce a structured error.
- [ ] Comparison requests identify missing or incompatible measurements.
- [ ] AI insight responses include evidence references or disclose missing evidence.
- [ ] Image-analysis outputs identify their method and limitations.
- [ ] All mock results are visibly labeled as illustrative.
- [ ] The team demonstrates one complete user journey.

## D. Daily Coordination

**24 October:** Review architecture, draft schema, and confirm responsibilities.

**25 October:** Members implement their components against the draft contract.

**26 October:** Exchange sample JSON, test module interfaces, and fix mismatches.

**27 October:** Integrate the minimum working prototype, review evidence traceability, and freeze Draft v0.1.

**28 October:** Inspect the official NASA resources, map the real fields, and revise the contract where necessary.

## E. Definition of Done

A component is complete when its owner provides:

1. Working code or a usable prototype.
2. The agreed input/output interface.
3. At least one example input and output.
4. Basic tests or a manual verification procedure.
5. Known limitations and any outstanding dependencies.

**Integration priority:** Experiment exploration → experiment details → valid comparison → evidence-backed AI insight.

# Ngabo — Judge-Facing Architecture Diagram

**Status:** Required submission artifact; target architecture until deployment freeze  
**Date:** 2026-08-16

This diagram is intentionally optimized for the hackathon judge: it shows autonomous execution, Google technology usage, Clean Architecture boundaries, state ownership, safety policy, action and acknowledgement without exposing implementation noise.

> Before submission, update labels/optional model nodes to match the **actually deployed** `v0.1.0` release and export a high-resolution image if Devpost rendering requires one.

```mermaid
flowchart TB
    DATA[Synthetic WHONET-style AMR data] --> INGEST[Deterministic validation + normalization]
    INGEST --> DETECT[Deterministic surveillance detector]
    DETECT -->|surveillance.signal.detected| PS[Google Cloud Pub/Sub]

    subgraph GCP[Google Cloud]
      PS --> CORE[Cloud Run · ngabo-core]
      WEB[Cloud Run · ngabo-web]
      FS[(Firestore\nCanonical incident/workflow truth)]
      GCS[(Cloud Storage\nRaw files + artifacts)]
      LOG[Cloud Logging / Trace\nSafe execution telemetry]
    end

    USER[Browser / Judge] --> WEB
    WEB -->|HTTP/SSE| CORE

    subgraph CLEAN[ngabo-core · Clean Architecture]
      direction TB

      subgraph OUTER[Infrastructure / Interface Adapters]
        EVT[Pub/Sub event adapter]
        ADK[Google ADK runtime]
        GEM[Gemini 3.6 Flash]
        EVID[Evidence adapter\nEmbeddingGemma if implemented]
        NOTIFY[NotificationPort adapter]
      end

      subgraph APP[Application / Use Cases / Ports]
        FLOW[Incident workflow]
        CTX[Incident context query]
        ACTION[Autonomous action policy]
        FRESH[Pre-action freshness check]
        IDEM[Idempotency / delivery policy]
      end

      subgraph DOMAIN[Domain / Deterministic Scientific Core]
        PROFILE[Resistance-profile comparison]
        BASE[Baseline summary]
        MISS[Missing-field assessment]
        VALID[Package + claim validation]
        STATE[Incident state policy]
      end

      EVT --> FLOW
      ADK --> CTX
      CTX --> PROFILE
      CTX --> BASE
      CTX --> MISS
      PROFILE --> JOIN[Parallel join]
      BASE --> JOIN
      MISS --> JOIN
      JOIN --> TRIAGE[Gemini bounded triage]
      GEM --> TRIAGE
      TRIAGE --> EVID
      EVID --> SYNTH[Gemini evidence-grounded synthesis]
      GEM --> SYNTH
      SYNTH --> VALID
      VALID -->|valid| ACTION
      VALID -->|invalid| REPAIR[Bounded automatic repair]
      REPAIR --> SYNTH
      ACTION -->|A1 safe autonomous coordination| FRESH
      ACTION -->|A2/A3 blocked| ABSTAIN[Autonomous abstention / policy blocked]
      FRESH --> IDEM
      IDEM --> NOTIFY
    end

    CORE <--> FS
    CORE <--> GCS
    CORE --> LOG

    NOTIFY --> EXT[Authorized external test/sandbox endpoint]
    EXT -->|machine acknowledgement callback/event| CORE

    ACTION -. policy boundary .-> SAFETY[No prescribing · no diagnosis · no autonomous outbreak confirmation]

    style SAFETY stroke-dasharray: 5 5
```

## Hero Taskmaster Path

The canonical filmed path is:

```text
signal
→ Pub/Sub
→ ADK graph
→ deterministic fan-out/join
→ Gemini bounded reasoning
→ approved evidence
→ validated package
→ A1 autonomous action policy
→ freshness
→ idempotency
→ real external action
→ automated acknowledgement
```

Required hero counters:

```text
manual prompts:       0
human interventions: 0
clarifications:       0
approval clicks:      0
```

## Safety Boundary

The diagram deliberately separates **autonomous coordination** from **clinical/official public-health authority**.

A1 safe coordination actions can execute autonomously only after deterministic validation/policy/freshness/idempotency gates. A2/A3 action classes are blocked from the zero-human v0.1 lane.

## Google Technology Proof

The final version must truthfully show only technologies that actually execute in the submitted release:

- Gemini 3.6 Flash;
- Google ADK Python;
- Cloud Run;
- Firestore;
- Pub/Sub;
- Cloud Storage;
- Cloud Logging/Trace;
- EmbeddingGemma only if successfully integrated and evaluated;
- MedGemma only if successfully integrated and evaluated.

## Final Export Checklist

- [ ] diagram matches deployed source code;
- [ ] optional models removed if not implemented;
- [ ] Cloud Run service names match deployment;
- [ ] action/ack endpoint shown accurately;
- [ ] human/clinical safety boundary understandable in <10 seconds;
- [ ] autonomous hero path visually obvious;
- [ ] readable at 1080p video resolution;
- [ ] exported image committed/linked if needed for Devpost.

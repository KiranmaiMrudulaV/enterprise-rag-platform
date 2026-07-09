# Problem Framing
**Phase:** 01 — Discovery  
**Status:** Approved  

---

## The Problem

Company knowledge is siloed in documents that no one can find fast enough.

An engineer oncall at 2am cannot locate the payment service runbook buried in Confluence.  
A new hire reads 40 pages of onboarding docs to find the answer to one question about PTO.  
A PM opening an old product spec has no way to search across all specs for a past decision.  
An HR manager answers the same benefits questions 10 times a week because no one reads the handbook.

The documents exist. The answers are in them. The problem is access — slow, manual, unscalable.

---

## What We Are Building

An internal knowledge assistant that lets any company employee ask a question in plain English
and receive a direct answer, grounded in company documents, with exact source citations.

The system ingests company documents (PDFs, DOCX, runbooks, policies, specs).  
When an employee asks a question, the system finds the relevant passages, sends them to an LLM,
and returns an answer with clickable references to the source document and page number.

---

## Users

| User | Primary Need | Key Documents |
|------|-------------|---------------|
| **Engineers** | Query runbooks and deployment guides during incidents — fast, no browsing | Runbooks, incident reports, architecture decision records, deployment guides |
| **HR / People Ops** | Deflect repetitive policy questions to the system | PTO policy, remote work policy, benefits guide, performance review process |
| **Product Managers** | Search past product decisions and specs without opening 20 files | Product specs, feature design docs, roadmap, A/B test results |
| **New hires** | Navigate onboarding without pinging a senior engineer for every question | Onboarding guide, team wiki, company handbook, tool access docs |

---

## User Stories

### Engineers
- As an **oncall engineer**, I want to ask "how do I roll back the payment service?" and get step-by-step instructions with the runbook page cited, so I resolve incidents faster without hunting through Confluence at 2am.
- As an **engineer onboarding to a new service**, I want to ask "what does the notification service own?" and get an answer from the architecture docs, so I don't interrupt the owning team.

### HR / People Ops
- As an **HR manager**, I want employees to ask PTO and benefits questions to the system, so I stop answering the same 10 questions every week.
- As an **employee**, I want to ask "can I work remotely from another country?" and get the exact policy with the relevant section cited, so I know the rule without filing an HR ticket.

### Product Managers
- As a **PM**, I want to search "what did we decide about dark mode?" across all product specs, so I find past decisions without scrolling through old Slack threads or Notion pages.
- As a **PM**, I want to ask "what are the open risks in Project Alpha?" across Jira exports and project reports, so I have a current risk picture before a stakeholder meeting.

### New Hires
- As a **new hire**, I want to ask "how do I get access to the production database?" and receive step-by-step instructions from the onboarding doc, so I'm unblocked without interrupting a senior engineer.

---

## What Happens When the System Doesn't Know

**Decision:** Return the closest related documents with a low-confidence disclaimer.

When no retrieved chunk scores above the confidence threshold, the system responds:

> "I couldn't find a direct answer to this in the available documents. Here are the most related sections I found — they may help:"
> — followed by the top 3 closest chunks with their source documents.

**Why this over "I don't know":** An employee who gets pointed toward the right document, even without a direct answer, is better served than one who gets a dead end. The system remains useful even at the edges of its knowledge.

**Why not answer from general LLM knowledge:** For HR policy and runbook queries, a hallucinated answer is worse than no answer. An engineer following incorrect deployment steps can cause an incident. Trust requires grounding.

---

## Core Design Constraint — Coverage is Primary

**The most important quality of this system is that it finds answers that exist.**

If a policy is in the documents and the system fails to retrieve it, the system has failed — regardless of how fast it responded or how well-formatted the answer was.

This constraint drives specific technical decisions:
- **Retrieval recall is the #1 metric** (not answer quality, not latency — recall first)
- **Hybrid search (semantic + keyword) in V2** — pure semantic search misses exact-term queries like policy numbers, service names, and jargon
- **Chunk overlap is non-negotiable** — losing information at chunk boundaries directly hurts recall
- **Evaluation runs measure context recall first** before measuring faithfulness or relevancy

---

## Out of Scope for V1

- Real-time document sync (Confluence, SharePoint) — V3
- Slack bot interface — V3
- Multi-language support
- Voice interface
- Image or table understanding in PDFs (text only for V1)

---

## Success Metrics

Defined before any code is written. Evaluated after V1 ships.

| Metric | Target | How Measured |
|--------|--------|-------------|
| Context Recall (RAGAS) | > 0.70 | Automated eval on golden dataset |
| Faithfulness (RAGAS) | > 0.80 | Automated eval on golden dataset |
| Answer Relevancy (RAGAS) | > 0.75 | Automated eval on golden dataset |
| Query latency (p95) | < 2 seconds | Logged in search_history.latency_ms |
| User thumbs-up rate | > 70% | Logged in search_history.feedback |
| Hallucination rate | < 5% | Faithfulness score proxy |
| Cost per query | < $0.02 | Logged in search_history.token_count |

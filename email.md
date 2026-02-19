

**Subject: RE: Microsoft Solutions Directory (MSD) — AI Chat Apps updated & Ready for Testing & Feedback**

Hi Will,

Great question — please share the following with the director.

**Short answer: Yes, the app handles new or updated resources gracefully. No redeployment is needed.**

Here's the technical rationale:

**1. Dynamic NL2SQL — no pre-built or cached queries**
The app generates SQL queries dynamically at runtime using AI. When a user asks a question, Agent 2 (the SQL Executor) reasons over the live database schema and constructs the query on the fly. New solutions added to the database are immediately available in the next query — nothing in the app needs to change.

**2. Schema-aware generation**
The NL2SQL agent is provided the database schema as context at query time. It queries the production view (`dbo.vw_ISDSolution_All`), which aggregates all solution data. As long as the view is updated (new rows, updated records), the AI automatically incorporates them. Adding new columns would require a one-line prompt update — not a code deployment.

**3. Built-in SQL validation and retry logic**
The pipeline validates generated SQL before execution and retries automatically on syntax errors. It also enforces **read-only** access with four validation layers, so no query — regardless of how it's phrased — can modify the underlying data.

**4. Stateless, containerized pipeline**
The four-agent pipeline runs in Azure Container Apps and holds no local cache of solution data. Each request queries the live database fresh. Updating records in the source has zero impact on the running app.

**5. Conversation memory is query-scoped, not data-scoped**
The app does maintain short-term conversation memory (last 10 turns) for follow-up questions, but this stores user intent and result summaries — not raw solution data. A new question always triggers a fresh database query.

**The one scenario that would need attention:**
A **structural schema change** — such as renaming or dropping a key column in the database view — would require updating the schema context passed to the SQL agent. That's a configuration-level change, not a code rewrite, and it would produce an obvious, immediately visible error rather than a silent failure.

Happy to jump on a call if the director wants a deeper walkthrough of the architecture.

Thanks,
Arturo
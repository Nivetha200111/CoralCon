# CoralCon Architecture

## Pipeline

```
User -> CLI / Web Dashboard
     -> CoralCon Orchestrator
        -> Recon Agent
           -> Coral SQL Layer
              -> GitHub (repos, events, profile)
              -> Notion (applications, status, skills)
              -> LinkedIn (GDPR export: skills, positions, headline)
        -> Analyst Agent
           -> Deterministic rule-based insights
           -> Optional Claude API narrative analysis
        -> Dashboard Agent
           -> Notion dashboard writes (optional)
        -> Action Agent
           -> Prioritized Notion tasks (optional)
```

## Data Flow

1. **Recon Agent** executes Coral SQL queries to collect raw data from all sources.
   Every query is logged with source tables, row count, execution time, and cache status.

2. **Analyst Agent** processes the raw data through deterministic rules to generate
   evidence-backed insights. Each insight includes the query ID, supporting numbers,
   and confidence score. Optionally, Claude API adds narrative analysis.

3. **Dashboard Agent** writes structured results to a Notion page (when configured).

4. **Action Agent** creates prioritized tasks in a Notion database (when configured).

## Key Design Decisions

- **Coral SQL is the only data access path.** The agent never calls GitHub, Notion,
  or LinkedIn APIs directly. This ensures all data retrieval is logged and auditable.

- **Deterministic first, LLM second.** All core insights use rule-based analysis.
  Claude API narrative is optional and never generates numbers — those come from queries.

- **Evidence-backed insights.** Every claim includes the query ID, source tables,
  row count, and supporting numbers. No insight without evidence.

- **Sample fallback.** Deterministic sample mode uses seeded JSON data for reproducible
  judging. Same pipeline, same output format, no credentials needed.

- **Local-first privacy.** Raw data stays on the machine. LLM analysis sends only
  summarized results.

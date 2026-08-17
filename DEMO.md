# Demo Script

A guided walkthrough of the PE Partners LP Intelligence Platform.

---

## 1. Customers Tab

**URL:** `/#/customers`

This is the landing page showing the investor (Limited Partner) overview.

**Key talking points:**
- Total AUM commitment across all LPs
- Active vs total investor count
- Filter by Investor Type (Sovereign Wealth Fund, Pension Fund, etc.), Region, or Status
- Click column headers to sort
- Data is served from Snowflake Interactive Tables for sub-second response times

**Demo action:** Filter by "Sovereign Wealth Fund" to show the largest institutional investors.

---

## 2. Financial Tab

**URL:** `/#/financial`

Fund-level financial dashboard with AUM breakdown and portfolio positions.

**Key talking points:**
- Horizontal bar chart shows AUM by fund, color-coded by strategy
- Click any fund bar to drill into sector allocation and position weights
- Long/Short breakdown by sector (green = long, red = short)
- Position weight curve shows portfolio concentration

**Demo action:** Click "PE Partners AI Growth Fund" to see its sector allocation and top positions.

---

## 3. LP Reporting Tab

**URL:** `/#/reporting`

Automated LP report generation with email delivery and scheduling.

**Key talking points:**
- Select a fund to view its monthly returns and ROIC comparison
- Generate a professional PDF report with one click
- Email reports directly to LPs from the platform
- Schedule recurring reports (daily/weekly/monthly) — creates a Snowflake Task behind the scenes

**Demo action:**
1. Fund defaults to "PE Partners AI Growth Fund"
2. Click "Download PDF" to generate and view the report
3. Show the scheduling panel — explain this creates a Snowflake CRON task

---

## 4. Document Search Tab

**URL:** `/#/search`

Cortex Search over SEC filings with AI-powered analysis.

**Key talking points:**
- Semantic search across filing documents (10-K, 10-Q, S-1, etc.)
- Pre-computed AI summaries and sentiment analysis per filing
- Full-text view with positive/negative keyword highlighting
- Powered by Cortex Search Service for fast vector retrieval

**Demo action:**
1. The search defaults to "Funding round" — results show relevant filing excerpts
2. In the company browser (defaults to OpenAI), select a filing to view its AI summary
3. Expand the full text to show keyword highlighting (green = positive, red = negative signals)

---

## 5. Call Analytics Tab

**URL:** `/#/call-analytics`

Earnings call transcript analysis with video playback.

**Key talking points:**
- Company selector with call count badges
- Sentiment scoring (0-100 scale) per call
- Full transcript with positive keyword highlighting
- Embedded video player for recorded calls
- AI-generated call summaries

**Demo action:**
1. OpenAI is pre-selected — calls load automatically
2. Select any call to see the sentiment score, summary, and transcript
3. Play the embedded video recording
4. Point out highlighted positive keywords in the transcript

---

## 6. Agent Tab

**URL:** `/#/agent`

Conversational AI assistant with live portfolio data context.

**Key talking points:**
- Powered by Cortex Complete (LLM inference in Snowflake)
- Model selector (GPT-5.2, o3, o4-mini, etc.)
- Context includes live fund, investor, position, and performance data
- Answers questions with exact numbers from the portfolio

**Demo action:** Ask questions like:
- "What is our total AUM across all funds?"
- "Who are our top 3 investors by commitment?"
- "Which fund has the best YTD performance?"
- "What sectors are we most exposed to?"

---

## Architecture Highlights (for technical audiences)

1. **Single-container deployment** — Nginx + FastAPI managed by Supervisord
2. **SPCS OAuth** — Zero-credential authentication; token auto-injected at `/snowflake/session/token`
3. **Interactive Tables** — Sub-second query latency for the serving layer
4. **Cortex Search** — Vector search over chunked documents without managing embeddings
5. **Cortex Complete** — LLM inference with structured data context, no data leaves Snowflake
6. **Snowflake Tasks** — Report scheduling creates real CRON tasks in the account
7. **CI/CD** — GitHub Actions builds and pushes to Snowflake image registry on every merge

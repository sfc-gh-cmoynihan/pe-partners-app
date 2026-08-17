# PE Partners - LP Intelligence Platform

A full-stack investment intelligence application for Private Equity fund management, deployed on Snowpark Container Services (SPCS). Built with FastAPI, AngularJS, and Snowflake Cortex AI.

## Features

- **Customer Overview** — LP investor tracking with AUM commitments, regions, and risk profiles
- **Financial Dashboard** — Fund AUM visualization, sector allocation, and position weights
- **LP Reporting** — Automated PDF report generation with email delivery and scheduling via Snowflake Tasks
- **Document Search** — Cortex Search over SEC filings with AI-powered sentiment analysis and summarization
- **Call Analytics** — Earnings call transcripts with video playback, sentiment scoring, and keyword highlighting
- **AI Agent** — Conversational assistant powered by Cortex Complete with live portfolio data context

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Snowpark Container Services          │
│                                                   │
│  ┌───────────┐     ┌────────────────────────┐   │
│  │   Nginx   │────▶│   FastAPI (Python)      │   │
│  │  (8080)   │     │   - REST API            │   │
│  │  Static   │     │   - Snowflake Connector │   │
│  │  Frontend │     │   - PDF Generation      │   │
│  └───────────┘     └────────────┬───────────┘   │
│                                  │               │
└──────────────────────────────────┼───────────────┘
                                   │ SPCS OAuth
                                   ▼
┌─────────────────────────────────────────────────┐
│                  Snowflake                        │
│                                                   │
│  • Interactive Tables (real-time serving)         │
│  • Cortex Search Services (document retrieval)   │
│  • Cortex Complete (LLM inference)               │
│  • Snowflake Tasks (scheduled reports)           │
│  • Internal Stages (video/file storage)          │
└─────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | AngularJS 1.x, Chart.js |
| Backend | Python 3.13, FastAPI, Uvicorn |
| Process Manager | Supervisord (nginx + uvicorn) |
| Container | Docker on SPCS |
| Database | Snowflake (Interactive Tables) |
| AI/ML | Cortex Search, Cortex Complete |
| Reports | ReportLab + Matplotlib |

## Quick Start

1. Run `setup/01_ddl.sql` in your Snowflake account to create all objects
2. Run `setup/02_data.sql` to load sample data
3. Build and push the Docker image (see below)
4. Run `setup/03_deploy_service.sql` to create the SPCS service

See [INSTALL.md](INSTALL.md) for detailed setup instructions.

See [DEMO.md](DEMO.md) for a guided walkthrough of the application.

## Project Structure

```
spcs-app/
├── Dockerfile
├── nginx.conf
├── supervisord.conf
├── backend/
│   ├── main.py          # FastAPI routes
│   ├── db.py            # Snowflake connection (SPCS OAuth / PAT)
│   ├── report.py        # PDF report generation
│   └── requirements.txt
└── frontend/src/
    ├── index.html
    ├── app.js           # AngularJS app + routing
    ├── styles.css
    ├── controllers/     # One controller per page
    ├── views/           # HTML templates
    └── lib/             # Vendored JS libraries

setup/
├── 01_ddl.sql           # Database, tables, interactive tables
├── 02_data.sql          # Sample data (funds, investors, positions)
└── 03_deploy_service.sql # SPCS service creation
```

## CI/CD

The included GitHub Actions workflow (`.github/workflows/build-push.yml`) automatically builds and pushes the Docker image to the Snowflake image registry on every push to `main` that modifies `spcs-app/`.

## License

MIT

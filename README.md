# THE MOON
### Microgravity Observation & Orbital Network

**NASA Space Apps Challenge 2026 | Multan, Pakistan**

THE MOON is an AI-powered scientific intelligence platform developed for NASA Space Apps Challenge 2026 challenge **"Flame in Freefall: AI-Powered Fire Safety Insights from Microgravity Combustion Data."**

The platform explores microgravity combustion experiments, analyzes available experimental measurements, compares normal and inverse flame behavior, and provides research-based insights relevant to spacecraft fire safety.

Our goal is to make scientific combustion data easier to explore, understand, compare, and interpret for future space exploration missions.

---

## Project Objectives

- Explore NASA-related microgravity combustion experiment data.
- Analyze normal and inverse flame experiment records.
- Compare available combustion measurements.
- Provide interactive scientific data visualizations.
- Integrate AI-powered research assistance using Retrieval-Augmented Generation (RAG).
- Present evidence-linked insights with clear data limitations.
- Support research into fire safety considerations for future Moon and Mars missions.

---

## Key Features

### 1. Scientific Dashboard
An interactive web dashboard providing an overview of available experiments, measurements, and analysis results.

### 2. Experiment Explorer
Explore available experiment records, including:

- PSI-159 Normal Flame Experiments
- PSI-159 Inverse Flame Experiments

### 3. Experiment Details
View experiment metadata, available measurements, source information, and data limitations.

### 4. Normal vs. Inverse Flame Comparison
Compare available experimental measurements and explore differences between normal and inverse flame records.

### 5. AI Research Assistant
An AI-powered research interface designed to retrieve relevant scientific information and provide evidence-linked answers.

### 6. Data Quality and Transparency
The system communicates data availability, validation status, and known limitations to avoid presenting uncertain information as established scientific findings.

---

## System Architecture

```text
                 USER
                   |
                   v
          REACT WEB DASHBOARD
                   |
                   v
             FASTAPI BACKEND
                   |
          +--------+--------+
          |                 |
          v                 v
    EXPERIMENT DATA     ANALYSIS ENGINE
          |                 |
          v                 v
     PSI-159 CSV       STATISTICAL
       RECORDS          ANALYSIS
          |                 |
          +--------+--------+
                   |
                   v
             DATA INSIGHTS
                   |
                   v
          DASHBOARD VISUALIZATION


          AI RESEARCH ASSISTANT
                   |
                   v
              RAG MODULE
                   |
                   v
          SCIENTIFIC KNOWLEDGE
                   |
                   v
          EVIDENCE-LINKED ANSWERS
```

---

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| UI and Icons | CSS, Lucide React |
| Data Visualization | Recharts |
| Backend | Python, FastAPI |
| API Models | Pydantic |
| Data Processing | Python, CSV |
| AI Research | Retrieval-Augmented Generation (RAG) |
| API Communication | REST API |
| Development | Git, GitHub, VS Code |

---

## Experimental Data

The current data integration includes processed PSI-159 experiment records for:

**Normal Flame**
- Experiment ID: `PSI159-CFIG-NORMAL`
- Source ID: `PSI159-NORMAL-CSV`

**Inverse Flame**
- Experiment ID: `PSI159-CFIG-INVERSE`
- Source ID: `PSI159-INVERSE-CSV`

Investigation: Cool Flames Investigation with Gases (CFI-G)

Program: Advanced Combustion via Microgravity Experiments (ACME)

Platform: International Space Station (ISS)

Available measurement categories include:

- Adiabatic flame temperature
- Burn time
- Fuel fraction
- Hydrocarbon mass flow
- Oxygen fraction
- Peak burner temperature
- Pressure
- Stoichiometric mixture fraction

The available measurement fields differ between experiment types.

**Data Status:** The currently integrated PSI-159 records are marked `unverified` by the project's data adapter. They are locally processed CSV records and have not been independently re-verified by this adapter.

ISS microgravity experiments are not direct simulations of lunar or Martian environments. Any application to future Moon or Mars missions must be treated as research interpretation rather than direct experimental proof.

---

## Project Structure

```text
THE_MOON_CORE/
│
├── app/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── adapters/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   │
│   └── tests/
│
├── data-anlysis/
│   └── data/
│       └── processed/
│           ├── normal_analysis.csv
│           └── inverse_analysis.csv
│
└── tests/
```

The frontend is maintained separately in the `the-MOON--frontend` repository.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js and npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Younushk123/the-MOON-.git
```

Navigate to the core project directory:

```bash
cd the-MOON-/THE_MOON_CORE
```

### 2. Configure the Backend

Navigate to the backend:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the data mode in the backend `.env` file:

```env
MOON_DATA_MODE=psi
```

### 3. Start the Backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend API:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

### 4. Configure the Frontend

Clone the frontend repository separately:

```bash
git clone https://github.com/Younushk123/the-MOON--frontend.git
```

Navigate into it:

```bash
cd the-MOON--frontend
```

Install dependencies:

```bash
npm install
```

Create `.env.local`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_USE_MOCK_DATA=false
VITE_API_TIMEOUT_MS=15000
VITE_ENABLE_VISION=false
```

### 5. Start the Frontend

```bash
npm run dev
```

Open the local Vite URL shown in the terminal, usually:

`http://localhost:5173`

Make sure the backend is running before using the dashboard.

---

## API Overview

The main backend exposes versioned REST API endpoints.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/experiments` | List experiments |
| GET | `/api/v1/experiments/{experiment_id}` | Experiment details |
| GET | `/api/v1/experiments/{experiment_id}/measurements` | Experiment measurements |
| POST | `/api/v1/analysis` | Run experiment analysis |
| POST | `/api/v1/comparison` | Compare experiments |
| POST | `/api/v1/insights` | Generate insights |
| POST | `/api/v1/assistant/ask` | Ask the research assistant |
| POST | `/api/v1/vision/analyze` | Optional image analysis |

For complete request and response schemas, visit the interactive API documentation at `/docs`.

---

## Scientific Integrity and Limitations

THE MOON is a research-support platform, not a certified spacecraft fire-safety system.

Important limitations:

- Integrated PSI-159 CSV records are currently marked unverified.
- Measurements must be interpreted according to their available units, definitions, and experimental conditions.
- Normal and inverse flame records may contain different measurement fields.
- Only compatible measurements should be compared.
- AI-generated explanations must be interpreted alongside their supporting evidence.
- ISS microgravity observations should not be treated as direct representations of Moon or Mars surface conditions.
- Image-analysis features should only be used when suitable source imagery and validation are available.

The project aims to communicate scientific uncertainty transparently rather than make unsupported conclusions.

---

## Team

**Team Name:** THE MOON

**Event:** NASA Space Apps Challenge 2026

**Location:** Multan, Pakistan

Our multidisciplinary team works across project coordination, frontend development, backend engineering, scientific data analysis, AI research, and computer vision.

---

## Future Development

Potential future improvements include:

- Additional verified NASA experimental datasets.
- Improved scientific data validation and unit handling.
- More advanced combustion analysis.
- Enhanced evidence retrieval and research assistance.
- Better visualization of experimental trends.
- Further investigation of spacecraft fire-safety implications.
- Validated image-based flame analysis where suitable imagery is available.

---

## Acknowledgment

Developed as part of the **NASA Space Apps Challenge 2026**, inspired by the challenge:

*Flame in Freefall: AI-Powered Fire Safety Insights from Microgravity Combustion Data.*

**THE MOON — Exploring combustion science for safer future space exploration.**

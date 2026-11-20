# THE MOON 🌕

### Microgravity Observation & Orbital Network

**AI-Powered Scientific Intelligence for Microgravity Combustion Research**

**Live demo:**  https://the-moon-frontend-younus11.vercel.app

---

## About the Project

**THE MOON (Microgravity Observation & Orbital Network)** is an AI-powered scientific web dashboard developed for the **NASA Space Apps Challenge 2026 – Local Event, Multan, Pakistan**.

Our project addresses the official challenge:

**"Flame in Freefall: AI-Powered Fire Safety Insights from Microgravity Combustion Data."**

THE MOON aims to make NASA's microgravity combustion research more accessible through an interactive scientific intelligence platform. It brings together combustion experiment information, available research datasets, scientific analysis, and AI-powered evidence retrieval to help users explore how combustion behaves in microgravity.

The platform focuses on understanding the implications of microgravity combustion research for fire safety in spacecraft and future Moon and Mars habitats.

## Project Objectives

- Explore NASA's microgravity combustion experiments and research resources.
- Organize experimental information and available scientific datasets.
- Analyze and visualize available combustion measurements.
- Compare experiments where their data and conditions are compatible.
- Retrieve relevant scientific evidence through an AI-powered research assistant.
- Present research-based insights while identifying data limitations and uncertainties.

## Key Modules

| Module | Description |
|---|---|
| **Experiment Explorer** | Explore NASA combustion experiments and their available research information. |
| **Scientific Data Analysis** | Process, analyze, and visualize available experimental datasets. |
| **Experiment Comparison** | Compare compatible experiments and scientific measurements. |
| **AI Research Assistant (RAG)** | Retrieve relevant information from indexed NASA research materials with supporting evidence. |
| **Computer Vision** | Explore flame-related images and videos through image and video processing. |
| **Scientific Insights** | Present research-based findings and their relevance to spacecraft fire safety. |

## Technology Stack

- **Frontend:** React, TypeScript, Vite
- **Backend:** Python, FastAPI, Pydantic
- **Data Analysis:** Python and scientific data processing
- **Research Assistant:** Retrieval-Augmented Generation (RAG)
- **Computer Vision:** Python, image and video processing
- **Data & Schemas:** JSON, JSON Schema
- **Testing:** Pytest, Python unittest

## Repository Structure

```text
the-moon/
├── README.md
├── PROJECT_CONTRACT.md
├── CONTRIBUTING.md
├── .env.example
├── docs/
├── frontend/
├── backend/
├── data_analysis/
├── research_rag/
├── computer_vision/
├── shared/
│   ├── schemas/
│   └── sample_data/
└── .github/workflows/tests.yml
```

### Module Overview

- `frontend/`: React, TypeScript, and Vite-based dashboard.
- `backend/`: FastAPI REST API and canonical Pydantic schemas.
- `data_analysis/`: PSI-159 raw and processed combustion datasets and notebooks.
- `research_rag/`: Evidence retrieval, source register, generation, and evaluation.
- `computer_vision/`: PSI-69 FLEX image/video processing and reference outputs.
- `shared/`: Generated JSON Schemas and illustrative mock fixtures.

## Getting Started

### Prerequisites

- Python
- Node.js and npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Younushk123/the-MOON-.git
cd the-MOON-
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate the environment:

**Windows**
```bash
.venv\Scripts\activate
```

**Linux/macOS**
```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Copy `.env.example` to `.env` and configure the required environment variables.

Start the backend:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Set `MOON_DATA_MODE=mock` or `MOON_DATA_MODE=psi` according to the required data mode.

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Copy `.env.example` to `.env.local` and configure the required environment variables.

Start the development server:

```bash
npm run dev
```

### 4. Research Assistant (RAG)

From the repository root:

```bash
python research_rag/rag_pipeline.py ask "Why is combustion different in microgravity?"
```

Set `GROQ_API_KEY` only when using Groq-based generation. Otherwise, extraction-only mode is used.

### 5. Computer Vision

Run the unit tests:

```bash
python -m unittest discover -s computer_vision/tests -v
```

Process an image:

```bash
python -m computer_vision --image /path/to/still.jpg --output computer_vision/outputs/generated
```

Source FLEX MP4/JPG media are intentionally not redistributed. The backend supports uploads and temporary processing. Supported source profiles are documented in `computer_vision/README.md`.

## Validation & Testing

Run the following checks from the repository root:

**Backend**
```bash
cd backend
python -m pytest -q
```

**Research RAG**
```bash
cd research_rag
python -m pytest -q
```

**Computer Vision**
```bash
python -m unittest discover -s computer_vision/tests -v
```

**Frontend**
```bash
cd frontend
npm run build
```

## NASA Data & Research

THE MOON uses NASA's Physical Sciences Informatics (PSI) resources and related combustion science research materials as its scientific foundation.

Primary NASA resources:

- [NASA Physical Sciences Informatics (PSI)](https://psi.nasa.gov/)
- [NASA Combustion Science](https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/)
- [NASA Research on Combustion and Fire Safety](https://www.nasa.gov/missions/station/iss-research/studying-combustion-and-fire-safety/)
- [NASA Technical Reports Server (NTRS)](https://ntrs.nasa.gov/)

Specific dataset and research references are documented within the relevant project modules.

## Scientific Limitations

Scientific accuracy and transparency are important principles of THE MOON.

- PSI-159 data status is unverified unless independently validated.
- PSI-69 FLEX measurements are pixel-based and do not represent calibrated physical dimensions.
- RAG responses remain evidence-linked and may abstain when available sources do not provide sufficient support.
- ISS microgravity observations should not be interpreted as direct simulations of Moon or Mars surface conditions.
- Illustrative mock data must be distinguished from actual NASA experimental measurements.

THE MOON is a scientific research and exploration platform, not a certified spacecraft fire detection or fire suppression system.

## Project Team

**Team THE MOON**

- **Younus Hassan Khan** – Project Lead & AI/ML Integration Lead
- **Hammad Shafique** – Dashboard Development & Data Visualization
- **Sameer Ahmad** – Backend Architecture & API Development
- **Haram Abbas** – NASA Data Processing & Scientific Analysis
- **Humna Fahad** – NASA Research & RAG Development
- **Muhammad Ahsan** – Computer Vision Development

## Hackathon Information

| Detail | Information |
|---|---|
| Event | NASA Space Apps Challenge 2026 |
| Local Event | Multan, Pakistan |
| Challenge | Flame in Freefall: AI-Powered Fire Safety Insights from Microgravity Combustion Data |
| Project | THE MOON |
| Focus Areas | Artificial Intelligence, Scientific Research & Space Exploration |

---

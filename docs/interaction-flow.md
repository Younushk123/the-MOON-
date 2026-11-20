# Interaction Flow

1. The user opens the dashboard and the backend loads either mock or PSI data.
2. Experiment Explorer shows the canonical experiment list.
3. Experiment Details show metadata, measurements, sources, and limitations.
4. Comparison and analysis pages use structured PSI-159 measurements.
5. AI Insights sends questions to the RAG module. Answers must remain evidence-linked or abstain.
6. Microgravity Flame Explorer accepts a supported FLEX still image or MP4.
7. Image results are returned directly. Video uploads return a job ID and are polled until completion.
8. PSI-69 video and image results remain separate from PSI-159 experiment records.

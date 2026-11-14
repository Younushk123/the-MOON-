"""Where teammates' modules plug into the backend.

To connect a real module, implement its Protocol and return it from build_integrations().
"""

from dataclasses import dataclass

from app.config import Settings
from app.integrations.analysis import AnalysisEngine, ReferenceAnalysisEngine
from app.integrations.insights import (
    InsightEngine,
    ResearchAssistant,
    UnavailableInsightEngine,
    UnavailableResearchAssistant,
)
from app.integrations.vision import UnavailableVisionAnalyzer, VisionAnalyzer


@dataclass(frozen=True)
class Integrations:
    analysis: AnalysisEngine
    insights: InsightEngine
    assistant: ResearchAssistant
    vision: VisionAnalyzer


def build_integrations(settings: Settings) -> Integrations:
    return Integrations(
        analysis=ReferenceAnalysisEngine(),
        insights=UnavailableInsightEngine(),
        assistant=UnavailableResearchAssistant(),
        vision=UnavailableVisionAnalyzer(),
    )

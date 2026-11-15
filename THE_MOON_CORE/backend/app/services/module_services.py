"""Services that resolve experiments, then hand off to a teammate's module (or its placeholder)."""

from app.config import DataMode
from app.errors import MediaExperimentMismatchError
from app.integrations.analysis import AnalysisEngine
from app.integrations.insights import InsightEngine, ResearchAssistant
from app.integrations.vision import VisionAnalyzer, not_processed
from app.models.analysis import AnalysisRequest, AnalysisResult, Comparison, ComparisonRequest
from app.models.insight import AskRequest, Insight, InsightRequest
from app.models.vision import CVResult, VisionRequest
from app.services.experiment_service import ExperimentService


class _ModuleService:
    def __init__(self, experiments: ExperimentService) -> None:
        self.experiments = experiments

    @property
    def data_mode(self) -> DataMode:
        return self.experiments.data_mode


class AnalysisService(_ModuleService):
    def __init__(self, experiments: ExperimentService, engine: AnalysisEngine) -> None:
        super().__init__(experiments)
        self.engine = engine

    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        experiment = self.experiments.get_experiment(request.experiment_id)
        measurements = self.experiments.all_measurements(experiment.experiment_id)
        return self.engine.analyze(experiment, measurements, request.analysis_type, request.variables)

    def compare(self, request: ComparisonRequest) -> Comparison:
        experiments = self.experiments.get_experiments(request.experiment_ids)
        measurements = {e.experiment_id: self.experiments.all_measurements(e.experiment_id) for e in experiments}
        return self.engine.compare(experiments, measurements, request.variables)


class InsightService(_ModuleService):
    def __init__(self, experiments: ExperimentService, insights: InsightEngine, assistant: ResearchAssistant) -> None:
        super().__init__(experiments)
        self.insights = insights
        self.assistant = assistant

    def generate(self, request: InsightRequest) -> Insight:
        experiments = self.experiments.get_experiments(request.experiment_ids)
        return self.insights.generate(request.question, experiments)

    def ask(self, request: AskRequest) -> Insight:
        return self.assistant.ask(request.question)


class VisionService(_ModuleService):
    def __init__(self, experiments: ExperimentService, analyzer: VisionAnalyzer) -> None:
        super().__init__(experiments)
        self.analyzer = analyzer

    def analyze(self, request: VisionRequest) -> CVResult:
        """Check the media belongs to the experiment and has a file before the CV module sees it."""
        experiment = self.experiments.get_experiment(request.experiment_id)
        media = self.experiments.get_media(request.media_id)
        if media.experiment_id != experiment.experiment_id:
            raise MediaExperimentMismatchError(media.media_id, experiment.experiment_id, media.experiment_id)
        if media.availability_status != "available":
            reason = f"Media '{media.media_id}' is {media.availability_status}. No file was analysed."
            return not_processed(experiment, media, reason)
        return self.analyzer.analyze(experiment, media)

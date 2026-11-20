"""Services that resolve experiments, then hand off to a teammate's module (or its placeholder)."""

from pathlib import Path

from app.config import DataMode
from app.integrations.analysis import AnalysisEngine
from app.integrations.insights import InsightEngine, ResearchAssistant
from app.integrations.vision import VisionAnalyzer
from app.models.analysis import AnalysisRequest, AnalysisResult, Comparison, ComparisonRequest
from app.models.insight import AskRequest, Insight, InsightRequest
from app.models.vision import CVAnalysisJob, CVResult, VisionRequest
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
        return self.assistant.ask(
            request.question,
            request.experiment_ids,
            request.validated_findings,
            request.top_k,
        )


class VisionService(_ModuleService):
    def __init__(self, experiments: ExperimentService, analyzer: VisionAnalyzer) -> None:
        super().__init__(experiments)
        self.analyzer = analyzer

    def analyze(self, request: VisionRequest) -> CVResult:
        experiment = self.experiments.get_experiment(request.experiment_id)
        return self.analyzer.analyze(experiment, request.media_id)

    def analyze_uploaded_image(self, media_id: str, image_path: Path) -> CVResult:
        return self.analyzer.analyze_uploaded_image(media_id, image_path)

    def submit_video(self, media_id: str, video_path: Path, upload_directory: Path) -> CVAnalysisJob:
        return self.analyzer.submit_video(media_id, video_path, upload_directory)

    def get_video_job(self, job_id: str) -> CVAnalysisJob:
        return self.analyzer.get_video_job(job_id)

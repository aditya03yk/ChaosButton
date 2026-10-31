"""Importing the package registers every table with SQLModel metadata."""
from app.models.analysis import AIAnalysis  # noqa: F401
from app.models.events import RequestEvent, TimelineEvent  # noqa: F401
from app.models.experiment import Experiment  # noqa: F401
from app.models.fixes import FixRecord  # noqa: F401
from app.models.metrics import ExperimentMetrics  # noqa: F401
from app.models.target import Target  # noqa: F401

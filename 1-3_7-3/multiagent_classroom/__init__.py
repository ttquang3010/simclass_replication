"""
Multi-Agent Classroom Simulation Package

A modular system for simulating classroom teaching scenarios with AI agents
based on COPUS (Classroom Observation Protocol for Undergraduate STEM).
"""

__version__ = "1.0.0"
__author__ = "ttquang3010"

from .api_client import APIClient
from .agent import SimpleAgent
from .observer import COPUSObserver
from .scenarios import ScenarioExecutor
from .evaluator import TeachingEvaluator
from .data_loader import DataLoader
from .result_saver import ResultSaver

__all__ = [
    "APIClient",
    "SimpleAgent",
    "COPUSObserver",
    "ScenarioExecutor",
    "TeachingEvaluator",
    "DataLoader",
    "ResultSaver",
]

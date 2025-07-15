"""
Cohort-Based Planogram System

This module provides a dedicated system for generating cohort-based planograms
that show LOB-accessory relationships based on customer purchase behavior.

Key Components:
- CohortDataLoader: Loads and processes corrected cohort data
- CohortPlanogramBase: Base class for cohort planogram generation
- iPhone/iPad/Mac/Watch/AirPods specific cohort planogram generators
- CohortPlanogramRunner: Main entry point for cohort planogram generation

Usage:
    from src.cohort_planogram.runner import CohortPlanogramRunner
    
    runner = CohortPlanogramRunner()
    runner.generate_cohort_planogram('iPhone', 'flagship')
"""

from .runner import CohortPlanogramRunner
from .iphone_cohort import iPhoneCohortPlanogram
from .data_loader import CohortDataLoader

__all__ = ['CohortPlanogramRunner', 'iPhoneCohortPlanogram', 'CohortDataLoader']

"""
Cohort-based planogram generation system

This package provides cohort-based planogram generation for different LOBs,
showing relationships between core products and their accessories based on
customer purchase behavior and attach rates.
"""

from .runner import CohortPlanogramRunner
from .base import CohortPlanogramBase, StoreTemplateLoader
from .data_loader import CohortDataLoader
from .iphone_cohort import iPhoneCohortPlanogram
from .ipad_cohort import iPadCohortPlanogram
from .mac_cohort import MacCohortPlanogram
from .watch_cohort import WatchCohortPlanogram

__all__ = [
    'CohortPlanogramRunner',
    'CohortPlanogramBase',
    'StoreTemplateLoader', 
    'CohortDataLoader',
    'iPhoneCohortPlanogram',
    'iPadCohortPlanogram',
    'MacCohortPlanogram',
    'WatchCohortPlanogram'
]

__version__ = '1.0.0'
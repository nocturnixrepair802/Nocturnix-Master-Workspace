"""
============================================================
Nocturnix Repair Platform
Training Video Repository
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Status:
    Placeholder

Purpose:
    Repository responsible for training videos and
    instructional media used throughout the platform.

Planned Features:
    • Video catalog
    • YouTube links
    • Internal training
    • OEM training
    • Vendor certification videos
    • Difficulty levels

============================================================
"""

from repositories.repository_base import RepositoryBase


class TrainingVideoRepository(RepositoryBase):

    def __init__(self, database):

        super().__init__(database, "training_videos")

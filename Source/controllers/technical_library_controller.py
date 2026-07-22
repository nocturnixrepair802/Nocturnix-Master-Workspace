"""
============================================================
Nocturnix Business Portal
Technical Library Controller
============================================================

Author: Nocturnix Mobile Repair
Version: 1.0.0 Alpha

Purpose:
    Controller for the Technical Knowledge Module.

============================================================
"""

from typing import Optional, cast

import pandas as pd

from core.base_controller import BaseController
from services.technical_knowledge_service import TechnicalKnowledgeService


class TechnicalLibraryController(BaseController):
    """
    Controller responsible for coordinating
    Technical Knowledge operations between the
    GUI and the Service layer.
    """

    def __init__(
        self,
        service: TechnicalKnowledgeService,
    ):

        super().__init__(service)

    # ======================================================
    # Service
    # ======================================================

    @property
    def technical_service(self) -> TechnicalKnowledgeService:

        return cast(TechnicalKnowledgeService, self.service)

    # ======================================================
    # Collections
    # ======================================================

    def get_all_guides(self) -> pd.DataFrame:
        """
        Returns all repair guides.
        """

        return self.technical_service.all()

    # ======================================================
    # Single Record
    # ======================================================

    def get_guide(
        self,
        guide_id: str,
    ) -> Optional[pd.Series]:
        """
        Returns a repair guide by Guide ID.
        """

        return self.technical_service.get_guide(guide_id)

    # ======================================================
    # Validation
    # ======================================================

    def guide_exists(
        self,
        guide_id: str,
    ) -> bool:
        """
        Determines whether a guide exists.
        """

        return self.technical_service.exists(guide_id)

    # ======================================================
    # Search
    # ======================================================

    def search_guides(
        self,
        text: str = "",
    ) -> pd.DataFrame:
        """
        Searches repair guides.
        """

        return self.technical_service.search(text)

    # ======================================================
    # Filters
    # ======================================================

    def guides_by_device(
        self,
        device_id: str,
    ) -> pd.DataFrame:

        return self.technical_service.guides_by_device(device_id)

    def guides_by_service(
        self,
        service_id: str,
    ) -> pd.DataFrame:

        return self.technical_service.guides_by_service(service_id)

    def guides_by_category(
        self,
        category_id: str,
    ) -> pd.DataFrame:

        return self.technical_service.guides_by_category(category_id)

    def guides_by_source(
        self,
        source_id: str,
    ) -> pd.DataFrame:

        return self.technical_service.guides_by_source(source_id)

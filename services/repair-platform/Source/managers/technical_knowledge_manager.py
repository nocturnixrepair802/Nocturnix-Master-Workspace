"""
============================================================
Nocturnix Business Portal
Technical Knowledge Manager
============================================================
"""
import pandas as pd

from services.technical_knowledge_service import (
    TechnicalKnowledgeService,
)


class TechnicalKnowledgeManager:

    def __init__(
        self,
        service: TechnicalKnowledgeService,
    ):

        self.service = service

    # ======================================================
    # Collections
    # ======================================================

    def all(self) -> pd.DataFrame:

        return self.service.all()

    # ======================================================
    # Search
    # ======================================================

    def search(self, text: str = "") -> pd.DataFrame:

        return self.service.search(text)

    # ======================================================
    # Filters
    # ======================================================

    def by_device(self, device_id):

        return self.service.guides_by_device(device_id)

    def by_service(self, service_id):

        return self.service.guides_by_service(service_id)

    def by_category(self, category_id):

        return self.service.guides_by_category(category_id)

    def by_source(self, source_id):

        return self.service.guides_by_source(source_id)

    # ======================================================
    # Single Record
    # ======================================================

    def get(self, guide_id):

        return self.service.get_guide(guide_id)

    def count(self):

        return self.service.count()


    def exists(self, guide_id):

        return self.service.exists(guide_id)

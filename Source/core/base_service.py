"""
============================================================
Nocturnix Business Portal
Base Service
============================================================

Author: Nocturnix Mobile Repair

Description:
    Base class inherited by every business service in the
    Nocturnix Business Portal.

Responsibilities:
    • Business logic
    • Validation
    • Communication with repositories
    • Common logging support
    • Future transaction handling

All business services should inherit from this class.

Example:

    class CustomerService(BaseService):
        ...

    class RepairService(BaseService):
        ...

    class TechnicalKnowledgeService(BaseService):
        ...

============================================================
"""

from abc import ABC
from typing import Any


class BaseService(ABC):
    """
    Base class for all business services.

    Services are responsible for business logic and communicate
    with repositories. They should never communicate directly
    with Excel, SQLite, or the GUI.
    """

    def __init__(self, repository: Any):
        """
        Initialize the service.

        Parameters
        ----------
        repository
            Repository used by this service.
        """
        self.repository = repository

    def initialize(self) -> None:
        """
        Called when the service is initialized.

        Override in child classes if needed.
        """
        pass

    def shutdown(self) -> None:
        """
        Called before the service is destroyed.

        Override in child classes if needed.
        """
        pass

    def validate(self, data: Any) -> bool:
        """
        Performs validation.

        Child services should override this method.

        Returns
        -------
        bool
            True if validation succeeds.
        """
        return True

    def refresh(self) -> None:
        """
        Refresh cached data.

        Child services may override this.
        """
        pass

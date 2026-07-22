from typing import Generic, TypeVar

TService = TypeVar("TService")
"""
Base class for all application controllers.

Controllers coordinate between the GUI and the
business services. They should not contain
business logic.
"""

class BaseController(Generic[TService]):

    def __init__(self, service: TService):

        self.service: TService = service

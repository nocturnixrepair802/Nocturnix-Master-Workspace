"""
============================================================
Nocturnix Business Portal
Base Model
============================================================

Author: Nocturnix Mobile Repair
Purpose:
    Base class inherited by every model in the system.

Every model receives:

• ID
• Created Date
• Modified Date
• Active Flag
• Serialization
• Dictionary Conversion
• Timestamp Management

============================================================
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class BaseModel:
    """
    Base class for all business models.
    """

    id: str = ""

    active: bool = True

    created_date: datetime = field(default_factory=datetime.now)

    modified_date: datetime = field(default_factory=datetime.now)

    def touch(self) -> None:
        """
        Updates the modified timestamp.
        """
        self.modified_date = datetime.now()

    def deactivate(self) -> None:
        """
        Marks the record inactive.
        """
        self.active = False
        self.touch()

    def activate(self) -> None:
        """
        Marks the record active.
        """
        self.active = True
        self.touch()

    def to_dict(self) -> dict[str, Any]:
        """
        Converts model to dictionary.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        """
        Creates object from dictionary.
        """
        return cls(**data)

from config.database import MASTER_DATABASE
from managers.repair_manager import RepairManager
from managers.repository_manager import RepositoryManager
from managers.service_manager import ServiceManager
from managers.technical_knowledge_manager import TechnicalKnowledgeManager
from managers.workflow_manager import WorkflowManager
from services.table_loader import TableLoader


class Application:
    """Root dependency container for the Nocturnix Repair Platform."""

    def __init__(self) -> None:
        print()
        print("=" * 70)
        print("Initializing Nocturnix Repair Platform")
        print("=" * 70)

        loader = TableLoader(MASTER_DATABASE)

        self.database = loader.load_all_tables()

        self.repositories = RepositoryManager(self.database)

        self.services = ServiceManager(self.repositories)

        self.technical = TechnicalKnowledgeManager(self.services.technical)

        self.repair = RepairManager(
            self.database,
            self.repositories,
        )

        self.workflow = WorkflowManager(self.repair)

        print()
        print("Application Ready")
        print("=" * 70)

from config.database import MASTER_DATABASE

from services.table_loader import TableLoader

from managers.repository_manager import RepositoryManager
from managers.service_manager import ServiceManager
from managers.repair_manager import RepairManager
from managers.workflow_manager import WorkflowManager
from managers.technical_knowledge_manager import TechnicalKnowledgeManager


class Application:
    """
    Root dependency container for the Nocturnix Repair Platform.
    """

    def __init__(self):

        print()
        print("=" * 70)
        print("Initializing Nocturnix Repair Platform")
        print("=" * 70)

        loader = TableLoader(MASTER_DATABASE)

        self.database: dict = loader.load_all_tables()

        self.repositories: RepositoryManager = RepositoryManager(
            self.database
        )

        self.services: ServiceManager = ServiceManager(
            self.repositories
        )

        self.technical: TechnicalKnowledgeManager = (
            TechnicalKnowledgeManager(self.services.technical)
        )

        self.repair: RepairManager = RepairManager(
            self.database
        )

        self.workflow: WorkflowManager = WorkflowManager(
            self.repair
        )

        print()
        print("Application Ready")
        print("=" * 70)

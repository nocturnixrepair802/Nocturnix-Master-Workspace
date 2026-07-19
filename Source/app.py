from config.database import MASTER_DATABASE

from services.table_loader import TableLoader

from managers.repository_manager import RepositoryManager
from managers.service_manager import ServiceManager
from managers.repair_manager import RepairManager
from managers.workflow_manager import WorkflowManager


class Application:

    def __init__(self):

        print()
        print("=" * 70)
        print("Initializing Nocturnix Repair Platform")
        print("=" * 70)

        loader = TableLoader(MASTER_DATABASE)

        self.database = loader.load_all_tables()

        # Repository Layer
        self.repositories = RepositoryManager(
            self.database
        )

        # Service Layer
        self.services = ServiceManager(
            self.repositories
        )

        # Business Logic Layer
        self.repair = RepairManager(
            self.database
        )

        # Workflow Layer
        self.workflow = WorkflowManager(
            self.repair
        )

        print()
        print("Application Ready")
        print("=" * 70)
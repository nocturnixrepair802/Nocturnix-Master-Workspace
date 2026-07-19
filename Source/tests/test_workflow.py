from config.database import MASTER_DATABASE

from services.table_loader import TableLoader

from managers.repair_manager import RepairManager
from managers.workflow_manager import WorkflowManager


print("=" * 70)
print("WORKFLOW TEST")
print("=" * 70)

loader = TableLoader(MASTER_DATABASE)

database = loader.load_all_tables()

repair = RepairManager(database)

workflow = WorkflowManager(repair)

print()

print("Workflow Objects")

print(workflow.repair)

print(workflow.estimate)

print(workflow.invoice)
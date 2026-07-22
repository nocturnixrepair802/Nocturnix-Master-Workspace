from app import Application
from config.database import MASTER_DATABASE
from controllers.application_controller import ApplicationController
from validators.database_validator import DatabaseValidator
from validators.relationship_validator import RelationshipValidator
from validators.workbook_validator import WorkbookValidator


def main():

    print("=" * 70)
    print("Nocturnix Repair Platform")
    print("=" * 70)

    workbook = WorkbookValidator(MASTER_DATABASE)

    if not workbook.validate():
        return

    application = Application()

    DatabaseValidator(
        application.database
    ).validate()

    RelationshipValidator(
        application.database
    ).validate()

    controller = ApplicationController(application)

    controller.run()


if __name__ == "__main__":
    main()
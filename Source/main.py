from config.database import MASTER_DATABASE

from validators.workbook_validator import WorkbookValidator
from validators.database_validator import DatabaseValidator
from validators.relationship_validator import RelationshipValidator

from app import Application
from controllers.application_controller import ApplicationController


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
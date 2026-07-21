import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT))

from app import Application
from seeders.seeder_manager import SeederManager

def main():

    app = Application()

    SeederManager(app.database).run()


if __name__ == "__main__":

    main()

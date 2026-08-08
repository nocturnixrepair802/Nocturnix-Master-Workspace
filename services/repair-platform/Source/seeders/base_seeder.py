class BaseSeeder:

    def __init__(self, application):

        self.application = application

    # ======================================================
    # Interface
    # ======================================================

    def seed(self):

        raise NotImplementedError("Seeder must implement seed().")

    # ======================================================
    # Utility
    # ======================================================

    def message(self, text):

        print(f"[Seeder] {text}")

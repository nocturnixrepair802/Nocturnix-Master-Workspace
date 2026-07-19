from legacy_ui.dashboard import Dashboard
from legacy_ui.customer_menu import CustomerMenu

from controllers.customer_controller import CustomerController


class ApplicationController:

    def __init__(self, application):

        self.app = application

        self.dashboard = Dashboard()

        self.customer_menu = CustomerMenu()

        self.customer_controller = CustomerController(

            application.services

        )

    def customer_loop(self):

        while True:

            choice = self.customer_menu.show()

            if choice == "1":

                self.customer_controller.list_customers()

            elif choice == "2":

                self.customer_controller.search_customer()

            elif choice == "6":

                self.customer_controller.customer_count()

            elif choice == "7":

                return

            else:

                print("\nComing Soon...")

        input("\nPress ENTER...")

    def run(self):

        while True:

            choice = self.dashboard.show()

            if choice == "1":

                self.customer_loop()

            elif choice == "7":

                print("\nGoodbye.")

                return

            else:

                print("\nComing Soon...")

                input("\nPress ENTER...")
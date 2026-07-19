class Customer:

    def __init__(

        self,

        customer_id,

        first_name,

        last_name,

        business_name,

        email,

        mobile_phone,

        preferred_contact,

        active=True

    ):

        self.customer_id = customer_id

        self.first_name = first_name

        self.last_name = last_name

        self.business_name = business_name

        self.email = email

        self.mobile_phone = mobile_phone

        self.preferred_contact = preferred_contact

        self.active = active

    @property
    def full_name(self):

        return f"{self.first_name} {self.last_name}"

    def __str__(self):

        return self.full_name
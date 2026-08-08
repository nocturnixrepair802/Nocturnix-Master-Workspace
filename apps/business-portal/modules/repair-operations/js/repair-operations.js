/*
=========================================================
Nocturnix Business Portal

Repair Operations Module
=========================================================
*/

const REPAIR_API_BASE =
  `${window.location.protocol}//${window.location.hostname}:8000`;


function initializeRepairOperations() {
  const workspace = document.querySelector(
    ".workspace"
  );

  if (!workspace) {
    return;
  }

  const form = workspace.querySelector(
    ".repair-form"
  );

  if (!form) {
    return;
  }

  if (form.dataset.initialized === "true") {
    return;
  }

  form.dataset.initialized = "true";

  prepareRepairForm(form);

  form.addEventListener(
    "submit",
    handleRepairSubmit
  );

  console.log(
    "Nocturnix Repair Operations initialized."
  );
}


function prepareRepairForm(form) {
  const groups =
    form.querySelectorAll(
      ".form-group"
    );

  groups.forEach((group) => {
    const label = group
      .querySelector("label")
      ?.textContent
      ?.trim();

    const control = group.querySelector(
      "input, select, textarea"
    );

    if (!label || !control) {
      return;
    }

    const fieldName =
      fieldNameForLabel(label);

    if (fieldName) {
      control.name = fieldName;
    }
  });

  const submitButton =
    form.querySelector(
      ".save-button"
    );

  if (submitButton) {
    submitButton.type = "submit";
  }
}


function fieldNameForLabel(label) {
  const fields = {
    "Customer Name":
      "customer_name",

    "Phone Number":
      "mobile_phone",

    "Email":
      "email",

    "Manufacturer":
      "manufacturer",

    "Model":
      "model",

    "IMEI / Serial Number":
      "serial_number",

    "Repair Status":
      "repair_status",

    "Estimated Cost":
      "estimated_cost",

    "Problem Description":
      "problem_description",

    "Technician Notes":
      "technician_notes",
  };

  return fields[label] || "";
}


async function handleRepairSubmit(event) {
  event.preventDefault();

  const form = event.currentTarget;

  const submitButton =
    form.querySelector(
      ".save-button"
    );

  setSubmitState(
    submitButton,
    true
  );

  clearRepairMessage(form);

  try {
    const values =
      readRepairForm(form);

    validateRepairForm(values);

    const customer =
      await createCustomer(values);

    const device =
      await createDevice(
        customer.id,
        values
      );

    const repair =
      await createRepair(
        customer.id,
        device.id,
        values
      );

    showRepairSuccess(
      form,
      repair
    );

    form.reset();

    console.log(
      "Repair intake created:",
      {
        customer,
        device,
        repair,
      }
    );
  } catch (error) {
    console.error(
      "Repair intake failed:",
      error
    );

    showRepairError(
      form,
      error
    );
  } finally {
    setSubmitState(
      submitButton,
      false
    );
  }
}


function readRepairForm(form) {
  const formData =
    new FormData(form);

  const customerName =
    String(
      formData.get(
        "customer_name"
      ) || ""
    ).trim();

  const nameParts =
    splitCustomerName(
      customerName
    );

  const estimatedCostRaw =
    String(
      formData.get(
        "estimated_cost"
      ) || ""
    ).trim();

  return {
    customer_name:
      customerName,

    first_name:
      nameParts.firstName,

    last_name:
      nameParts.lastName,

    mobile_phone:
      String(
        formData.get(
          "mobile_phone"
        ) || ""
      ).trim(),

    email:
      String(
        formData.get(
          "email"
        ) || ""
      ).trim(),

    manufacturer:
      String(
        formData.get(
          "manufacturer"
        ) || ""
      ).trim(),

    model:
      String(
        formData.get(
          "model"
        ) || ""
      ).trim(),

    serial_number:
      String(
        formData.get(
          "serial_number"
        ) || ""
      ).trim(),

    repair_status:
      String(
        formData.get(
          "repair_status"
        ) || "New Intake"
      ).trim(),

    estimated_cost:
      estimatedCostRaw
        ? Number(
            estimatedCostRaw
          )
        : null,

    problem_description:
      String(
        formData.get(
          "problem_description"
        ) || ""
      ).trim(),

    technician_notes:
      String(
        formData.get(
          "technician_notes"
        ) || ""
      ).trim(),
  };
}


function splitCustomerName(
  customerName
) {
  const parts =
    customerName
      .trim()
      .split(/\s+/)
      .filter(Boolean);

  if (parts.length === 0) {
    return {
      firstName: "",
      lastName: "",
    };
  }

  if (parts.length === 1) {
    return {
      firstName: parts[0],
      lastName: "",
    };
  }

  return {
    firstName: parts[0],
    lastName:
      parts
        .slice(1)
        .join(" "),
  };
}


function validateRepairForm(values) {
  if (!values.customer_name) {
    throw new Error(
      "Customer name is required."
    );
  }

  if (!values.manufacturer) {
    throw new Error(
      "Manufacturer is required."
    );
  }

  if (!values.model) {
    throw new Error(
      "Device model is required."
    );
  }

  if (
    !values.problem_description
  ) {
    throw new Error(
      "Problem description is required."
    );
  }

  if (
    values.estimated_cost !== null
    && (
      Number.isNaN(
        values.estimated_cost
      )
      || values.estimated_cost < 0
    )
  ) {
    throw new Error(
      "Estimated cost must be zero or greater."
    );
  }
}


async function createCustomer(values) {
  return apiRequest(
    "/api/customers",
    {
      method: "POST",

      body: {
        first_name:
          values.first_name,

        last_name:
          values.last_name,

        business_name: "",

        email:
          values.email,

        mobile_phone:
          values.mobile_phone,

        customer_type:
          "Individual",

        notes:
          "Created through Business Portal repair intake.",
      },
    }
  );
}


async function createDevice(
  customerId,
  values
) {
  return apiRequest(
    "/api/devices",
    {
      method: "POST",

      body: {
        customer_id:
          customerId,

        manufacturer:
          values.manufacturer,

        model:
          values.model,

        serial_number:
          values.serial_number,

        device_type:
          "Mobile Device",

        notes:
          "Created through Business Portal repair intake.",
      },
    }
  );
}


async function createRepair(
  customerId,
  deviceId,
  values
) {
  return apiRequest(
    "/api/repairs",
    {
      method: "POST",

      body: {
        customer_id:
          customerId,

        device_id:
          deviceId,

        repair_status:
          values.repair_status,

        problem_description:
          values.problem_description,

        technician_notes:
          values.technician_notes,

        estimated_cost:
          values.estimated_cost,
      },
    }
  );
}


async function apiRequest(
  path,
  options = {}
) {
  const response =
    await fetch(
      `${REPAIR_API_BASE}${path}`,
      {
        method:
          options.method || "GET",

        headers: {
          "Content-Type":
            "application/json",
        },

        body:
          options.body
            ? JSON.stringify(
                options.body
              )
            : undefined,
      }
    );

  const contentType =
    response.headers.get(
      "content-type"
    ) || "";

  let payload = null;

  if (
    contentType.includes(
      "application/json"
    )
  ) {
    payload =
      await response.json();
  } else {
    payload =
      await response.text();
  }

  if (!response.ok) {
    let message =
      `Request failed with status ${response.status}.`;

    if (
      payload
      && typeof payload === "object"
      && payload.detail
    ) {
      message =
        String(
          payload.detail
        );
    }

    throw new Error(
      message
    );
  }

  return payload;
}


function setSubmitState(
  button,
  submitting
) {
  if (!button) {
    return;
  }

  button.disabled =
    submitting;

  button.textContent =
    submitting
      ? "Saving Repair..."
      : "Save Repair";
}


function clearRepairMessage(form) {
  form
    .querySelector(
      ".repair-form-message"
    )
    ?.remove();
}


function showRepairSuccess(
  form,
  repair
) {
  const message =
    document.createElement(
      "div"
    );

  message.className =
    "repair-form-message repair-form-success";

  message.innerHTML = `
    <strong>
      Repair created successfully.
    </strong>

    <div>
      Ticket ID:
      ${escapeHtml(
        String(
          repair.id
        )
      )}
    </div>
  `;

  form.prepend(
    message
  );
}


function showRepairError(
  form,
  error
) {
  const message =
    document.createElement(
      "div"
    );

  message.className =
    "repair-form-message repair-form-error";

  const errorMessage =
    error instanceof Error
      ? error.message
      : String(error);

  message.textContent =
    `Unable to save repair: ${errorMessage}`;

  form.prepend(
    message
  );
}


function escapeHtml(value) {
  return String(value)
    .replaceAll(
      "&",
      "&amp;"
    )
    .replaceAll(
      "<",
      "&lt;"
    )
    .replaceAll(
      ">",
      "&gt;"
    )
    .replaceAll(
      '"',
      "&quot;"
    )
    .replaceAll(
      "'",
      "&#039;"
    );
}


document.addEventListener(
  "nocturnix:module-loaded",
  (event) => {
    if (
      event.detail?.path
      === "/repairs"
    ) {
      initializeRepairOperations();
    }
  }
);
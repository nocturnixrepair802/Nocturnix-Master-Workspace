/*
=========================================================
Nocturnix Business Portal
Repair Operations
=========================================================
*/

const REPAIR_API_BASE =
  `${window.location.protocol}//${window.location.hostname}:8000`;

let customerSearchTimer = null;
let repairQueueRecords = [];


/*
=========================================================
Initialization
=========================================================
*/

async function initializeRepairOperations() {
  const workspace =
    document.querySelector(
      ".workspace"
    );

  if (!workspace) {
    return;
  }

  const form =
    workspace.querySelector(
      "#repairIntakeForm"
    );

  if (!form) {
    return;
  }

  if (
    form.dataset.initialized
    === "true"
  ) {
    return;
  }

  form.dataset.initialized =
    "true";

  /*
  =======================================================
  Initialize Feature Groups
  =======================================================
  */

  initializeCustomerSearch(
    form
  );

  initializeExistingDeviceControls(
    form
  );

  initializeCatalogListeners(
    form
  );

  /*
  =======================================================
  Repair Queue Filters
  =======================================================
  */

  initializeRepairQueueFilters(
    form
  );

  /*
  =======================================================
  Existing Form Listeners
  =======================================================
  */

  form.addEventListener(
    "submit",
    handleRepairSubmit
  );

  form.addEventListener(
    "reset",
    () => {
      window.setTimeout(
        () => {
          resetCustomerSelection(
            form
          );

          resetExistingDeviceSelection(
            form
          );

          resetCatalogSelections(
            form
          );

          hideExistingCustomerDeviceSection(
            form
          );

          showNewDeviceMode(
            form
          );

          closeRepairDetails(
            form
          );
        },
        0
      );
    }
  );

  const saveDetailsButton =
    form.querySelector(
      "#saveRepairDetailsButton"
    );

  const closeDetailsButton =
    form.querySelector(
      "#closeRepairDetailsButton"
    );

  saveDetailsButton?.addEventListener(
    "click",
    async () => {
      try {
        await saveRepairDetails(
          form
        );
      } catch (error) {
        console.error(
          "Unable to save repair details:",
          error
        );

        showRepairError(
          form,
          error
        );
      }
    }
  );

  closeDetailsButton?.addEventListener(
    "click",
    () => {
      closeRepairDetails(
        form
      );
    }
  );

  /*
  =======================================================
  Initial API Loads
  =======================================================
  */

  try {
    await loadManufacturers(
      form
    );

    await loadRepairQueue(
      form
    );

    console.log(
      "Repair Operations initialized."
    );
  } catch (error) {
    console.error(
      "Repair Operations initialization failed:",
      error
    );

    showRepairError(
      form,
      error
    );
  }
}


/*
=========================================================
Customer Search
=========================================================
*/

function initializeCustomerSearch(
  form
) {
  const searchInput =
    form.querySelector(
      "#repairCustomerSearch"
    );

  const clearButton =
    form.querySelector(
      "#clearSelectedCustomer"
    );

  searchInput?.addEventListener(
    "input",
    () => {
      scheduleCustomerSearch(
        form
      );
    }
  );

  searchInput?.addEventListener(
    "focus",
    () => {
      if (
        searchInput.value
          .trim()
          .length >= 2
      ) {
        scheduleCustomerSearch(
          form,
          0
        );
      }
    }
  );

  clearButton?.addEventListener(
    "click",
    () => {
      resetCustomerSelection(
        form,
        {
          clearFields: true,
        }
      );

      resetExistingDeviceSelection(
        form
      );

      hideExistingCustomerDeviceSection(
        form
      );

      showNewDeviceMode(
        form
      );

      resetCatalogSelections(
        form
      );

      searchInput?.focus();
    }
  );
}


function scheduleCustomerSearch(
  form,
  delay = 300
) {
  if (customerSearchTimer) {
    window.clearTimeout(
      customerSearchTimer
    );
  }

  customerSearchTimer =
    window.setTimeout(
      async () => {
        try {
          await searchCustomers(
            form
          );
        } catch (error) {
          console.error(
            "Customer search failed:",
            error
          );
        }
      },
      delay
    );
}


async function searchCustomers(
  form
) {
  const input =
    form.querySelector(
      "#repairCustomerSearch"
    );

  const results =
    form.querySelector(
      "#repairCustomerResults"
    );

  if (
    !input
    || !results
  ) {
    return;
  }

  const query =
    input.value.trim();

  if (
    query.length < 2
  ) {
    results.hidden =
      true;

    results.innerHTML =
      "";

    return;
  }

  results.hidden =
    false;

  results.innerHTML = `
    <div class="customer-search-message">
      Searching customers...
    </div>
  `;

  const customers =
    await apiRequest(
      `/api/customers?q=${
        encodeURIComponent(
          query
        )
      }`
    );

  renderCustomerResults(
    form,
    customers
  );
}


function renderCustomerResults(
  form,
  customers
) {
  const results =
    form.querySelector(
      "#repairCustomerResults"
    );

  if (!results) {
    return;
  }

  results.innerHTML =
    "";

  if (
    !Array.isArray(
      customers
    )
    || customers.length === 0
  ) {
    results.hidden =
      false;

    results.innerHTML = `
      <div class="customer-search-message">
        No existing customers found.
      </div>
    `;

    return;
  }

  for (
    const customer
    of customers
  ) {
    const button =
      document.createElement(
        "button"
      );

    button.type =
      "button";

    button.className =
      "customer-search-result";

    const displayName =
      getCustomerDisplayName(
        customer
      );

    const contact =
      [
        customer.mobile_phone,
        customer.email,
      ]
        .filter(Boolean)
        .join(" • ");

    button.innerHTML = `
      <strong>
        ${escapeHtml(
          displayName
        )}
      </strong>

      <span>
        ${escapeHtml(
          contact
        )}
      </span>

      <small>
        ${escapeHtml(
          customer.id
        )}
      </small>
    `;

    button.addEventListener(
      "click",
      async () => {
        try {
          await selectExistingCustomer(
            form,
            customer
          );
        } catch (error) {
          showRepairError(
            form,
            error
          );
        }
      }
    );

    results.appendChild(
      button
    );
  }

  results.hidden =
    false;
}


function getCustomerDisplayName(
  customer
) {
  if (
    customer.business_name
  ) {
    return customer.business_name;
  }

  const name =
    [
      customer.first_name,
      customer.last_name,
    ]
      .filter(Boolean)
      .join(" ")
      .trim();

  return (
    name
    || customer.id
    || "Customer"
  );
}


async function selectExistingCustomer(
  form,
  customer
) {
  const selectedId =
    form.querySelector(
      "#repairSelectedCustomerId"
    );

  const nameInput =
    form.querySelector(
      "#repairCustomerName"
    );

  const phoneInput =
    form.querySelector(
      "#repairPhone"
    );

  const emailInput =
    form.querySelector(
      "#repairEmail"
    );

  const searchInput =
    form.querySelector(
      "#repairCustomerSearch"
    );

  if (selectedId) {
    selectedId.value =
      customer.id || "";
  }

  if (nameInput) {
    nameInput.value =
      getCustomerDisplayName(
        customer
      );
  }

  if (phoneInput) {
    phoneInput.value =
      customer.mobile_phone
      || "";
  }

  if (emailInput) {
    emailInput.value =
      customer.email
      || "";
  }

  if (searchInput) {
    searchInput.value =
      getCustomerDisplayName(
        customer
      );
  }

  showSelectedCustomer(
    form,
    customer
  );

  hideCustomerResults(
    form
  );

  resetExistingDeviceSelection(
    form
  );

  await loadExistingCustomerDevices(
    form,
    customer.id
  );
}


function showSelectedCustomer(
  form,
  customer
) {
  const panel =
    form.querySelector(
      "#selectedCustomerPanel"
    );

  if (!panel) {
    return;
  }

  const name =
    panel.querySelector(
      "#selectedCustomerName"
    );

  const contact =
    panel.querySelector(
      "#selectedCustomerContact"
    );

  const id =
    panel.querySelector(
      "#selectedCustomerId"
    );

  if (name) {
    name.textContent =
      getCustomerDisplayName(
        customer
      );
  }

  if (contact) {
    contact.textContent =
      [
        customer.mobile_phone,
        customer.email,
      ]
        .filter(Boolean)
        .join(" • ");
  }

  if (id) {
    id.textContent =
      `Customer ID: ${customer.id}`;
  }

  panel.hidden =
    false;
}


function resetCustomerSelection(
  form,
  options = {}
) {
  const selectedId =
    form.querySelector(
      "#repairSelectedCustomerId"
    );

  const panel =
    form.querySelector(
      "#selectedCustomerPanel"
    );

  const results =
    form.querySelector(
      "#repairCustomerResults"
    );

  if (selectedId) {
    selectedId.value =
      "";
  }

  if (panel) {
    panel.hidden =
      true;
  }

  if (results) {
    results.hidden =
      true;

    results.innerHTML =
      "";
  }

  if (
    options.clearFields
    === true
  ) {
    const selectors = [
      "#repairCustomerSearch",
      "#repairCustomerName",
      "#repairPhone",
      "#repairEmail",
    ];

    for (
      const selector
      of selectors
    ) {
      const input =
        form.querySelector(
          selector
        );

      if (input) {
        input.value =
          "";
      }
    }
  }
}


function hideCustomerResults(
  form
) {
  const results =
    form.querySelector(
      "#repairCustomerResults"
    );

  if (results) {
    results.hidden =
      true;
  }
}


/*
=========================================================
Existing Customer Device
=========================================================
*/

function initializeExistingDeviceControls(
  form
) {
  const select =
    form.querySelector(
      "#existingCustomerDevice"
    );

  const useButton =
    form.querySelector(
      "#useExistingDeviceButton"
    );

  const addButton =
    form.querySelector(
      "#addNewDeviceButton"
    );

  const clearButton =
    form.querySelector(
      "#clearExistingDeviceButton"
    );

  select?.addEventListener(
    "change",
    () => {
      if (useButton) {
        useButton.disabled =
          !select.value;
      }
    }
  );

  useButton?.addEventListener(
    "click",
    async () => {
      try {
        await selectExistingCustomerDevice(
          form
        );
      } catch (error) {
        showRepairError(
          form,
          error
        );
      }
    }
  );

  addButton?.addEventListener(
    "click",
    () => {
      resetExistingDeviceSelection(
        form
      );

      resetCatalogSelections(
        form
      );

      showNewDeviceMode(
        form
      );
    }
  );

  clearButton?.addEventListener(
    "click",
    () => {
      resetExistingDeviceSelection(
        form
      );

      resetCatalogSelections(
        form
      );

      showNewDeviceMode(
        form
      );
    }
  );
}


async function loadExistingCustomerDevices(
  form,
  customerId
) {
  const section =
    form.querySelector(
      "#existingCustomerDeviceSection"
    );

  const select =
    form.querySelector(
      "#existingCustomerDevice"
    );

  const useButton =
    form.querySelector(
      "#useExistingDeviceButton"
    );

  if (
    !section
    || !select
  ) {
    return;
  }

  section.hidden =
    false;

  select.disabled =
    true;

  select.innerHTML = `
    <option value="">
      Loading existing devices...
    </option>
  `;

  const devices =
    await apiRequest(
      `/api/customers/${
        encodeURIComponent(
          customerId
        )
      }/devices`
    );

  select.innerHTML = `
    <option value="">
      Select existing device
    </option>
  `;

  for (
    const device
    of devices
  ) {
    const option =
      document.createElement(
        "option"
      );

    option.value =
      device.id;

    option.textContent =
      [
        device.manufacturer,
        device.model,
        device.serial_number
          ? `(${device.serial_number})`
          : "",
      ]
        .filter(Boolean)
        .join(" ");

    option.dataset.catalogDeviceId =
      device.catalog_device_id
      || "";

    option.dataset.manufacturer =
      device.manufacturer
      || "";

    option.dataset.model =
      device.model
      || "";

    option.dataset.serialNumber =
      device.serial_number
      || "";

    option.dataset.deviceType =
      device.device_type
      || "";

    select.appendChild(
      option
    );
  }

  if (
    devices.length === 0
  ) {
    select.innerHTML = `
      <option value="">
        No existing devices
      </option>
    `;

    select.disabled =
      true;

    if (useButton) {
      useButton.disabled =
        true;
    }

    showNewDeviceMode(
      form
    );

    return;
  }

  select.disabled =
    false;

  if (useButton) {
    useButton.disabled =
      true;
  }
}


async function selectExistingCustomerDevice(
  form
) {
  const select =
    form.querySelector(
      "#existingCustomerDevice"
    );

  const hidden =
    form.querySelector(
      "#repairSelectedExistingDeviceId"
    );

  if (
    !select
    || !select.value
  ) {
    return;
  }

  const option =
    select.selectedOptions[0];

  if (hidden) {
    hidden.value =
      select.value;
  }

  const catalogDeviceId =
    option?.dataset
      .catalogDeviceId
    || "";

  showExistingDevicePanel(
    form,
    {
      id:
        select.value,

      catalog_device_id:
        catalogDeviceId,

      manufacturer:
        option?.dataset
          .manufacturer
        || "",

      model:
        option?.dataset
          .model
        || "",

      serial_number:
        option?.dataset
          .serialNumber
        || "",

      device_type:
        option?.dataset
          .deviceType
        || "",
    }
  );

  hideNewDeviceMode(
    form
  );

  resetServiceSelection(
    form
  );

  if (
    catalogDeviceId
  ) {
    form.dataset.catalogDeviceId =
      catalogDeviceId;

    await loadServices(
      form,
      catalogDeviceId
    );
  } else {
    showNewDeviceMode(
      form
    );

    showRepairInfo(
      form,
      (
        "This existing device is not linked "
        + "to the catalog yet. Select its "
        + "manufacturer and model."
      )
    );
  }
}


function showExistingDevicePanel(
  form,
  device
) {
  const panel =
    form.querySelector(
      "#selectedExistingDevicePanel"
    );

  if (!panel) {
    return;
  }

  const name =
    panel.querySelector(
      "#selectedExistingDeviceName"
    );

  const details =
    panel.querySelector(
      "#selectedExistingDeviceDetails"
    );

  const id =
    panel.querySelector(
      "#selectedExistingDeviceId"
    );

  if (name) {
    name.textContent =
      [
        device.manufacturer,
        device.model,
      ]
        .filter(Boolean)
        .join(" ");
  }

  if (details) {
    details.textContent =
      [
        device.serial_number
          ? `Serial / IMEI: ${device.serial_number}`
          : "",

        device.device_type
          ? `Type: ${device.device_type}`
          : "",
      ]
        .filter(Boolean)
        .join(" • ");
  }

  if (id) {
    id.textContent =
      (
        `Device ID: ${device.id}`
        + (
            device.catalog_device_id
              ? ` • Catalog: ${device.catalog_device_id}`
              : ""
          )
      );
  }

  panel.hidden =
    false;
}


function resetExistingDeviceSelection(
  form
) {
  const hidden =
    form.querySelector(
      "#repairSelectedExistingDeviceId"
    );

  const panel =
    form.querySelector(
      "#selectedExistingDevicePanel"
    );

  const select =
    form.querySelector(
      "#existingCustomerDevice"
    );

  const useButton =
    form.querySelector(
      "#useExistingDeviceButton"
    );

  if (hidden) {
    hidden.value =
      "";
  }

  if (panel) {
    panel.hidden =
      true;
  }

  if (select) {
    select.selectedIndex =
      0;
  }

  if (useButton) {
    useButton.disabled =
      true;
  }

  delete form.dataset
    .catalogDeviceId;

  resetServiceSelection(
    form
  );
}


function hideExistingCustomerDeviceSection(
  form
) {
  const section =
    form.querySelector(
      "#existingCustomerDeviceSection"
    );

  if (section) {
    section.hidden =
      true;
  }
}


function showNewDeviceMode(
  form
) {
  const section =
    form.querySelector(
      "#newDeviceSection"
    );

  if (section) {
    section.hidden =
      false;
  }

  const manufacturer =
    form.querySelector(
      "#repairManufacturer"
    );

  const device =
    form.querySelector(
      "#repairDevice"
    );

  if (manufacturer) {
    manufacturer.required =
      true;
  }

  if (device) {
    device.required =
      true;
  }
}


function hideNewDeviceMode(
  form
) {
  const section =
    form.querySelector(
      "#newDeviceSection"
    );

  if (section) {
    section.hidden =
      true;
  }

  const manufacturer =
    form.querySelector(
      "#repairManufacturer"
    );

  const device =
    form.querySelector(
      "#repairDevice"
    );

  if (manufacturer) {
    manufacturer.required =
      false;
  }

  if (device) {
    device.required =
      false;
  }
}


/*
=========================================================
Catalog
=========================================================
*/

function initializeCatalogListeners(
  form
) {
  const manufacturer =
    form.querySelector(
      "#repairManufacturer"
    );

  const device =
    form.querySelector(
      "#repairDevice"
    );

  const service =
    form.querySelector(
      "#repairService"
    );

  manufacturer?.addEventListener(
    "change",
    async () => {
      try {
        await handleManufacturerChange(
          form
        );
      } catch (error) {
        showRepairError(
          form,
          error
        );
      }
    }
  );

  device?.addEventListener(
    "change",
    async () => {
      try {
        await handleCatalogDeviceChange(
          form
        );
      } catch (error) {
        showRepairError(
          form,
          error
        );
      }
    }
  );

  service?.addEventListener(
    "change",
    async () => {
      try {
        await handleServiceChange(
          form
        );
      } catch (error) {
        showRepairError(
          form,
          error
        );
      }
    }
  );
}


async function loadManufacturers(
  form
) {
  const select =
    form.querySelector(
      "#repairManufacturer"
    );

  if (!select) {
    return;
  }

  select.disabled =
    true;

  select.innerHTML = `
    <option value="">
      Loading manufacturers...
    </option>
  `;

  const manufacturers =
    await apiRequest(
      "/api/catalog/manufacturers"
    );

  select.innerHTML = `
    <option value="">
      Select manufacturer
    </option>
  `;

  for (
    const manufacturer
    of manufacturers
  ) {
    const option =
      document.createElement(
        "option"
      );

    option.value =
      manufacturer.manufacturer_id;

    option.textContent =
      manufacturer.manufacturer;

    option.dataset.name =
      manufacturer.manufacturer;

    select.appendChild(
      option
    );
  }

  select.disabled =
    false;
}


async function handleManufacturerChange(
  form
) {
  const manufacturer =
    form.querySelector(
      "#repairManufacturer"
    );

  const device =
    form.querySelector(
      "#repairDevice"
    );

  if (
    !manufacturer
    || !device
  ) {
    return;
  }

  resetServiceSelection(
    form
  );

  delete form.dataset
    .catalogDeviceId;

  if (
    !manufacturer.value
  ) {
    device.disabled =
      true;

    device.innerHTML = `
      <option value="">
        Select manufacturer first
      </option>
    `;

    return;
  }

  await loadDevices(
    form,
    manufacturer.value
  );
}


async function loadDevices(
  form,
  manufacturerId
) {
  const select =
    form.querySelector(
      "#repairDevice"
    );

  if (!select) {
    return;
  }

  select.disabled =
    true;

  select.innerHTML = `
    <option value="">
      Loading devices...
    </option>
  `;

  const devices =
    await apiRequest(
      "/api/catalog/devices"
      + "?manufacturer_id="
      + encodeURIComponent(
          manufacturerId
        )
      + "&limit=1000"
    );

  select.innerHTML = `
    <option value="">
      Select device
    </option>
  `;

  for (
    const device
    of devices
  ) {
    const option =
      document.createElement(
        "option"
      );

    option.value =
      device.device_id;

    option.textContent =
      device.device_model;

    option.dataset.manufacturer =
      device.manufacturer
      || "";

    option.dataset.manufacturerId =
      device.manufacturer_id
      || "";

    option.dataset.model =
      device.device_model
      || "";

    option.dataset.deviceTypeId =
      device.device_type_id
      || "";

    option.dataset.deviceFamilyId =
      device.device_family_id
      || "";

    select.appendChild(
      option
    );
  }

  if (
    devices.length === 0
  ) {
    select.innerHTML = `
      <option value="">
        No devices found
      </option>
    `;

    return;
  }

  select.disabled =
    false;
}


async function handleCatalogDeviceChange(
  form
) {
  const select =
    form.querySelector(
      "#repairDevice"
    );

  if (!select) {
    return;
  }

  resetServiceSelection(
    form
  );

  if (
    !select.value
  ) {
    delete form.dataset
      .catalogDeviceId;

    return;
  }

  form.dataset.catalogDeviceId =
    select.value;

  await loadServices(
    form,
    select.value
  );
}


async function loadServices(
  form,
  deviceId
) {
  const select =
    form.querySelector(
      "#repairService"
    );

  if (!select) {
    return;
  }

  select.disabled =
    true;

  select.innerHTML = `
    <option value="">
      Loading services...
    </option>
  `;

  const services =
    await apiRequest(
      "/api/catalog/services"
      + "?device_id="
      + encodeURIComponent(
          deviceId
        )
      + "&limit=250"
    );

  select.innerHTML = `
    <option value="">
      Select service
    </option>
  `;

  for (
    const service
    of services
  ) {
    const option =
      document.createElement(
        "option"
      );

    option.value =
      service.service_id;

    option.textContent =
      service.service_name;

    option.dataset.serviceName =
      service.service_name
      || "";

    option.dataset.serviceType =
      service.service_type
      || "";

    option.dataset.serviceTypeId =
      service.service_type_id
      || "";

    select.appendChild(
      option
    );
  }

  if (
    services.length === 0
  ) {
    select.innerHTML = `
      <option value="">
        No services available
      </option>
    `;

    return;
  }

  select.disabled =
    false;
}


function resetServiceSelection(
  form
) {
  const select =
    form.querySelector(
      "#repairService"
    );

  if (select) {
    select.disabled =
      true;

    select.innerHTML = `
      <option value="">
        Select service
      </option>
    `;
  }

  clearPricing(
    form
  );
}


async function handleServiceChange(
  form
) {
  const service =
    form.querySelector(
      "#repairService"
    );

  const deviceId =
    form.dataset.catalogDeviceId;

  clearPricing(
    form
  );

  if (
    !service
    || !service.value
    || !deviceId
  ) {
    return;
  }

  const pricing =
    await apiRequest(
      "/api/catalog/pricing"
      + "?device_id="
      + encodeURIComponent(
          deviceId
        )
      + "&service_id="
      + encodeURIComponent(
          service.value
        )
      + "&limit=1"
    );

  if (
    !Array.isArray(
      pricing
    )
    || pricing.length === 0
  ) {
    return;
  }

  const record =
    pricing[0];

  form.dataset.catalogPrice =
    record.price
    ?? "";

  form.dataset.catalogPartCost =
    record.part_cost
    ?? "";

  form.dataset.catalogPricingStatus =
    record.status
    ?? "";

  showPricing(
    form,
    record
  );
}


function showPricing(
  form,
  record
) {
  const panel =
    form.querySelector(
      "#repairPricing"
    );

  const retail =
    form.querySelector(
      "#repairRetailPrice"
    );

  const partCost =
    form.querySelector(
      "#repairPartCost"
    );

  const status =
    form.querySelector(
      "#repairPricingStatus"
    );

  const notice =
    form.querySelector(
      "#repairPricingNotice"
    );

  if (retail) {
    retail.textContent =
      formatCurrency(
        record.price
      );
  }

  if (partCost) {
    partCost.textContent =
      formatCurrency(
        record.part_cost
      );
  }

  if (status) {
    status.textContent =
      record.status
      || "Unknown";
  }

  if (notice) {
    notice.textContent =
      String(
        record.status
        || ""
      ).toLowerCase()
      === "approved"
        ? "This pricing record is approved."
        : "This pricing record is not currently marked Approved.";
  }

  if (panel) {
    panel.hidden =
      false;
  }
}


function clearPricing(
  form
) {
  const panel =
    form.querySelector(
      "#repairPricing"
    );

  if (panel) {
    panel.hidden =
      true;
  }

  delete form.dataset
    .catalogPrice;

  delete form.dataset
    .catalogPartCost;

  delete form.dataset
    .catalogPricingStatus;
}


/*
=========================================================
Repair Intake
=========================================================
*/

async function handleRepairSubmit(
  event
) {
  event.preventDefault();

  const form =
    event.currentTarget;

  const submitButton =
    form.querySelector(
      "#saveRepairButton"
    );

  clearRepairMessage(
    form
  );

  setSubmitState(
    submitButton,
    true
  );

  try {
    const values =
      readRepairForm(
        form
      );

    validateRepairForm(
      values
    );

    let customer;

    if (
      values.existing_customer_id
    ) {
      customer =
        await apiRequest(
          `/api/customers/${
            encodeURIComponent(
              values.existing_customer_id
            )
          }`
        );
    } else {
      customer =
        await createCustomer(
          values
        );
    }

    let customerDevice;

    if (
      values.existing_device_id
    ) {
      customerDevice =
        await apiRequest(
          `/api/devices/${
            encodeURIComponent(
              values.existing_device_id
            )
          }`
        );
    } else {
      customerDevice =
        await createCustomerDevice(
          customer.id,
          values
        );
    }

    const repair =
      await createRepair(
        customer.id,
        customerDevice.id,
        values
      );

    showRepairSuccess(
      form,
      repair,
      customer,
      customerDevice,
      values
    );

    await loadRepairQueue(
      form
    );

    resetFormAfterSuccess(
      form
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


function readRepairForm(
  form
) {
  const data =
    new FormData(
      form
    );

  const customerName =
    String(
      data.get(
        "customer_name"
      )
      || ""
    ).trim();

  const names =
    splitCustomerName(
      customerName
    );

  const manufacturer =
    form.querySelector(
      "#repairManufacturer"
    );

  const device =
    form.querySelector(
      "#repairDevice"
    );

  const service =
    form.querySelector(
      "#repairService"
    );

  return {
    existing_customer_id:
      form.querySelector(
        "#repairSelectedCustomerId"
      )?.value
      || "",

    existing_device_id:
      form.querySelector(
        "#repairSelectedExistingDeviceId"
      )?.value
      || "",

    customer_name:
      customerName,

    first_name:
      names.firstName,

    last_name:
      names.lastName,

    mobile_phone:
      String(
        data.get(
          "mobile_phone"
        )
        || ""
      ).trim(),

    email:
      String(
        data.get(
          "email"
        )
        || ""
      ).trim(),

    manufacturer_id:
      manufacturer?.value
      || "",

    manufacturer:
      manufacturer
        ?.selectedOptions[0]
        ?.dataset.name
      || "",

    catalog_device_id:
      form.dataset
        .catalogDeviceId
      || "",

    device_model:
      device
        ?.selectedOptions[0]
        ?.dataset.model
      || "",

    device_type_id:
      device
        ?.selectedOptions[0]
        ?.dataset.deviceTypeId
      || "",

    device_family_id:
      device
        ?.selectedOptions[0]
        ?.dataset.deviceFamilyId
      || "",

    serial_number:
      String(
        data.get(
          "serial_number"
        )
        || ""
      ).trim(),

    service_id:
      service?.value
      || "",

    service_name:
      service
        ?.selectedOptions[0]
        ?.dataset.serviceName
      || "",

    repair_status:
      String(
        data.get(
          "repair_status"
        )
        || "New Intake"
      ).trim(),

    estimated_cost:
      form.dataset.catalogPrice
        ? Number(
            form.dataset
              .catalogPrice
          )
        : null,

    pricing_status:
      form.dataset
        .catalogPricingStatus
      || "",

    problem_description:
      String(
        data.get(
          "problem_description"
        )
        || ""
      ).trim(),

    technician_notes:
      String(
        data.get(
          "technician_notes"
        )
        || ""
      ).trim(),
  };
}


function validateRepairForm(
  values
) {
  if (
    !values.customer_name
    && !values.existing_customer_id
  ) {
    throw new Error(
      "Customer name is required."
    );
  }

  if (
    !values.existing_device_id
    && !values.catalog_device_id
  ) {
    throw new Error(
      "A device is required."
    );
  }

  if (
    !values.service_id
  ) {
    throw new Error(
      "Repair service is required."
    );
  }

  if (
    !values.problem_description
  ) {
    throw new Error(
      "Problem description is required."
    );
  }
}


async function createCustomer(
  values
) {
  return apiRequest(
    "/api/customers",
    {
      method:
        "POST",

      body: {
        first_name:
          values.first_name,

        last_name:
          values.last_name,

        business_name:
          "",

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


async function createCustomerDevice(
  customerId,
  values
) {
  return apiRequest(
    "/api/devices",
    {
      method:
        "POST",

      body: {
        customer_id:
          customerId,

        catalog_device_id:
          values.catalog_device_id,

        manufacturer:
          values.manufacturer,

        model:
          values.device_model,

        serial_number:
          values.serial_number,

        device_type:
          values.device_type_id
          || "Catalog Device",

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
  const notes =
    [
      values.technician_notes,

      `Catalog Device ID: ${values.catalog_device_id}`,

      `Service ID: ${values.service_id}`,

      `Service: ${values.service_name}`,

      `Pricing Status: ${values.pricing_status || "Unknown"}`,
    ]
      .filter(Boolean)
      .join("\n");

  return apiRequest(
    "/api/repairs",
    {
      method:
        "POST",

      body: {
        customer_id:
          customerId,

        device_id:
          deviceId,

        repair_status:
          values.repair_status,

        problem_description:
          (
            `${values.service_name}: `
            + values.problem_description
          ),

        technician_notes:
          notes,

        estimated_cost:
          values.estimated_cost,
      },
    }
  );
}


/*
=========================================================
Repair Queue Filters
=========================================================
*/

function initializeRepairQueueFilters(
  form
) {
  const search =
    document.querySelector(
      "#repairQueueSearch"
    );

  const status =
    document.querySelector(
      "#repairQueueStatusFilter"
    );

  const priority =
    document.querySelector(
      "#repairQueuePriorityFilter"
    );

  const overdue =
    document.querySelector(
      "#repairQueueOverdueOnly"
    );

  search?.addEventListener(
    "input",
    () => {
      renderFilteredRepairQueue(
        form
      );
    }
  );

  status?.addEventListener(
    "change",
    () => {
      renderFilteredRepairQueue(
        form
      );
    }
  );

  priority?.addEventListener(
    "change",
    () => {
      renderFilteredRepairQueue(
        form
      );
    }
  );

  overdue?.addEventListener(
    "change",
    () => {
      renderFilteredRepairQueue(
        form
      );
    }
  );
}


async function loadRepairQueue(
  form
) {
  const queue =
    document.querySelector(
      "#repairQueue"
    );

  if (!queue) {
    console.error(
      "Repair queue element not found."
    );

    return;
  }

  queue.innerHTML = `
    <p>
      Loading repair queue...
    </p>
  `;

  try {
    repairQueueRecords =
      await apiRequest(
        "/api/repair-queue"
      );

    console.log(
      "Repair queue records:",
      repairQueueRecords
    );

    renderFilteredRepairQueue(
      form
    );
  } catch (error) {
    console.error(
      "Repair queue load failed:",
      error
    );

    queue.innerHTML = `
      <p>
        Unable to load repair queue.
      </p>
    `;
  }
}


function renderFilteredRepairQueue(
  form
) {
  const queue =
    document.querySelector(
      "#repairQueue"
    );

  if (!queue) {
    return;
  }

  const search =
    (
      document.querySelector(
        "#repairQueueSearch"
      )?.value
      || ""
    )
      .trim()
      .toLowerCase();

  const status =
    document.querySelector(
      "#repairQueueStatusFilter"
    )?.value
    || "";

  const priority =
    document.querySelector(
      "#repairQueuePriorityFilter"
    )?.value
    || "";

  const overdueOnly =
    document.querySelector(
      "#repairQueueOverdueOnly"
    )?.checked
    === true;

  const today =
    new Date();

  today.setHours(
    0,
    0,
    0,
    0
  );

  const filtered =
    repairQueueRecords.filter(
      (repair) => {
        if (
          status
          && repair.repair_status
          !== status
        ) {
          return false;
        }

        if (
          priority
          && repair.priority
          !== priority
        ) {
          return false;
        }

        if (search) {
          const searchable =
            [
              repair.id,
              repair.customer_name,
              repair.manufacturer,
              repair.device_model,
              repair.problem_description,
              repair.repair_status,
              repair.priority,
            ]
              .filter(Boolean)
              .join(" ")
              .toLowerCase();

          if (
            !searchable.includes(
              search
            )
          ) {
            return false;
          }
        }

        if (overdueOnly) {
          if (
            !repair.due_date
          ) {
            return false;
          }

          const due =
            new Date(
              `${repair.due_date}T00:00:00`
            );

          if (
            Number.isNaN(
              due.getTime()
            )
          ) {
            return false;
          }

          if (
            due >= today
          ) {
            return false;
          }

          if (
            repair.repair_status
            === "Completed"
          ) {
            return false;
          }
        }

        return true;
      }
    );

  renderRepairQueue(
    form,
    queue,
    filtered
  );
}


function renderRepairQueue(
  form,
  queue,
  repairs
) {
  queue.innerHTML =
    "";

  if (
    !Array.isArray(
      repairs
    )
    || repairs.length === 0
  ) {
    queue.innerHTML = `
      <p>
        No repairs match the current filters.
      </p>
    `;

    return;
  }

  for (
    const repair
    of repairs
  ) {
    const card =
      document.createElement(
        "article"
      );

    card.className =
      "repair-queue-card";

    card.tabIndex =
      0;

    card.setAttribute(
      "role",
      "button"
    );

    card.setAttribute(
      "aria-label",
      `Open repair ${repair.id}`
    );

    const deviceName =
      [
        repair.manufacturer,
        repair.device_model,
      ]
        .filter(Boolean)
        .join(" ");

    card.innerHTML = `
      <div class="repair-queue-card-header">

        <strong>
          ${escapeHtml(
            repair.id
          )}
        </strong>

        <span class="repair-status">
          ${escapeHtml(
            repair.repair_status
            || "Unknown"
          )}
        </span>

      </div>

      <div>
        <strong>
          ${escapeHtml(
            repair.customer_name
            || repair.customer_id
          )}
        </strong>
      </div>

      <div>
        ${escapeHtml(
          deviceName
          || repair.device_id
        )}
      </div>

      <div>
        Priority:
        <strong>
          ${escapeHtml(
            repair.priority
            || "Normal"
          )}
        </strong>
      </div>

      <div>
        Technician:
        ${escapeHtml(
          repair.technician
          || "Ryan Brown"
        )}
      </div>

      <div>
        Due:
        ${escapeHtml(
          formatDueDate(
            repair.due_date
          )
        )}
      </div>

      <div>
        Estimated:
        ${escapeHtml(
          formatCurrency(
            repair.estimated_cost
          )
        )}
      </div>

      <div>
        ${escapeHtml(
          repair.problem_description
          || ""
        )}
      </div>
    `;

    const openCard =
      async () => {
        try {
          await openRepairDetails(
            form,
            repair.id
          );
        } catch (error) {
          showRepairError(
            form,
            error
          );
        }
      };

    card.addEventListener(
      "click",
      openCard
    );

    card.addEventListener(
      "keydown",
      async (event) => {
        if (
          event.key
          !== "Enter"
          && event.key
          !== " "
        ) {
          return;
        }

        event.preventDefault();

        await openCard();
      }
    );

    queue.appendChild(
      card
    );
  }
}


/*
=========================================================
Repair Details
=========================================================
*/

async function openRepairDetails(
  form,
  repairId
) {
  const repair =
    await apiRequest(
      `/api/repairs/${
        encodeURIComponent(
          repairId
        )
      }`
    );

  const panel =
    document.querySelector(
      "#repairDetailsPanel"
    );

  if (!panel) {
    throw new Error(
      "Repair details panel was not found."
    );
  }

  panel.dataset.repairId =
    repair.id;

  const ticket =
    panel.querySelector(
      "#repairDetailsTicketId"
    );

  const status =
    panel.querySelector(
      "#repairDetailsStatus"
    );

  const technician =
    panel.querySelector(
      "#repairDetailsTechnician"
    );

  const finalCost =
    panel.querySelector(
      "#repairDetailsFinalCost"
    );

  const notes =
    panel.querySelector(
      "#repairDetailsNotes"
    );

  const priority =
    panel.querySelector(
      "#repairDetailsPriority"
    );

  const dueDate =
    panel.querySelector(
      "#repairDetailsDueDate"
    );

  if (ticket) {
    ticket.textContent =
      `Ticket: ${repair.id}`;
  }

  if (status) {
    status.value =
      repair.repair_status
      || "New Intake";
  }

  if (technician) {
    technician.value =
      repair.technician
      || "Ryan Brown";
  }

  if (finalCost) {
    finalCost.value =
      repair.final_cost
      ?? "";
  }

  if (notes) {
    notes.value =
      repair.technician_notes
      || "";
  }

  if (priority) {
    priority.value =
      repair.priority
      || "Normal";
  }

  if (dueDate) {
    dueDate.value =
      repair.due_date
      || "";
  }

  panel.hidden =
    false;

  await loadRepairTimeline(
    repair.id
  );

  panel.scrollIntoView(
    {
      behavior:
        "smooth",

      block:
        "start",
    }
  );
}


async function saveRepairDetails(
  form
) {
  const panel =
    document.querySelector(
      "#repairDetailsPanel"
    );

  if (!panel) {
    return;
  }

  const repairId =
    panel.dataset.repairId;

  if (!repairId) {
    throw new Error(
      "No repair ticket is selected."
    );
  }

  const status =
    panel.querySelector(
      "#repairDetailsStatus"
    );

  const technician =
    panel.querySelector(
      "#repairDetailsTechnician"
    );

  const finalCost =
    panel.querySelector(
      "#repairDetailsFinalCost"
    );

  const notes =
    panel.querySelector(
      "#repairDetailsNotes"
    );

  const priority =
    panel.querySelector(
      "#repairDetailsPriority"
    );

  const dueDate =
    panel.querySelector(
      "#repairDetailsDueDate"
    );

  const finalCostValue =
    finalCost?.value
      ?.trim()
    || "";

  const body = {
    repair_status:
      status?.value
      || null,

    technician:
      technician?.value
      || "Ryan Brown",

    technician_notes:
      notes?.value
      || "",

    final_cost:
      finalCostValue
        ? Number(
            finalCostValue
          )
        : null,

    priority:
      priority?.value
      || "Normal",

    due_date:
      dueDate?.value
      || "",
  };

  if (
    body.final_cost
    !== null
    && (
      Number.isNaN(
        body.final_cost
      )
      || body.final_cost < 0
    )
  ) {
    throw new Error(
      "Final cost must be a valid positive number."
    );
  }

  await apiRequest(
    `/api/repairs/${
      encodeURIComponent(
        repairId
      )
    }`,
    {
      method:
        "PATCH",

      body,
    }
  );

  await loadRepairTimeline(
    repairId
  );

  await loadRepairQueue(
    form
  );

  showRepairInfo(
    form,
    `Repair ${repairId} updated successfully.`
  );
}


function closeRepairDetails(
  form
) {
  void form;

  const panel =
    document.querySelector(
      "#repairDetailsPanel"
    );

  if (!panel) {
    return;
  }

  panel.hidden =
    true;

  delete panel.dataset
    .repairId;
}


/*
=========================================================
Repair Timeline
=========================================================
*/

async function loadRepairTimeline(
  repairId
) {
  const timeline =
    document.querySelector(
      "#repairTimeline"
    );

  if (!timeline) {
    return;
  }

  timeline.innerHTML = `
    <p>
      Loading timeline...
    </p>
  `;

  try {
    const events =
      await apiRequest(
        `/api/repairs/${
          encodeURIComponent(
            repairId
          )
        }/events`
      );

    renderRepairTimeline(
      timeline,
      events
    );
  } catch (error) {
    console.error(
      "Repair timeline load failed:",
      error
    );

    timeline.innerHTML = `
      <p>
        Unable to load timeline.
      </p>
    `;
  }
}


function renderRepairTimeline(
  timeline,
  events
) {
  timeline.innerHTML =
    "";

  if (
    !Array.isArray(
      events
    )
    || events.length === 0
  ) {
    timeline.innerHTML = `
      <p>
        No timeline events recorded yet.
      </p>
    `;

    return;
  }

  for (
    const event
    of [...events].reverse()
  ) {
    const item =
      document.createElement(
        "article"
      );

    item.className =
      "repair-timeline-item";

    const changedValues =
      (
        event.old_value
        || event.new_value
      )
        ? `
          <div class="repair-timeline-change">
            ${escapeHtml(
              event.old_value
              || "—"
            )}
            →
            ${escapeHtml(
              event.new_value
              || "—"
            )}
          </div>
        `
        : "";

    item.innerHTML = `
      <div class="repair-timeline-date">
        ${escapeHtml(
          formatRepairDate(
            event.created_at
          )
        )}
      </div>

      <div class="repair-timeline-content">

        <strong>
          ${escapeHtml(
            formatEventType(
              event.event_type
            )
          )}
        </strong>

        ${changedValues}

        ${
          event.notes
            ? `
              <div>
                ${escapeHtml(
                  event.notes
                )}
              </div>
            `
            : ""
        }

        <small>
          By
          ${escapeHtml(
            event.created_by
            || "Ryan Brown"
          )}
        </small>

      </div>
    `;

    timeline.appendChild(
      item
    );
  }
}


/*
=========================================================
API
=========================================================
*/

async function apiRequest(
  path,
  options = {}
) {
  const requestOptions = {
    method:
      options.method
      || "GET",

    headers: {},
  };

  if (
    options.body
    !== undefined
  ) {
    requestOptions.headers[
      "Content-Type"
    ] =
      "application/json";

    requestOptions.body =
      JSON.stringify(
        options.body
      );
  }

  const response =
    await fetch(
      `${REPAIR_API_BASE}${path}`,
      requestOptions
    );

  const contentType =
    response.headers.get(
      "content-type"
    )
    || "";

  const payload =
    contentType.includes(
      "application/json"
    )
      ? await response.json()
      : await response.text();

  if (!response.ok) {
    const message =
      (
        payload
        && typeof payload
          === "object"
        && payload.detail
      )
        ? String(
            payload.detail
          )
        : (
            `Request failed with status ${response.status}.`
          );

    throw new Error(
      message
    );
  }

  return payload;
}


/*
=========================================================
Formatting Helpers
=========================================================
*/

function splitCustomerName(
  customerName
) {
  const parts =
    customerName
      .trim()
      .split(/\s+/)
      .filter(Boolean);

  if (
    parts.length === 0
  ) {
    return {
      firstName:
        "",

      lastName:
        "",
    };
  }

  if (
    parts.length === 1
  ) {
    return {
      firstName:
        parts[0],

      lastName:
        "",
    };
  }

  return {
    firstName:
      parts[0],

    lastName:
      parts
        .slice(1)
        .join(" "),
  };
}


function formatCurrency(
  value
) {
  if (
    value === null
    || value === undefined
    || value === ""
  ) {
    return "—";
  }

  const number =
    Number(
      value
    );

  if (
    Number.isNaN(
      number
    )
  ) {
    return "—";
  }

  return new Intl.NumberFormat(
    "en-US",
    {
      style:
        "currency",

      currency:
        "USD",
    }
  ).format(
    number
  );
}


function formatDueDate(
  value
) {
  if (!value) {
    return "Not set";
  }

  const date =
    new Date(
      `${value}T00:00:00`
    );

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleDateString(
    "en-US",
    {
      year:
        "numeric",

      month:
        "short",

      day:
        "numeric",
    }
  );
}


function formatRepairDate(
  value
) {
  if (!value) {
    return "—";
  }

  const date =
    new Date(
      value
    );

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return String(
      value
    );
  }

  return date.toLocaleString(
    "en-US"
  );
}


function formatEventType(
  eventType
) {
  return String(
    eventType
    || "activity"
  )
    .replaceAll(
      "_",
      " "
    )
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase()
    );
}


/*
=========================================================
Messages
=========================================================
*/

function clearRepairMessage(
  form
) {
  form
    .querySelectorAll(
      ".repair-form-message"
    )
    .forEach(
      (message) => {
        message.remove();
      }
    );
}


function showRepairInfo(
  form,
  text
) {
  clearRepairMessage(
    form
  );

  const message =
    document.createElement(
      "div"
    );

  message.className =
    (
      "repair-form-message "
      + "repair-form-info"
    );

  message.textContent =
    text;

  form.prepend(
    message
  );
}


function showRepairSuccess(
  form,
  repair,
  customer,
  customerDevice,
  values
) {
  clearRepairMessage(
    form
  );

  const message =
    document.createElement(
      "div"
    );

  message.className =
    (
      "repair-form-message "
      + "repair-form-success"
    );

  message.innerHTML = `
    <strong>
      Repair created successfully.
    </strong>

    <div>
      Customer:
      ${escapeHtml(
        getCustomerDisplayName(
          customer
        )
      )}
    </div>

    <div>
      Device:
      ${escapeHtml(
        customerDevice.id
      )}
    </div>

    <div>
      Ticket:
      ${escapeHtml(
        repair.id
      )}
    </div>

    <div>
      Service:
      ${escapeHtml(
        values.service_name
      )}
    </div>

    <div>
      Estimated:
      ${escapeHtml(
        formatCurrency(
          values.estimated_cost
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
  clearRepairMessage(
    form
  );

  const message =
    document.createElement(
      "div"
    );

  message.className =
    (
      "repair-form-message "
      + "repair-form-error"
    );

  message.textContent =
    (
      "Unable to complete repair operation: "
      + (
          error instanceof Error
            ? error.message
            : String(error)
        )
    );

  form.prepend(
    message
  );
}


/*
=========================================================
Reset Helpers
=========================================================
*/

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


function resetCatalogSelections(
  form
) {
  const manufacturer =
    form.querySelector(
      "#repairManufacturer"
    );

  const device =
    form.querySelector(
      "#repairDevice"
    );

  if (manufacturer) {
    manufacturer.selectedIndex =
      0;
  }

  if (device) {
    device.disabled =
      true;

    device.innerHTML = `
      <option value="">
        Select manufacturer first
      </option>
    `;
  }

  delete form.dataset
    .catalogDeviceId;

  resetServiceSelection(
    form
  );
}


function resetFormAfterSuccess(
  form
) {
  form.reset();

  resetCustomerSelection(
    form
  );

  resetExistingDeviceSelection(
    form
  );

  resetCatalogSelections(
    form
  );

  hideExistingCustomerDeviceSection(
    form
  );

  showNewDeviceMode(
    form
  );
}


/*
=========================================================
HTML Escape
=========================================================
*/

function escapeHtml(
  value
) {
  return String(
    value
    ?? ""
  )
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


/*
=========================================================
Router Lifecycle
=========================================================
*/

document.addEventListener(
  "nocturnix:module-loaded",
  async (event) => {
    if (
      event.detail?.path
      === "/repairs"
    ) {
      await initializeRepairOperations();
    }
  }
);
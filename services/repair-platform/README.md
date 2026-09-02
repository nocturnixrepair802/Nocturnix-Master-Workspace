# Nocturnix Repair Platform

Nocturnix Repair Platform is a Python 3.14 and PySide6 desktop application backed
by an Excel workbook.

The active application source is in `Source/`. Project documentation currently
lives in `Source/documentation/` while the documentation folders are consolidated.

## Development setup

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

## Run the application

After installing the project, use the supported GUI entry point:

```powershell
.venv\Scripts\nocturnix.exe
```

During source development, it can also be run directly from the repository root:

```powershell
.venv\Scripts\python Source\run_gui.py
```

The console application in `Source/main.py` is retained as a legacy development
interface and is not the primary entry point.

## iFixit technical-guide metadata

Phase 1 provides read-only access to public iFixit API v2.0 metadata:

```text
GET /api/v1/integrations/ifixit/devices/search?q=iPhone%2015
GET /api/v1/integrations/ifixit/guides/search?q=iPhone%2015%20screen
GET /api/v1/integrations/ifixit/guides/{guide_id}
```

Phase 2 connects a Nocturnix manufacturer/model identity to ranked iFixit
device candidates and guide summaries without writing the selection:

```text
GET /api/v1/integrations/ifixit/device-guide-match?manufacturer=Apple&model=iPhone%2015
```

An exact category can be selected for the request with the optional
`ifixit_device_override` query parameter. Responses explain candidate confidence
and classify the result as `exact`, `likely`, `uncertain`, or `no_match`.

The integration returns attribution, metadata, and links to original iFixit pages.
It does not persist or reproduce guide steps, manuals, or images. iFixit API content
is not approved for AI ingestion or training, and commercial use requires licensing
confirmation from iFixit.

The public endpoints need no credentials. Optional runtime configuration is shown in
`.env.example`; do not commit local `.env` files.
## Mobile Sentrix supplier integration

Nocturnix integrates with Mobile Sentrix as a supplier source for product,
SKU, pricing, availability, and detailed supplier-product metadata.

Provider responsibilities remain intentionally separated:

- **Mobile Sentrix** supplies products, supplier SKUs, pricing, and availability.
- **iFixit** supplies device identification and technical-guide discovery.
- **Nocturnix** connects supplier products and technical information to internal
  devices, repairs, and operational workflows.

### API endpoints

The current read-only Mobile Sentrix API surface is:

```text
GET /api/v1/integrations/mobilesentrix/oauth/status
GET /api/v1/integrations/mobilesentrix/oauth/start
GET /api/v1/integrations/mobilesentrix/oauth/callback

GET /api/v1/integrations/mobilesentrix/products/search?q=iPhone%2015
GET /api/v1/integrations/mobilesentrix/products/{product_id}
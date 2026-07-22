# Dependency Graph

Last updated: 2026-07-22

This document lists the current application dependency surface. `Application` in
`Source/app.py` is the active composition root. Items marked **active** are created
by the official GUI startup path; items marked **unwired** exist in the repository
but are not constructed by `Application`.

```text
Application
|
+-- Managers
|   |
|   +-- RepositoryManager [active]
|   |   +-- CustomerRepository
|   |   +-- CustomerDeviceRepository
|   |   +-- DeviceRepository
|   |   +-- ManufacturerRepository
|   |   +-- DeviceFamilyRepository
|   |   +-- RepairRepository
|   |   `-- GuideRepository
|   |
|   +-- ServiceManager [active]
|   |   +-- RepositoryManager
|   |   +-- CustomerService
|   |   +-- CustomerDeviceService
|   |   +-- DeviceService
|   |   +-- RepairService
|   |   `-- TechnicalKnowledgeService
|   |
|   +-- RepairManager [active]
|   |   +-- QuoteEngine
|   |   +-- PricingEngine
|   |   +-- InventoryEngine
|   |   `-- CompatibilityEngine
|   |
|   +-- TechnicalKnowledgeManager [active]
|   |   `-- TechnicalKnowledgeService
|   |
|   +-- WorkflowManager [active]
|   |   +-- RepairManager
|   |   +-- RepairWorkflow
|   |   +-- EstimateWorkflow
|   |   `-- InvoiceWorkflow
|   |
|   +-- WorkbookManager [preferred, unwired]
|   +-- WorksheetManager [preferred, unwired]
|   |   `-- WorkbookManager
|   +-- TableManager [preferred, unwired]
|   |   +-- WorkbookManager
|   |   `-- WorksheetManager
|   +-- SeederManager [obsolete API, unwired]
|   +-- CatalogManager [unwired]
|   |   `-- CatalogGenerator
|   +-- InventoryManager [placeholder, unwired]
|   +-- ApplicationManager [placeholder, unwired]
|   `-- ControllerManager [placeholder, unwired]
|
+-- Services
|   |
|   +-- TableLoader [active infrastructure service]
|   |   +-- config.database.TABLES
|   |   +-- openpyxl
|   |   `-- pandas
|   |
|   +-- CustomerService [active]
|   |   +-- BaseService
|   |   `-- CustomerRepository
|   +-- CustomerDeviceService [active]
|   |   `-- CustomerDeviceRepository
|   +-- DeviceService [active]
|   |   +-- BaseService
|   |   +-- DeviceRepository
|   |   +-- ManufacturerRepository
|   |   +-- DeviceFamilyRepository
|   |   `-- GuideRepository
|   +-- RepairService [active]
|   |   +-- BaseService
|   |   `-- RepairRepository
|   +-- TechnicalKnowledgeService [active]
|   |   `-- GuideRepository
|   +-- CustomerEditor [active legacy helper; migrate into CustomerService]
|   |   `-- CustomerRepository
|   +-- SupplierService [unwired]
|   +-- GuideService [unwired]
|   +-- DocumentService [unwired]
|   +-- LaborService [unwired]
|   +-- ToolService [unwired]
|   +-- TrainingService [unwired]
|   `-- CatalogGenerator [unwired placeholder]
|
+-- Repositories
|   |
|   +-- RepositoryBase
|   |   +-- dict[str, pandas.DataFrame]
|   |   `-- pandas
|   |
|   +-- Active through RepositoryManager
|   |   +-- CustomerRepository -> customers
|   |   +-- CustomerDeviceRepository -> customer_devices
|   |   +-- DeviceRepository -> master_devices
|   |   +-- ManufacturerRepository -> manufacturer_catalog
|   |   +-- DeviceFamilyRepository -> device_catalog
|   |   +-- RepairRepository -> repair_tickets
|   |   `-- GuideRepository -> repair_guides
|   |
|   +-- Configured database key but unwired
|   |   +-- CompatibilityRepository -> compatibility
|   |   +-- InventoryRepository -> parts_catalog
|   |   +-- LaborRepository -> labor_rates
|   |   +-- ServiceRepository -> master_services
|   |   +-- SupplierRepository -> supplier_catalog
|   |   +-- GuideCategoryRepository -> guide_categories
|   |   +-- GuideSourceRepository -> guide_sources
|   |   `-- TechnicalLibraryRepository -> technical_library
|   |
|   `-- Database key not configured and currently unusable
|       +-- CommonFailureRepository -> common_failures
|       +-- QualityChecklistRepository -> quality_checklists
|       +-- RepairNoteRepository -> repair_notes
|       +-- RepairPartRepository -> repair_parts
|       +-- RepairToolRepository -> repair_tools
|       +-- TechnicalDocumentRepository -> technical_documents
|       +-- ToolRepository -> tool_catalog
|       `-- TrainingVideoRepository -> training_videos
|
+-- Engines
|   |
|   +-- EngineBase
|   |   `-- shared database dictionary
|   +-- PricingEngine
|   |   `-- EngineBase
|   +-- InventoryEngine
|   |   `-- EngineBase
|   +-- CompatibilityEngine
|   |   `-- EngineBase
|   `-- QuoteEngine
|       +-- CompatibilityEngine
|       `-- PricingEngine
|
+-- Controllers
|   |
|   +-- ApplicationController [legacy console path]
|   |   +-- CustomerController
|   |   +-- DeviceController
|   |   `-- legacy_ui dashboard and menus
|   +-- CustomerController
|   |   +-- ServiceManager
|   |   `-- CustomerEditor
|   +-- DeviceController
|   |   `-- ServiceManager
|   +-- RepairController
|   |   `-- ServiceManager
|   `-- TechnicalLibraryController
|       +-- BaseController
|       `-- TechnicalKnowledgeService
|
+-- GUI
|   |
|   +-- Source/run_gui.py [official entry point]
|   |   `-- gui.app.main_window.main
|   +-- MainWindow [active]
|   |   +-- Application
|   |   +-- DashboardPage
|   |   +-- CustomerPage
|   |   +-- DevicePage
|   |   `-- RepairPage
|   +-- DashboardPage
|   |   +-- BasePage
|   |   `-- StatCard
|   +-- CustomerPage
|   |   +-- BasePage
|   |   +-- CustomerGuiService
|   |   +-- CustomerTable
|   |   +-- CustomerDialog
|   |   `-- CustomerDetailsDialog
|   +-- DevicePage
|   |   +-- BasePage
|   |   +-- DeviceCatalogService
|   |   +-- DeviceTable
|   |   +-- DeviceDialog
|   |   `-- DeviceDetailsDialog
|   +-- RepairPage
|   |   +-- BasePage
|   |   +-- RepairGuiService
|   |   +-- RepairTable
|   |   `-- RepairDialog
|   +-- CustomerGuiService
|   |   +-- CustomerService
|   |   +-- CustomerEditor
|   |   `-- CustomerRepository
|   +-- DeviceCatalogService
|   |   `-- DeviceService
|   `-- RepairGuiService
|       +-- RepairService
|       +-- CustomerService
|       +-- CustomerDeviceService
|       +-- DeviceService
|       +-- CompatibilityRepository [expected but not registered]
|       `-- master_services DataFrame
|
`-- Models
    |
    +-- RepairSession [active through RepairWorkflow]
    |   `-- pandas.Series references
    +-- RepairGuide
    |   `-- BaseModel
    +-- Implemented standalone models
    |   +-- Customer
    |   +-- Device
    |   +-- Diagnostic
    |   +-- Manufacturer
    |   +-- Service
    |   +-- Supplier
    |   +-- Part
    |   +-- InventoryItem
    |   +-- Invoice
    |   +-- Payment
    |   +-- Compatibility
    |   +-- DeviceFamily
    |   +-- RepairTicket
    |   `-- RepairQuote
    `-- Empty or planned model modules
        +-- Address
        +-- CommonFailure
        +-- CustomerDevice
        +-- GuideCategory
        +-- GuideSource
        +-- LaborRate
        +-- LaborStandard
        +-- QualityChecklist
        +-- RepairJob
        +-- RepairNote
        +-- RepairPart
        +-- RepairTool
        +-- TechnicalDocument
        +-- Tool
        `-- TrainingVideo
```

## Ownership summary

- `Application` owns the top-level active managers and loaded database dictionary.
- `RepositoryManager` owns active repository instances.
- `ServiceManager` owns active business-service instances.
- `RepairManager` owns repair-engine instances.
- `WorkflowManager` owns multi-step workflow instances.
- `MainWindow` owns the active GUI pages.

The preferred `Source/managers/` workbook subsystem (`WorkbookManager`,
`WorksheetManager`, and `TableManager`) is not yet connected to `Application` or
`TableLoader`. Startup continues to use `TableLoader` directly.

`CustomerEditor` is an active legacy mutation helper used by `CustomerGuiService`
and `CustomerController`. Its behavior is planned for migration into
`CustomerService` so customer business rules have one service boundary.

## Known broken or incomplete edges

- `RepairGuiService` expects `RepositoryManager.compatibility`, which is not
  registered.
- `TechnicalKnowledgeService` expects `GuideRepository.all_guides()`, while the
  repository currently exposes `all()`.
- Several implemented repositories bind database keys that are not loaded by the
  current `config.database.TABLES` mapping.
- Repositories that reference absent `TABLES` keys will fail during construction:
  `RepositoryBase.__init__` indexes the shared database dictionary by key.
- Controllers belong to the legacy console path; the official GUI uses GUI services.
- Placeholder modules are listed for visibility but do not represent working
  dependencies.

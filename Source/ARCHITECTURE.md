# Nocturnix Repair Platform Architecture

Version: 0.1
Status: Draft

---

# Design Goals

The Nocturnix Repair Platform is a modular desktop repair management system.

Objectives:

- Maintainability
- Scalability
- Separation of Responsibilities
- Single Source of Truth
- Data-driven architecture
- Repository / Service pattern
- GUI independent of database

---

# Overall Architecture

GUI
↓
GUI Services
↓
Business Services
↓
Repositories
↓
Excel Database

---

# Layers

## GUI Layer

Location

Source/gui/

Responsibilities

- Display data
- Collect user input
- Validation
- Navigation

Never:

- Read Excel
- Perform business logic

---

## GUI Service Layer

Location

Source/gui/services/

Responsibilities

Convert GUI requests into business service requests.

Examples

CustomerGuiService

DeviceCatalogService

RepairGuiService

---

## Business Service Layer

Location

Source/services/

Responsibilities

Business rules.

Examples

CustomerService

DeviceService

RepairService

InventoryService

PricingService

---

## Repository Layer

Location

Source/repositories/

Responsibilities

Read and write database tables.

One repository per table.

Repositories never know about GUI.

---

## Manager Layer

Location

Source/managers/

Responsibilities

Initialize and connect the application.

RepositoryManager

ServiceManager

WorkflowManager

RepairManager

---

## Database

Single source of truth

Nocturnix_Master_Database.xlsm

All data originates here.

---

# Repository Rules

One repository per database table.

Examples

CustomerRepository

ManufacturerRepository

DeviceFamilyRepository

DeviceRepository

RepairRepository

SupplierRepository

InventoryRepository

---

# Service Rules

Services never read Excel.

Services only communicate with repositories.

Services may combine information from multiple repositories.

---

# GUI Rules

GUI never accesses repositories.

GUI only communicates with GUI Services.

---

# Dependency Flow

GUI

↓

GUI Service

↓

Business Service

↓

Repository

↓

Excel Database

---

# Future Expansion

SQLite

SQL Server

REST API

Cloud Sync

Mobile Technician App

Customer Portal

POS Integration

AI Assistant

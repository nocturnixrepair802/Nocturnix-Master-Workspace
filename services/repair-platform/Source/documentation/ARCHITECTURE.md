# ARCHITECTURE.md

# Nocturnix Repair Platform System Architecture

**Project:** Nocturnix Repair Platform
**Version:** 0.7.0 Alpha
**Status:** Active Development
**Last Updated:** July 2026

---

# Table of Contents

1. Architecture Overview
2. Design Philosophy
3. Architectural Principles
4. Application Layers
5. Project Structure
6. Module Architecture
7. Repository Layer
8. Service Layer
9. Manager Layer
10. GUI Layer
11. Database Layer
12. Seeder Framework
13. Data Flow
14. Future Architecture
15. Version 1.0 Architecture Goals

---

# 1. Architecture Overview

The Nocturnix Repair Platform follows a layered architecture designed around modular development, separation of concerns, and long-term scalability.

The application separates presentation, business logic, data access, workflow management, and persistence into independent layers.

---

# 2. Design Philosophy

The architecture is designed around the following goals:

- Modular
- Maintainable
- Reusable
- Scalable
- Testable
- Expandable

Every component should have a single responsibility.

---

# 3. Architectural Principles

## Single Responsibility Principle

Each class performs one responsibility.

Examples

- CustomerRepository
- RepairRepository
- CustomerService
- RepairService
- RepairDialog

---

## Separation of Concerns

The application separates:

- User Interface
- Business Logic
- Data Access
- Workflow
- Database

---

## Dependency Direction

Dependencies always move downward.

GUI

↓

GUI Services

↓

Business Services

↓

Repositories

↓

Managers

↓

Database

↓

Excel Workbook

---

# 4. Application Layers

## Presentation Layer

Responsibilities

- Pages
- Dialogs
- Widgets
- User Interaction

Folder

```
Source/gui/
```

---

## GUI Service Layer

Responsibilities

- GUI data preparation
- UI helpers
- Display formatting

Folder

```
Source/gui/services/
```

---

## Business Service Layer

Responsibilities

- Business rules
- Validation
- Processing
- Workflow coordination

Folder

```
Source/services/
```

---

## Repository Layer

Responsibilities

- Data retrieval
- Search
- Filtering
- CRUD operations

Folder

```
Source/repositories/
```

---

## Manager Layer

Responsibilities

- Coordinate application components
- Manage repositories
- Manage services
- Workflow management

Folder

```
Source/managers/
```

---

## Database Layer

Responsibilities

- Workbook loading
- Table loading
- Persistence
- Save Engine

Folder

```
Source/data/
```

---

# 5. Project Structure

```
Source/

app.py

config/

data/

gui/

managers/

repositories/

services/

seeders/

scripts/

tests/
```

---

# 6. Module Architecture

Current Modules

- Customer Management
- Device Management
- Repair Management
- Seeder Framework

Future Modules

- Inventory
- Suppliers
- Reports
- Dashboard
- Settings
- User Management

---

# 7. Repository Layer

Repositories currently implemented

- RepositoryBase
- CustomerRepository
- CustomerDeviceRepository
- DeviceRepository
- RepairRepository
- ManufacturerRepository
- DeviceFamilyRepository

Responsibilities

- Search
- Filter
- Find
- Count
- Replace
- Append

Repositories shall never contain GUI logic.

---

# 8. Service Layer

Current Services

- CustomerService
- CustomerDeviceService
- DeviceService
- RepairService

Responsibilities

- Business Logic
- Validation
- Workflow
- Rule Enforcement

---

# 9. Manager Layer

Managers

- RepositoryManager
- ServiceManager
- RepairManager
- WorkflowManager

Responsibilities

- Coordinate repositories
- Coordinate services
- Maintain application state

---

# 10. GUI Layer

Pages

- Customer Page
- Repair Page

Dialogs

- Repair Dialog

Widgets

- Customer Table
- Repair Table

Future

- Inventory Page
- Dashboard
- Reports

---

# 11. Database Layer

Primary Database

```
Nocturnix_Master_Database.xlsm
```

Current Tables

- Customers
- Customer Devices
- Repair Tickets
- Diagnostics
- Manufacturers
- Device Catalog
- Master Devices
- Service Types
- Master Services
- Compatibility
- Parts
- Suppliers
- Labor Rates
- Retail Pricing
- Profit Margin

The workbook serves as the system of record.

---

# 12. Seeder Framework

Current Seeders

- CustomerSeeder
- CustomerDeviceSeeder
- RepairSeeder
- SeederManager

Execution Flow

```
CustomerSeeder

↓

CustomerDeviceSeeder

↓

RepairSeeder

↓

SeederManager

↓

Application Database
```

Current Status

Memory Generation Only

Future

Workbook Persistence

---

# 13. Data Flow

Application Startup

```
Application

↓

TableLoader

↓

Workbook

↓

Repositories

↓

Services

↓

GUI
```

Repair Workflow

```
User

↓

Repair Dialog

↓

GUI Service

↓

Repair Service

↓

Repair Repository

↓

Database
```

Future Save Workflow

```
Application

↓

Workbook Writer

↓

Table Writer

↓

Workbook Save

↓

Excel Database
```

---

# 14. Future Architecture

Planned Components

- Workbook Writer
- Save Engine
- Inventory Manager
- Reporting Engine
- Dashboard Engine
- Authentication
- Cloud Sync
- Customer Portal
- REST API
- Mobile Companion

---

# 15. Version 1.0 Architecture Goals

Version 1.0 shall include

- Complete layered architecture
- Modular services
- Modular repositories
- Workbook Save Engine
- Inventory subsystem
- Reporting subsystem
- Dashboard subsystem
- Full QA coverage
- Complete documentation

---

# Architecture Status

| Layer             | Status     |
| ----------------- | ---------- |
| GUI               | 🟢 Complete |
| GUI Services      | 🟢 Complete |
| Business Services | 🟢 Complete |
| Repository Layer  | 🟢 Complete |
| Manager Layer     | 🟢 Complete |
| Database Loader   | 🟢 Complete |
| Seeder Framework  | 🟢 Complete |
| Save Engine       | 🟡 Planned  |
| Inventory         | ⚪ Planned  |
| Reporting         | ⚪ Planned  |
| Dashboard         | ⚪ Planned  |

---

# Related Documents

- README.md
- REQUIREMENTS.md
- MASTER_DEVELOPMENT_PLAN.md
- CHANGELOG.md
- PROJECT_STATUS.md
- QA_STATUS.md
- AGENTS.md
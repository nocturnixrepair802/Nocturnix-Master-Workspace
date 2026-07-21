# AGENTS.md

# Nocturnix Repair Platform Development Guide

**Project:** Nocturnix Repair Platform
**Version:** 0.7.0 Alpha
**Status:** Active Development
**Last Updated:** July 2026

---

# Purpose

This document defines the development standards, architectural rules, coding practices, documentation requirements, testing expectations, and AI collaboration guidelines for the Nocturnix Repair Platform.

All contributors—including AI assistants—must follow these standards to ensure consistency, maintainability, and long-term scalability.

---

# Development Philosophy

The Nocturnix Repair Platform is being developed as a professional desktop application using enterprise software engineering principles.

Every feature must be:

- Modular
- Reusable
- Well documented
- Fully tested
- Easily maintainable
- Scalable

Code quality always takes priority over development speed.

---

# Core Development Principles

## Single Responsibility Principle

Every class should have one responsibility.

Examples

✔ CustomerRepository

✔ RepairRepository

✔ CustomerService

✔ RepairService

Avoid classes that perform multiple unrelated responsibilities.

---

## Separation of Concerns

Separate the application into distinct layers.

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

Each layer communicates only with adjacent layers.

---

# Project Architecture

Current Layers

GUI

- Pages
- Dialogs
- Widgets

↓

GUI Services

↓

Business Services

↓

Repositories

↓

Managers

↓

Excel Database

Future Layers

- Reporting
- Inventory
- Analytics
- Cloud Sync
- API

---

# Folder Structure

Source/

```
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

Documentation/

```
README.md
CHANGELOG.md
MASTER_DEVELOPMENT_PLAN.md
PROJECT_STATUS.md
QA_STATUS.md
RELEASE_NOTES.md
ARCHITECTURE.md
REQUIREMENTS.md
TODO.md
```

---

# Naming Standards

## Classes

PascalCase

Examples

```
CustomerRepository

RepairRepository

CustomerService

RepairDialog
```

---

## Methods

snake_case

Examples

```
search_customer()

load_repairs()

save_ticket()

create_customer()
```

---

## Variables

snake_case

Examples

```
customer_id

repair_ticket

device_model

labor_rate
```

---

## Constants

UPPER_CASE

Examples

```
MASTER_DATABASE

TABLES

PROJECT_ROOT
```

---

# Repository Rules

Repositories are responsible only for data access.

Repositories shall never:

- Display UI
- Perform business logic
- Modify GUI components

Repositories may:

- Search
- Filter
- Retrieve
- Append
- Replace
- Validate

---

# Service Rules

Services contain business logic.

Services may:

- Validate data
- Process workflow
- Coordinate repositories
- Enforce business rules

Services shall not directly manipulate GUI components.

---

# GUI Rules

GUI classes shall only:

- Display information
- Receive user input
- Call services
- Refresh controls

Business logic belongs in Services.

---

# Database Rules

The Excel workbook is the system of record.

All data must eventually be persisted to:

```
Nocturnix_Master_Database.xlsm
```

Tables must remain synchronized with the application schema.

---

# Seeder Standards

Seeders generate realistic development data.

Current Seeders

- CustomerSeeder
- CustomerDeviceSeeder
- RepairSeeder

Future Seeders

- InventorySeeder
- SupplierSeeder
- PurchaseOrderSeeder

Seeders shall never overwrite production data.

---

# Testing Standards

Every completed feature requires:

- Functional testing
- GUI testing
- Repository testing
- Service testing
- QA verification

Major milestones require regression testing.

---

# Documentation Requirements

Every sprint must update:

- CHANGELOG.md
- PROJECT_STATUS.md
- QA_STATUS.md
- RELEASE_NOTES.md
- MASTER_DEVELOPMENT_PLAN.md
- TODO.md
- VERSION_HISTORY.md

Documentation is considered part of the feature.

A sprint is not complete until both code and documentation are complete.

---

# Git Workflow

At the end of every sprint:

```
git status

git add .

git commit

git push
```

Commit messages should clearly describe the completed sprint or feature.

Example

```
Sprint 7

Repair Module Integration

Seeder Framework
```

---

# Backup Policy

Every completed sprint requires:

- Git Commit
- Git Push
- ZIP Backup

Major releases also require:

- Version Tag
- Release Archive

---

# AI Development Guidelines

AI assistance should:

- Preserve existing architecture.
- Avoid unnecessary redesigns.
- Maintain consistent coding standards.
- Keep documentation synchronized.
- Recommend scalable solutions.
- Respect repository and service boundaries.

AI should prefer improving the current architecture rather than replacing working components.

---

# Definition of Done

A feature is complete only when:

✓ Code implemented

✓ Unit tested

✓ GUI tested

✓ QA verified

✓ Documentation updated

✓ Git committed

✓ Backup created

---

# Current Development Phase

Sprint 7 Complete

Current Focus

- Repair Module
- Seeder Framework

Next Sprint

Sprint 8

Workbook Save Engine

---

# Long-Term Goals

Version 1.0

- Complete repair workflow
- Inventory management
- Reporting
- Dashboard
- Installer

Version 2.0

- Cloud synchronization
- Customer portal
- Online booking
- AI diagnostics
- Mobile companion application

---

# Guiding Principle

The Nocturnix Repair Platform is being developed as a long-term professional business application.

Every design decision should prioritize maintainability, scalability, and consistency over short-term convenience.
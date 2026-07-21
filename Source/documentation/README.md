# README.md

# Nocturnix Repair Platform

**Project:** Nocturnix Repair Platform
**Version:** 0.7.0 Alpha
**Status:** Active Development
**Current Sprint:** Sprint 7 Complete
**Next Sprint:** Sprint 8 – Workbook Save Engine
**Last Updated:** July 2026

---

# Table of Contents

- Project Overview
- Vision
- Project Objectives
- Key Features
- System Architecture
- Project Structure
- Technology Stack
- Current Development Status
- Current Modules
- Future Modules
- Installation
- Running the Application
- Development Workflow
- Documentation
- Version History
- License

---

# Project Overview

The Nocturnix Repair Platform is a professional desktop repair management application designed specifically for Nocturnix Mobile Repair.

The platform is intended to provide an all-in-one solution for managing customers, devices, repair tickets, inventory, reporting, pricing, business operations, and future integrations from a single desktop application.

Unlike traditional repair management software, the platform is designed around a modular architecture that allows future expansion without requiring major redesigns.

---

# Vision

Develop a scalable, professional repair management platform capable of supporting every aspect of Nocturnix Mobile Repair while maintaining a clean architecture suitable for long-term growth.

The application is being designed as an enterprise-grade desktop platform with future support for:

- Multi-user operation
- Cloud synchronization
- Online booking
- Customer portal
- Mobile companion applications
- Business analytics
- AI-assisted diagnostics
- Inventory forecasting

---

# Project Objectives

## Primary Objectives

- Centralize all repair operations
- Improve workflow efficiency
- Eliminate duplicate data entry
- Maintain a single master database
- Simplify technician workflows
- Improve reporting accuracy
- Support long-term scalability

---

# Key Features

## Customer Management

- Customer Profiles
- Contact Information
- Customer History
- Search
- Customer Devices

---

## Device Management

- Manufacturer Catalog
- Device Families
- Master Device Database
- Customer Device Tracking

---

## Repair Management

- Repair Intake
- Repair Tickets
- Status Tracking
- Technician Assignment
- Repair History

---

## Inventory Management (Planned)

- Parts Inventory
- Suppliers
- Purchase Orders
- Stock Levels
- Low Inventory Alerts

---

## Reporting (Planned)

- Revenue Reports
- Technician Reports
- Customer Reports
- Inventory Reports
- Dashboard Analytics

---

# System Architecture

The application follows a layered architecture.

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

Excel Database

↓

Master Workbook

Each layer has a single responsibility and communicates only with adjacent layers.

---

# Project Structure

Source/

- app.py
- config/
- data/
- gui/
- managers/
- repositories/
- services/
- seeders/
- scripts/
- tests/

Documentation/

- README.md
- CHANGELOG.md
- ARCHITECTURE.md
- REQUIREMENTS.md
- PROJECT_STATUS.md
- QA_STATUS.md
- RELEASE_NOTES.md
- MASTER_DEVELOPMENT_PLAN.md

Data/

- Nocturnix_Master_Database.xlsm

---

# Technology Stack

Programming Language

- Python 3.14

GUI Framework

- PySide6 (Qt)

Database

- Microsoft Excel (.xlsm)

Data Processing

- pandas
- openpyxl

IDE

- Visual Studio Code

Version Control

- Git

---

# Current Development Status

Current Version

0.7.0 Alpha

Overall Completion

Approximately 72%

Completed

- Customer Module
- Device Module
- Repository Layer
- Service Layer
- Repair Module Framework
- Seeder Framework

In Progress

- Repair Module
- Workbook Save Engine

Planned

- Inventory Module
- Reporting
- Dashboard
- Business Analytics

---

# Current Modules

Completed

- Customer Management
- Device Catalog
- Repair Framework
- Repository System
- Service System
- Seeder Framework

Planned

- Inventory
- Reports
- Dashboard
- Analytics
- Settings
- User Management

---

# Installation

Clone the repository

Create a virtual environment

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Application

Main Application

```bash
python run_gui.py
```

Seeder Framework

```bash
python .\scripts\run_seeders.py
```

---

# Development Workflow

Each development sprint follows the same process.

1. Feature Development
2. Unit Testing
3. QA Validation
4. Documentation Updates
5. Git Commit
6. Backup
7. Sprint Completion

---

# Documentation

Primary Documentation

- README.md
- CHANGELOG.md
- MASTER_DEVELOPMENT_PLAN.md
- PROJECT_STATUS.md
- QA_STATUS.md
- RELEASE_NOTES.md
- ARCHITECTURE.md
- REQUIREMENTS.md
- TODO.md

---

# Version History

Current Version

0.7.0 Alpha

Major Milestones

Version 0.1.0

Project Initialization

Version 0.2.0

Database Framework

Version 0.3.0

Customer Module

Version 0.4.0

Device Module

Version 0.5.0

Application Architecture

Version 0.6.0

Repair Module Foundation

Version 0.7.0

Repair Integration

Seeder Framework

---

# License

Internal Development Project

Copyright © Nocturnix Mobile Repair

All Rights Reserved.
# REQUIREMENTS.md

# Nocturnix Repair Platform Software Requirements Specification (SRS)

**Project:** Nocturnix Repair Platform
**Version:** 0.7.0 Alpha
**Status:** Active Development
**Last Updated:** July 2026

---

# Table of Contents

1. Introduction
2. Purpose
3. Project Scope
4. Business Objectives
5. Functional Requirements
6. Non-Functional Requirements
7. User Roles
8. System Requirements
9. Module Requirements
10. Database Requirements
11. Security Requirements
12. Reporting Requirements
13. Future Requirements
14. Version 1.0 Acceptance Criteria

---

# 1. Introduction

The Nocturnix Repair Platform is a desktop-based repair management system designed specifically for Nocturnix Mobile Repair.

The application centralizes customer management, repair tracking, inventory, pricing, reporting, and business operations into a single integrated platform.

---

# 2. Purpose

The purpose of this application is to:

- Replace manual tracking
- Eliminate duplicate data entry
- Improve repair workflow
- Maintain a centralized customer database
- Support business growth
- Provide accurate reporting
- Improve technician productivity

---

# 3. Project Scope

The application shall provide:

- Customer Management
- Customer Device Management
- Repair Ticket Management
- Inventory Management
- Parts Tracking
- Pricing Management
- Supplier Management
- Reporting
- Dashboard Analytics
- Administrative Tools

---

# 4. Business Objectives

The platform shall:

- Reduce repair intake time
- Improve technician workflow
- Improve customer communication
- Improve inventory accuracy
- Support business scalability
- Maintain a single source of truth

---

# 5. Functional Requirements

## Customer Management

The system shall:

- Create customers
- Edit customers
- Delete customers
- Search customers
- View customer history
- Store multiple contact methods
- Track customer devices

Status

✅ Complete

---

## Device Management

The system shall:

- Maintain manufacturer catalog
- Maintain device catalog
- Maintain customer devices
- Search devices
- Filter devices
- Track serial numbers
- Track IMEI / Service Tags

Status

✅ Complete

---

## Repair Management

The system shall:

- Create repair tickets
- Edit repair tickets
- Search repairs
- Filter repairs
- Track repair status
- Assign technicians
- Store repair notes
- Track warranty

Status

🟡 In Progress

---

## Inventory Management

The system shall:

- Track inventory
- Track stock levels
- Receive inventory
- Issue inventory
- Maintain suppliers
- Maintain purchase orders
- Track minimum stock

Status

⚪ Planned

---

## Reporting

The system shall:

- Produce repair reports
- Produce revenue reports
- Produce inventory reports
- Produce technician reports
- Produce customer reports

Status

⚪ Planned

---

## Dashboard

The system shall display:

- Open repairs
- Repairs by status
- Revenue
- Customer statistics
- Inventory alerts
- Technician workload

Status

⚪ Planned

---

# 6. Non-Functional Requirements

The application shall:

- Load quickly
- Maintain data integrity
- Support modular expansion
- Use reusable components
- Follow repository architecture
- Follow service architecture
- Be fully documented

---

# 7. User Roles

Current

- Administrator

Future

- Technician
- Manager
- Read Only
- Customer Portal

---

# 8. System Requirements

Programming Language

Python

GUI

PySide6

Database

Microsoft Excel (.xlsm)

Data Processing

pandas

Workbook Processing

openpyxl

Development Environment

Visual Studio Code

Version Control

Git

Operating System

Windows 11

---

# 9. Module Requirements

## Customer Module

Status

✅ Complete

---

## Device Module

Status

✅ Complete

---

## Repair Module

Status

🟡 In Progress

---

## Inventory Module

Status

⚪ Planned

---

## Supplier Module

Status

⚪ Planned

---

## Reporting Module

Status

⚪ Planned

---

## Dashboard Module

Status

⚪ Planned

---

## Settings Module

Status

⚪ Planned

---

# 10. Database Requirements

The system shall maintain:

- Customers
- Customer Devices
- Repair Tickets
- Diagnostics
- Manufacturer Catalog
- Device Catalog
- Master Devices
- Service Types
- Master Services
- Compatibility
- Parts Catalog
- Suppliers
- Labor Rates
- Retail Pricing
- Profit Margin

The Excel workbook remains the system of record until a future database migration.

---

# 11. Security Requirements

The application shall:

- Validate user input
- Prevent invalid data
- Preserve workbook integrity
- Prevent accidental overwrites
- Maintain backup compatibility

Future

- User authentication
- User permissions
- Audit logging

---

# 12. Reporting Requirements

The application shall generate:

- Daily Reports
- Weekly Reports
- Monthly Reports
- Annual Reports

Reports shall support:

- Printing
- PDF Export
- Excel Export

---

# 13. Future Requirements

Planned features include:

- Barcode scanning
- Label printing
- SMS notifications
- Email notifications
- Cloud synchronization
- Online booking
- Customer portal
- Mobile application
- AI-assisted diagnostics
- Business analytics

---

# 14. Version 1.0 Acceptance Criteria

Version 1.0 shall not be considered complete until the following modules are fully functional:

- Customer Management
- Device Management
- Repair Management
- Inventory Management
- Reporting
- Dashboard
- Workbook Save Engine
- QA Testing
- Documentation
- Installer
- Release Packaging

---

# Current Completion Status

| Module              | Completion |
| ------------------- | ---------: |
| Customer Management |       100% |
| Device Management   |       100% |
| Repair Management   |        80% |
| Inventory           |         5% |
| Reporting           |         0% |
| Dashboard           |         0% |
| Save Engine         |         0% |

Overall Project Completion

**Approximately 72%**

---

# Related Documents

- README.md
- ARCHITECTURE.md
- PROJECT_STATUS.md
- QA_STATUS.md
- MASTER_DEVELOPMENT_PLAN.md
- CHANGELOG.md
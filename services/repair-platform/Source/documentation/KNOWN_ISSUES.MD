# KNOWN_ISSUES.md

# Nocturnix Repair Platform Known Issues

**Project:** Nocturnix Repair Platform
**Current Version:** 0.7.0 Alpha
**Status:** Active Development
**Last Updated:** July 2026

---

# Table of Contents

1. Purpose
2. Critical Issues
3. High Priority Issues
4. Medium Priority Issues
5. Low Priority Issues
6. Resolved Issues
7. Deferred Issues
8. Future Improvements
9. Monitoring
10. Related Documents

---

# Purpose

This document tracks all known software issues, limitations, technical debt, deferred improvements, and enhancement opportunities for the Nocturnix Repair Platform.

Issues should remain in this document until they are resolved or intentionally deferred to a future version.

---

# Current Issue Summary

| Severity | Count |
| -------- | ----: |
| Critical |     0 |
| High     |     1 |
| Medium   |     4 |
| Low      |     6 |
| Resolved |   18+ |

Overall Application Status

🟢 Stable Alpha Development

---

# Critical Issues

## None

There are currently no known critical issues preventing continued development.

---

# High Priority Issues

## Workbook Save Engine

Status

Open

Description

The application currently loads data successfully but cannot write changes back to the Excel workbook.

Impact

High

Planned Resolution

Sprint 8

Modules Affected

- Customer
- Repairs
- Customer Devices
- Future Inventory

---

# Medium Priority Issues

## Repair Ticket Persistence

Status

Pending

Description

Repair tickets exist only in application memory until the Save Engine is implemented.

Target Sprint

Sprint 8

---

## Seeder Persistence

Status

Pending

Description

Seeder-generated data is not written back to the workbook.

Target Sprint

Sprint 8

---

## Repair Editing

Status

Pending

Description

Editing existing repair tickets has not yet been implemented.

Target Sprint

Sprint 9

---

## Repair Deletion

Status

Pending

Description

Repair deletion workflow has not yet been implemented.

Target Sprint

Sprint 9

---

# Low Priority Issues

## Dashboard

Not yet implemented.

---

## Reporting

Not yet implemented.

---

## Inventory Module

Framework only.

---

## Supplier Module

Framework only.

---

## User Authentication

Planned for a future release.

---

## Installer

Will be developed prior to Version 1.0.

---

# Resolved Issues

The following issues have been resolved during Sprints 1–7.

### Database

- Fixed Repair Ticket table schema
- Fixed Customer Device table schema
- Fixed missing Excel tables
- Corrected table loading

---

### Repository Layer

- Fixed repository inheritance
- Fixed repository initialization
- Fixed repository lookups
- Fixed column validation

---

### Repair Module

- Fixed Repair Dialog initialization
- Fixed Customer selection
- Fixed Device lookup
- Fixed search integration
- Fixed status filtering

---

### Services

- Fixed CustomerDeviceService integration
- Fixed RepairGuiService integration

---

### Seeder Framework

- Fixed SeederManager initialization
- Fixed seeder execution
- Fixed module imports

---

### Application

- Fixed application startup
- Fixed manager initialization
- Fixed repository registration

---

# Deferred Issues

The following items are intentionally postponed until after Version 1.0.

- Cloud Synchronization
- Customer Portal
- Mobile Application
- AI Repair Assistant
- AI Documentation Manager
- REST API
- Multi-user Support
- Accounting Integration
- Shipping Integration

---

# Future Improvements

## Version 1.1

- Automatic backups
- Enhanced logging
- Repair templates
- Improved search filters

---

## Version 2.0

- Cloud Sync
- Customer Portal
- Mobile App
- AI Diagnostics
- Barcode Support
- Label Printing
- SMS Notifications
- Email Notifications

---

# Monitoring

This document should be reviewed:

- At the end of every sprint
- Before every release
- Before QA certification
- Before Version 1.0 milestones

Resolved issues should be moved to the appropriate sprint section of the CHANGELOG and DEVELOPMENT_LOG.

---

# Issue Management Process

1. Identify issue
2. Assign severity
3. Add to this document
4. Assign target sprint
5. Resolve
6. QA Verify
7. Update CHANGELOG
8. Remove from active issue list

---

# Severity Definitions

## Critical

Application cannot continue development.

## High

Feature incomplete or blocks another feature.

## Medium

Feature missing but development may continue.

## Low

Enhancement or cosmetic improvement.

---

# Current Development Focus

Sprint 8

Primary Objective

Implement Workbook Save Engine

Once complete, the following issues will be resolved:

- Workbook persistence
- Repair persistence
- Customer persistence
- Customer Device persistence
- Seeder persistence

---

# Related Documents

- PROJECT_STATUS.md
- QA_STATUS.md
- CHANGELOG.md
- DEVELOPMENT_LOG.md
- BACKLOG.md
- TODO.md
- MASTER_DEVELOPMENT_PLAN.md

---

# Revision History

| Version | Date      | Description                                            |
| ------- | --------- | ------------------------------------------------------ |
| 1.0     | July 2026 | Initial Known Issues document created through Sprint 7 |
# Changelog

## Sprint 4 - 2026-07-20

### Added
- Device Module
- Device Page
- Device Table
- Device Dialog
- Device Service
- Device Repository

### Improved
- Customer Management
- Customer Dialog
- Customer Table

### Fixed
- Customer NaN display
- Customer Active column
- Main Window navigation

### Known Issues
- Device lookup tables not yet implemented

Version 0.3.0-dev

Date: July 20, 2026

Added
Initial project architecture documentation (ARCHITECTURE.md)
Repository lookup integration for normalized database
Manufacturer lookup support
Device Family lookup support
Improved Device Catalog data pipeline
Changed
Device table now reads normalized database fields.
DeviceService updated to utilize lookup repositories.
Repository architecture refactored toward single-responsibility pattern.
Service layer expanded to support lookup table translation.
Fixed
Corrected device table column mappings.
Corrected normalized database integration.
Resolved multiple repository initialization issues.
Fixed startup errors caused by missing repository references.
Corrected service initialization issues.
Identified and resolved Qt signal recursion during combo-box initialization.
Known Issues
Manufacturer filtering pending.
Device Family filtering pending.
Search filtering integration pending.
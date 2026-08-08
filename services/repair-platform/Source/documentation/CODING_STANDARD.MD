# CODING_STANDARDS.md

# Nocturnix Repair Platform Coding Standards

**Project:** Nocturnix Repair Platform
**Version:** 1.0
**Status:** Active Development
**Last Updated:** July 2026

---

# Table of Contents

1. Purpose
2. General Principles
3. Project Structure
4. Naming Conventions
5. Python Standards
6. GUI Standards
7. Repository Standards
8. Service Standards
9. Manager Standards
10. Database Standards
11. Error Handling
12. Logging
13. Documentation
14. Git Standards
15. Code Review Checklist

---

# 1. Purpose

This document establishes the coding standards for the Nocturnix Repair Platform.

Every new file and feature should follow these standards to maintain a clean, consistent, and maintainable codebase.

---

# 2. General Principles

## Follow PEP 8

All Python code shall comply with PEP 8 except where project standards explicitly differ.

---

## Readability Over Cleverness

Code should always be written for the next developer to understand.

---

## One Responsibility Per Class

Every class should have one clearly defined responsibility.

Examples

✔ CustomerRepository

✔ RepairService

✔ RepairDialog

✘ Classes that perform multiple unrelated tasks.

---

## Small Functions

Functions should ideally remain under 50 lines whenever practical.

---

# 3. Project Structure

```
Source/

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

Every new module belongs in its appropriate folder.

---

# 4. Naming Conventions

## Classes

PascalCase

Examples

CustomerRepository

RepairService

RepairDialog

WorkbookWriter

---

## Functions

snake_case

Examples

load_customers()

save_workbook()

search_repairs()

---

## Variables

snake_case

Examples

customer_id

repair_status

ticket_number

---

## Constants

UPPER_CASE

Examples

MASTER_DATABASE

TABLES

MAX_RESULTS

---

## Private Members

Leading underscore

Example

_validate_data()

---

# 5. Python Standards

Imports should follow this order:

1. Standard Library
2. Third-Party Packages
3. Local Project Modules

Example

```python
from pathlib import Path

import pandas as pd

from repositories.customer_repository import CustomerRepository
```

---

Use type hints whenever practical.

Example

```python
def get(customer_id: str):
```

---

Avoid global variables.

---

Avoid duplicate code.

---

Use descriptive variable names.

---

# 6. GUI Standards

Each GUI page should contain:

- Constructor
- UI Builder
- Signal Connections
- Data Loading
- Event Handlers
- Helper Methods

Preferred structure

```python
class RepairPage(BasePage):

    __init__()

    build_page()

    load_data()

    connect_signals()

    search_repairs()

    filter_repairs()

    refresh()
```

---

Dialogs should never contain business logic.

Business logic belongs in Services.

---

# 7. Repository Standards

Repositories shall only perform data access.

Repositories should never:

- Display GUI
- Show dialogs
- Validate business rules

Repositories may:

- Search
- Filter
- Count
- Retrieve
- Update
- Delete

---

# 8. Service Standards

Services contain business logic.

Responsibilities

- Validation
- Processing
- Workflow
- Business Rules

Services should never directly manipulate GUI widgets.

---

# 9. Manager Standards

Managers coordinate major subsystems.

Current Managers

- RepositoryManager
- ServiceManager
- RepairManager
- WorkflowManager

Managers should not contain UI code.

---

# 10. Database Standards

Excel remains the system of record.

Rules

- Never hard-code worksheet names.
- Always reference configuration constants.
- Always preserve table formatting.
- Never overwrite formulas.
- Always validate tables before writing.

---

# 11. Error Handling

Use specific exceptions whenever possible.

Preferred

```python
except KeyError:
```

Avoid

```python
except:
```

Display user-friendly error messages in the GUI.

Write technical details to the log.

---

# 12. Logging

Future logging should include:

- Startup
- Shutdown
- Save Operations
- Import Errors
- Database Errors
- Critical Exceptions

Recommended Levels

- INFO
- WARNING
- ERROR
- CRITICAL

---

# 13. Documentation

Every public class should include a docstring.

Example

```python
class CustomerRepository:
    """Provides customer data access."""
```

Every sprint must update:

- CHANGELOG.md
- PROJECT_STATUS.md
- QA_STATUS.md
- RELEASE_NOTES.md
- MASTER_DEVELOPMENT_PLAN.md

---

# 14. Git Standards

Commit messages should follow:

```
Sprint X - Short Description
```

Examples

```
Sprint 7 - Added Repair Dialog

Sprint 8 - Implement Workbook Save Engine

Sprint 10 - Inventory Module
```

Commit after:

- Completed feature
- Passing tests
- Documentation updates

---

# 15. Code Review Checklist

Before committing:

- [ ] Code follows PEP 8
- [ ] Naming conventions followed
- [ ] No duplicate code
- [ ] Repository pattern maintained
- [ ] Service pattern maintained
- [ ] Manager pattern maintained
- [ ] GUI separated from business logic
- [ ] Documentation updated
- [ ] Tests passed
- [ ] Git commit created
- [ ] Backup created

---

# Related Documents

- ARCHITECTURE.md
- REQUIREMENTS.md
- CONTRIBUTING.md
- TESTING_GUIDE.md
- DEVELOPMENT_LOG.md

---

# Revision History

| Version | Date      | Description                          |
| ------- | --------- | ------------------------------------ |
| 1.0     | July 2026 | Initial coding standards established |
# CONTRIBUTING.md

# Nocturnix Repair Platform Development Guide

**Project:** Nocturnix Repair Platform
**Version:** 1.0
**Status:** Active Development
**Last Updated:** July 2026

---

# Table of Contents

1. Purpose
2. Development Philosophy
3. Project Workflow
4. Sprint Lifecycle
5. Branch Strategy
6. Commit Standards
7. Coding Standards
8. Testing Requirements
9. Documentation Requirements
10. Pull Request Checklist
11. Definition of Done
12. Project Closeout Procedure
13. Related Documents

---

# 1. Purpose

This document establishes the official development workflow for the Nocturnix Repair Platform.

It ensures that all development follows a consistent process from planning through implementation, testing, documentation, and release.

---

# 2. Development Philosophy

The project follows these guiding principles:

- Build small, test often.
- Keep the architecture modular.
- Separate UI, business logic, and data access.
- Documentation is part of development.
- Never sacrifice maintainability for speed.
- Every sprint should leave the project in a stable state.

---

# 3. Project Workflow

Every feature follows the same workflow:

1. Review project documentation.
2. Define sprint objectives.
3. Implement feature.
4. Perform unit testing.
5. Perform integration testing.
6. Resolve defects.
7. Update documentation.
8. Commit changes to Git.
9. Create project backup.
10. Close the sprint.

---

# 4. Sprint Lifecycle

## Sprint Planning

Before development begins:

- Review BACKLOG.md.
- Select sprint objectives.
- Update MASTER_DEVELOPMENT_PLAN.md.
- Update TODO.md.

---

## Development

During development:

- Implement one feature at a time.
- Test each feature before moving on.
- Keep commits focused and descriptive.

---

## Quality Assurance

Before closing the sprint:

- Run application.
- Verify affected modules.
- Perform regression testing on related functionality.
- Resolve any discovered defects.

---

## Documentation

Update the following documents:

- CHANGELOG.md
- PROJECT_STATUS.md
- QA_STATUS.md
- RELEASE_NOTES.md
- DEVELOPMENT_LOG.md
- TODO.md
- VERSION_HISTORY.md
- MASTER_DEVELOPMENT_PLAN.md
- KNOWN_ISSUES.md (if applicable)

---

## Sprint Closeout

A sprint is not complete until:

- All planned work is finished.
- Testing has passed.
- Documentation is current.
- Git commit has been created.
- Project backup has been completed.

---

# 5. Branch Strategy

Recommended branch structure:

```
main
│
├── develop
│
├── feature/customer-module
├── feature/repair-module
├── feature/save-engine
├── feature/inventory
└── hotfix/*
```

For solo development, working directly on `main` is acceptable if each sprint concludes with a stable, tested state.

---

# 6. Commit Standards

Commit messages should follow this format:

```
Sprint X - Brief Description
```

Examples:

```
Sprint 7 - Added Repair Dialog
Sprint 8 - Implement Workbook Save Engine
Sprint 10 - Inventory Module
```

Each commit should represent a logical unit of completed work.

---

# 7. Coding Standards

All code must follow the rules in **CODING_STANDARDS.md**.

Key requirements:

- Follow PEP 8.
- Use descriptive names.
- Keep functions focused.
- Separate GUI from business logic.
- Keep repositories free of UI code.
- Keep services free of widget manipulation.

---

# 8. Testing Requirements

Before merging or completing a sprint:

## Functional Testing

- Verify new features.
- Confirm existing features still work.

## Regression Testing

Re-test:

- Customer Module
- Device Module
- Repair Module
- Seeder Framework
- Save Engine (when implemented)

## Smoke Testing

- Application starts successfully.
- Database loads.
- GUI opens.
- No startup exceptions.

---

# 9. Documentation Requirements

Every sprint must update:

- README.md
- CHANGELOG.md
- PROJECT_STATUS.md
- QA_STATUS.md
- RELEASE_NOTES.md
- MASTER_DEVELOPMENT_PLAN.md
- DEVELOPMENT_LOG.md
- TODO.md
- VERSION_HISTORY.md

Additional documents should be updated if changes affect them.

---

# 10. Pull Request Checklist

Before merging work:

- [ ] Feature complete
- [ ] Tests passed
- [ ] Documentation updated
- [ ] No known regressions
- [ ] Commit history reviewed
- [ ] Backup created

---

# 11. Definition of Done

A task is considered complete only when:

- Code is implemented.
- Feature functions as expected.
- Tests pass.
- Documentation is updated.
- No critical defects remain.
- Project builds successfully.

A sprint is considered complete only when all sprint tasks meet this definition.

---

# 12. Project Closeout Procedure

At the end of each development session:

1. Save all files.
2. Run the application.
3. Verify no startup errors.
4. Execute any relevant tests.
5. Update project documentation.
6. Commit changes to Git.
7. Create a dated project backup.
8. Record progress in DEVELOPMENT_LOG.md.
9. Update PROJECT_STATUS.md.
10. Plan the next sprint.

---

# Related Documents

- README.md
- MASTER_DEVELOPMENT_PLAN.md
- CODING_STANDARDS.md
- ARCHITECTURE.md
- REQUIREMENTS.md
- PROJECT_STATUS.md
- QA_STATUS.md
- CHANGELOG.md
- DEVELOPMENT_LOG.md
- TESTING_GUIDE.md

---

# Revision History

| Version | Date      | Description                                                     |
| ------- | --------- | --------------------------------------------------------------- |
| 1.0     | July 2026 | Initial contribution and development workflow guide established |
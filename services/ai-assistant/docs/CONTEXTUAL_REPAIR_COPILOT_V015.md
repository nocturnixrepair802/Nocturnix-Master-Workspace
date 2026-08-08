# Nocturnix v0.1.5 Contextual Repair Copilot and Business Focus Widget

Nocturnix v0.1.5 is development-only and mock-only. It supports organization, task management, reminder review, and repair-copilot drafting, but it does not diagnose or treat ADHD and does not connect to live AI, Gmail, Google Calendar, WordPress, Square, SMS, push notifications, customer systems, or Codex Cloud.

## Widget architecture
The embeddable loader lives in `src/nocturnix/static/widget-loader.js` and loads `widget.js` plus `widget.css` from the canonical static directory. The widget provides a floating launcher, expandable panel, mobile full-screen layout, keyboard controls, screen-reader status updates, reduced-motion support, online/offline notices, copy/retry/stop controls, source/task/reminder cards, and a visible development/mock warning.

## Repair copilot and context modes
Context modes are explicit: `public`, `customer`, `technician`, and `owner`. API-side permissions determine private access; prompt text is treated as content and cannot elevate the selected mode. Repair contexts store only safe mock fields: repair ID, device details, reported issue, status, technician, approval state, parts state, target date, and safety flags. Repair actions are proposals and use the approval system before any database-changing repair action can be executed.

## Business tasks, waiting-on, and follow-up tracking
`business_tasks` stores owner-scoped durable tasks with title, description, category, related repair/project, priority, effort estimate, status, next action, due/start/snooze/completion/cancellation timestamps, waiting-on type/reference, source, recurrence reference, escalation level, and retention metadata. Waiting-on states are separated from actionable work and cover customer, supplier, part, approval, payment, appointment, Codex task, pull-request review, and external response.

## Reminders, recurrence, quiet hours, and notifications
`reminders` stores scheduled, follow-up, status-age, expected-delivery, customer-reply, recurring, and review reminders. `recurrence_rules` supports a validated limited representation for daily, selected weekdays, weekly, monthly, and interval schedules. A uniqueness constraint prevents duplicate task records for the same recurrence occurrence. Notification providers are protocols; v0.1.5 implements only in-app mock and log-safe behavior with redacted summaries. Preferences expose workday times, quiet hours, reminder hourly limits, digest mode, urgent-only mode, default snooze, category toggles, morning briefing time, and end-of-day review time. Critical repair-safety alerts require a clear confirmation flow before being disabled in future implementations.

## Focus-now algorithm
The focus engine is deterministic and explainable. It considers overdue state, due date, customer impact, repair linkage, priority, effort, waiting/snooze state, available time, and escalation. It returns at most three items by default and includes explanations such as overdue customer follow-up, due today, quick task under five minutes, customer impact, or clear next action. No opaque machine-learning prioritization is used.

## Daily briefing and end-of-day review
The daily briefing combines top focus items, scheduled placeholders, customer follow-ups, repairs waiting on parts or approval, invoice and expected-parts placeholders, Codex review placeholders, a quick win, stalled risk, and recently completed tasks. End-of-day review summarizes completed, unfinished, waiting-on, overdue, tomorrow candidates, and items with no clear next action. Recovery choices are non-punitive: move to tomorrow, reschedule, mark waiting, break into smaller task, cancel, or retain in inbox.

## Codex task tracking
`codex_task_records` stores mock/background development-task tracking fields: repository, objective, status, timestamps, blocked reason, commit SHA, PR reference, test result, and next owner action. No Codex Cloud call is made.

## API routes
New versioned routes include `/api/v1/widget/config`, `/api/v1/widget/messages`, `/api/v1/conversations`, `/api/v1/tasks`, task complete/snooze/reschedule actions, `/api/v1/waiting-on`, `/api/v1/reminders`, mock reminder delivery, `/api/v1/recurrence-rules`, `/api/v1/focus-now`, `/api/v1/daily-briefing`, `/api/v1/end-of-day-review`, `/api/v1/reminder-preferences`, `/api/v1/repair-contexts`, repair proposals, and `/api/v1/codex-task-records`.

## Security boundaries and future integration
All private routes are authenticated and owner scoped. Cookie-authenticated state changes use the existing CSRF dependency. Browser code contains no credentials. Audit and notification summaries redact sensitive wording. Future real AI, email, browser/mobile push, SMS, WordPress embedding, and Mobile Repair System embedding must add explicit provider adapters, owner decisions, production transport security, external secret management, and formal review.

## Testing
Tests should cover ownership, CSRF, recurrence duplicate prevention, focus ordering and three-item limit, quiet-hour behavior, mock notification limits, repair authorization, proposed repair approvals, Codex tracking, migrations, no live network calls, and no secret leakage.

# User Management Specification

## Overview

BarPOS uses a **role-based access control (RBAC)** system. Permissions are assigned to roles, not individual users. Every user belongs to exactly one role.

If a specific employee requires a different set of permissions, a custom role is created for them — this keeps access control auditable (an admin can always see what each role allows).

---

## Roles

The system ships with four built-in roles. They can be edited or extended by admins.

| Role    | Default permissions                                    |
|---------|-------------------------------------------------------|
| barman  | `tables`                                              |
| cook    | `items`, `stock`                                      |
| manager | `tables`, `items`, `stock`, `stats`, `users`          |
| admin   | `tables`, `items`, `stock`, `stats`, `users`, `roles` |

---

## Permissions

Each permission gates a section of the application.

| Permission | What it grants                                      |
|------------|-----------------------------------------------------|
| `tables`   | Create/close tables, add and manage orders          |
| `items`    | View and edit the menu (items)                      |
| `stock`    | View and adjust item stock quantities               |
| `stats`    | Access daily statistics                             |
| `users`    | View and manage staff accounts                      |
| `roles`    | View and edit roles and their permission sets       |

---

## User Fields

| Field           | Description                                            |
|-----------------|--------------------------------------------------------|
| `id`            | Auto-increment primary key                             |
| `name`          | Display name (shown in UI)                             |
| `username`      | Unique login identifier                                |
| `password_hash` | bcrypt hash of the user's password                     |
| `role_id`       | FK → roles.id (required; determines all permissions)   |

---

## Authentication Flow

1. User opens the application.
2. A login screen is shown first; all other screens are inaccessible without a valid session.
3. User enters `username` + `password`.
4. Backend validates credentials and returns user info + permission list.
5. Frontend stores the session in memory for the duration of the browser session.
6. On each page render, the frontend checks the session. If absent, the login screen is shown.

---

## Permission Management Rules

- Only users with the `roles` permission can add or remove permissions from a role.
- Only users with the `users` permission can create, edit, or delete user accounts.
- The built-in `admin` role cannot be deleted.
- A role cannot be deleted if users are still assigned to it.

---

## Default Seed Data

On `seed-all`, the system creates:
- All four default roles with the permissions listed above.
- One `admin` user: `username=admin`, `password=admin` (must be changed in production).

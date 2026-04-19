# Manual Testing Guide — BarPOS

This document covers manual test cases for the React frontend.  
Each case includes preconditions, steps, and expected results.

---

## Environment Setup

1. Install Docker Desktop and start it.
2. Clone the repo and copy the env file:
   ```bash
   cp .env.example .env
   # Set SECRET_KEY and POSTGRES_PASSWORD in .env
   ```
3. Build and start:
   ```bash
   docker compose build
   docker compose up -d
   ```
4. Seed initial data (creates admin user + default roles + sample items):
   ```bash
   docker compose exec app python -m cli seed-all --admin-password admin
   ```
5. Open the frontend: **http://localhost:8501**
6. API docs (for direct API testing): **http://localhost:8000/docs**

To reset data between test runs:
```bash
docker compose down -v   # wipes the DB volume
docker compose up -d
docker compose exec app python -m cli seed-all --admin-password admin
```

---

## TC-AUTH: Authentication

### TC-AUTH-01 — Successful login

**Preconditions:** DB seeded with admin user.

1. Open http://localhost:8501 (or any protected URL).
2. Enter login `admin`, password `admin`.
3. Click **Войти**.

**Expected:** Redirected to `/tables`. Sidebar shows all nav items. Top-left shows user name and role.

---

### TC-AUTH-02 — Wrong credentials

**Preconditions:** On the login page.

1. Enter login `admin`, password `wrongpass`.
2. Click **Войти**.

**Expected:** Error message shown under the form. URL stays at `/login`. An "Ошибка входа" entry is recorded in the audit log.

---

### TC-AUTH-03 — Empty fields

**Preconditions:** On the login page.

1. Leave both fields empty and click **Войти**.

**Expected:** Browser validation prevents submit (HTML5 `required` attributes). No API call is made.

---

### TC-AUTH-04 — Unauthenticated access redirect

**Preconditions:** Not logged in (or after clearing localStorage).

1. Navigate directly to http://localhost:8501/tables.

**Expected:** Immediately redirected to `/login`. Protected content is not shown.

---

### TC-AUTH-05 — Session persistence across reload

**Preconditions:** Logged in as admin.

1. Navigate to any page (e.g. `/stats`).
2. Reload the browser tab (F5 / Cmd+R).

**Expected:** Still on `/stats`, still authenticated. No redirect to login. Access token is not stored in localStorage — only the refresh token is (`bar-pos-auth` key).

---

### TC-AUTH-06 — Logout clears session

**Preconditions:** Logged in as admin.

1. Click **Выйти** in the bottom of the sidebar.

**Expected:** Redirected to `/login`. `localStorage` entry `bar-pos-auth` no longer contains a `refreshToken`. Navigating to any protected URL redirects back to `/login`.

---

## TC-TABLES: Tables Board

### TC-TABLES-01 — Open a new table

**Preconditions:** Logged in with `tables` permission.

1. Click **Столы** in the sidebar.
2. Click **+ Открыть стол**.
3. Enter a name (e.g. `Стол 5`) and click **Открыть**.

**Expected:** New card appears in the grid with status "Активен", total 0.00 ₽, 0 заказов. Card has a **Закрыть** button.

---

### TC-TABLES-02 — Filter by status

**Preconditions:** At least one Active and one Closed table exist.

1. Click **Активные**.

**Expected:** Only Active cards shown.

2. Click **Закрытые**.

**Expected:** Only Closed cards shown.

3. Click **Все**.

**Expected:** All cards shown.

---

### TC-TABLES-03 — Close a table from the board

**Preconditions:** At least one Active table with at least one order.

1. Click **Закрыть** on an active card.
2. Confirm in the dialog.

**Expected:** Card status changes to "Закрыт". **Закрыть** button disappears from the card.

---

### TC-TABLES-04 — Empty state

**Preconditions:** No tables in the DB.

1. Go to Tables Board.

**Expected:** Empty state icon and message shown. No table cards.

---

## TC-TD: Table Detail

### TC-TD-01 — View table detail

**Preconditions:** At least one Active table exists.

1. Click **Открыть** on an active table card.

**Expected:** Table Detail page opens. Shows table name, status badge "Активен", empty orders list, and **+ Добавить товар** button.

---

### TC-TD-02 — Add an order (happy path)

**Preconditions:** On Table Detail of an Active table. Menu items exist.

1. Click **+ Добавить товар**.
2. Type a partial item name in the search field.
3. Click on a matching item in the list.
4. Set quantity (default 1) and click **Добавить**.

**Expected:** Order row appears with correct item name, unit price, quantity, and line total. Running total at the bottom updates.

---

### TC-TD-03 — Edit order quantity inline

**Preconditions:** Active table has at least one order.

1. Click the edit (pencil) icon on an order row.
2. Change the quantity number.
3. Click the checkmark (save) icon.

**Expected:** Quantity and line total update. Running total updates. PATCH request succeeds.

---

### TC-TD-04 — Cancel inline edit

**Preconditions:** Active table has at least one order.

1. Click the edit icon on an order row.
2. Change the quantity.
3. Click the X (cancel) icon.

**Expected:** Quantity reverts to the original value. No API call was made.

---

### TC-TD-05 — Delete an order line

**Preconditions:** Active table has at least one order.

1. Click the trash icon on an order row.

**Expected:** Order row disappears. Running total updates.

---

### TC-TD-06 — Close table from detail page

**Preconditions:** On Table Detail of an Active table.

1. Click **Закрыть стол**.
2. Confirm in the dialog.

**Expected:** Status badge changes to "Закрыт". **+ Добавить товар** button disappears. Edit and delete icons disappear from all rows.

---

### TC-TD-07 — Closed table is read-only

**Preconditions:** Open detail of a Closed table.

**Expected:** No **+ Добавить товар** button. No edit or delete icons on order rows.

---

### TC-TD-08 — Download PDF receipt

**Preconditions:** Closed table with at least one order.

1. Click **Скачать чек** (or the receipt/download button).

**Expected:** A PDF file is downloaded. Opening it shows the table name, date, order lines with prices, and total.

---

## TC-MENU: Menu (Items)

### TC-MENU-01 — Create a menu item

**Preconditions:** Logged in with `items` permission.

1. Click **Меню** in the sidebar.
2. Click **+ Добавить позицию**.
3. Enter Name = `Test Item`, Price = `9.99`, Category = `food`. Click **Сохранить**.

**Expected:** Item appears in the list with correct name, price, and category badge.

---

### TC-MENU-02 — Edit a menu item

**Preconditions:** At least one item exists.

1. Click the edit (pencil) icon on any item.
2. Change the price.
3. Click **Сохранить**.

**Expected:** Item row updates with the new price immediately.

---

### TC-MENU-03 — Toggle availability

**Preconditions:** At least one available item exists.

1. Click the edit icon on an item.
2. Uncheck **Доступен** and save.

**Expected:** Item shows a "Скрыт" badge or greyed-out state. It no longer appears in the Add Order search on Table Detail.

---

### TC-MENU-04 — Search by name

**Preconditions:** Several items exist.

1. Type a partial name in the search box.

**Expected:** List filters in real time to only matching items.

---

### TC-MENU-05 — Filter by category

**Preconditions:** Items with different categories exist.

1. Select a category from the category dropdown.

**Expected:** Only items in that category are shown.

---

### TC-MENU-06 — Delete a menu item

**Preconditions:** An item exists.

1. Click the trash icon on an item.
2. Confirm in the dialog.

**Expected:** Item disappears from the list.

---

### TC-MENU-07 — Validation: missing required fields

**Preconditions:** On the Add Item modal.

1. Leave the Name field empty and click **Сохранить**.

**Expected:** Form does not submit. Browser validation error shown on the Name field.

---

## TC-STOCK: Stock Management

### TC-STOCK-01 — Adjust stock up

**Preconditions:** Logged in with `stock` permission. At least one item with stock tracking enabled.

1. Click **Склад** in the sidebar.
2. Find an item, enter a positive number in the delta field (e.g. `5`).
3. Click **+** (increase).

**Expected:** Stock quantity increases by 5. Success state shown briefly.

---

### TC-STOCK-02 — Adjust stock down

**Preconditions:** An item has stock quantity > 0.

1. Enter a positive number in the delta field (e.g. `3`).
2. Click **−** (decrease).

**Expected:** Stock quantity decreases by 3.

---

### TC-STOCK-03 — Low stock indicator

**Preconditions:** An item has stock quantity ≤ 5.

**Expected:** The stock quantity cell is highlighted in red/amber to signal low stock.

---

### TC-STOCK-04 — Overdraft blocked

**Preconditions:** An item has stock quantity of N.

1. Enter a delta greater than N in the decrease field.
2. Click **−**.

**Expected:** Inline error message "Insufficient stock" (or equivalent Russian text) shown in red next to the row buttons. Stock is not changed.

---

## TC-USERS: User Management

### TC-USERS-01 — Create a user

**Preconditions:** Logged in with `users` permission.

1. Click **Персонал** in the sidebar.
2. Click **Добавить**.
3. Fill in: Name = `Test User`, Login = `testuser`, Password = `Pass1234!`, Role = `staff`.
4. Click **Сохранить**.

**Expected:** User appears in the table with correct name, login, and role badge.

---

### TC-USERS-02 — Edit a user's role

**Preconditions:** A non-admin user exists.

1. Click the edit icon on the user.
2. Change the Role dropdown.
3. Click **Сохранить**.

**Expected:** Role badge updates in the table.

---

### TC-USERS-03 — Edit leaves password unchanged when empty

**Preconditions:** A user exists.

1. Open edit modal.
2. Leave the password field empty.
3. Click **Сохранить**.

**Expected:** Save succeeds. User can still log in with their old password.

---

### TC-USERS-04 — Search filter

**Preconditions:** Several users exist.

1. Type a partial name or login in the search box.

**Expected:** Table filters in real time to matching users.

---

### TC-USERS-05 — Delete a user

**Preconditions:** A non-self user exists.

1. Click the trash icon on that user.
2. Confirm deletion.

**Expected:** User disappears from the table.

---

### TC-USERS-06 — Cannot delete yourself

**Preconditions:** Logged in as admin. Admin row is visible in the table.

**Expected:** The delete button on the row where "Вы" badge appears is **disabled** and cannot be clicked.

---

### TC-USERS-07 — Password validation

**Preconditions:** On the Create User modal.

1. Enter a password shorter than 8 characters or without a digit/special character.
2. Click **Сохранить**.

**Expected:** API returns an error. Error message is displayed in the form.

---

## TC-ROLES: Role Management

### TC-ROLES-01 — Create a role

**Preconditions:** Logged in with `roles` permission.

1. Click **Роли** in the sidebar.
2. Click **Новая роль**.
3. Enter Name = `testrole`, Description = `Test`.
4. Check two permissions (e.g. **Столы & заказы** and **Статистика**).
5. Click **Сохранить**.

**Expected:** New role appears in the table with the selected permission badges.

---

### TC-ROLES-02 — Edit a role's permissions

**Preconditions:** A non-admin role exists.

1. Click the edit icon on the role.
2. Check or uncheck a permission.
3. Click **Сохранить**.

**Expected:** Permission badges update in the table row.

---

### TC-ROLES-03 — Delete a role

**Preconditions:** A role exists that is not assigned to any user.

1. Click the trash icon on the role.
2. Confirm deletion.

**Expected:** Role disappears from the table.

---

### TC-ROLES-04 — Cannot delete admin role

**Preconditions:** Admin role is visible in the table.

**Expected:** The delete button on the admin row is **disabled** and shows tooltip "Нельзя удалить admin". It cannot be clicked.

---

### TC-ROLES-05 — Role with no permissions

**Preconditions:** A role with no permissions assigned exists (e.g. `staff`).

**Expected:** The Права cell shows "нет прав" instead of empty badges.

---

## TC-STATS: Statistics

### TC-STATS-01 — View today's statistics

**Preconditions:** Logged in with `stats` permission. At least one closed table with orders today.

1. Click **Статистика** in the sidebar.

**Expected:** Date picker defaults to today. Four summary cards are shown: Выручка за день, Закрытые столы, Активные столы, Заказов, Обслужено столов. Bar chart shows items sold. Orders log table is populated.

---

### TC-STATS-02 — Revenue split: active vs closed

**Preconditions:** One active table (orders) and one closed table (orders) exist today.

1. Go to Stats.

**Expected:**
- "Выручка за день" = total of all orders.
- "Закрытые столы" = sum from closed tables only.
- "Активные столы" = sum from active tables only.

---

### TC-STATS-03 — Empty state for a date with no data

**Preconditions:** No orders on a specific past date.

1. Change the date picker to `2020-01-01`.

**Expected:** All stat cards show 0. Bar chart and orders log are hidden. Message "Нет данных за 2020-01-01" is shown.

---

### TC-STATS-04 — Date picker is capped at today

**Preconditions:** On the Stats page.

**Expected:** The date input has `max` set to today's date. The browser prevents selecting a future date.

---

## TC-AUDIT: Audit Log

### TC-AUDIT-01 — Audit log renders

**Preconditions:** Logged in with `roles` permission. Several logins/actions have been performed.

1. Click **Аудит** in the sidebar.

**Expected:** Table shows events with columns: Время, Пользователь, Действие (colored badge), ID ресурса, IP.

---

### TC-AUDIT-02 — Filter by action type

**Preconditions:** Audit log has events of different types.

1. Select **Ошибка входа** from the action filter dropdown.

**Expected:** Only rows with "Ошибка входа" badge are shown. All other action types are hidden.

2. Select **Все события**.

**Expected:** All events are shown again.

---

### TC-AUDIT-03 — Change record limit

**Preconditions:** More than 50 audit events exist.

1. Change the limit dropdown from 100 to 50.

**Expected:** Table shows at most 50 rows (the most recent ones).

---

### TC-AUDIT-04 — Actions are recorded correctly

Perform the following actions and check the audit log:

| Action | Expected audit event |
|--------|---------------------|
| Successful login | `Вход` with correct username and IP |
| Failed login attempt | `Ошибка входа` with no username, correct IP |
| Logout | `Выход` with username |
| Create a role | `Роль создана` with resource ID |
| Update a role | `Роль изменена` with resource ID |
| Delete a role | `Роль удалена` with resource ID |
| Create a user | `Пользователь создан` with resource ID |
| Update a user | `Пользователь изменён` with resource ID |
| Delete a user | `Пользователь удалён` with resource ID |

---

## TC-SEC: Security

### TC-SEC-01 — Auth guard on all protected routes

**Preconditions:** Logged out (localStorage cleared).

1. Try to navigate to each of: `/tables`, `/menu`, `/stock`, `/stats`, `/users`, `/roles`, `/audit`.

**Expected:** Every URL immediately redirects to `/login`. No protected content is visible.

---

### TC-SEC-02 — Access token not persisted to localStorage

**Preconditions:** Logged in.

1. Open browser DevTools → Application → Local Storage.
2. Inspect the `bar-pos-auth` key.

**Expected:** The stored object contains `refreshToken` but **no** `accessToken`. The access token lives in memory only and is lost on page close.

---

### TC-SEC-03 — Permission-based navigation

**Preconditions:** A user exists with a role that has only the `tables` permission.

1. Log in as that user.

**Expected:** Sidebar shows only **Столы**. Navigating directly to `/menu`, `/stock`, `/stats`, `/users`, `/roles`, `/audit` redirects to `/tables` (or shows an access-denied state).

---

### TC-SEC-04 — Refresh token revoked on logout

**Preconditions:** Logged in.

1. Note the refresh token value in localStorage (`bar-pos-auth` → `state.refreshToken`).
2. Click **Выйти**.
3. Try to call `POST /api/v1/auth/refresh` with that token via API docs.

**Expected:** `401 Unauthorized` — the token has been revoked on the server.

---

### TC-SEC-05 — Concurrent session isolation

**Preconditions:** Two different browsers (or browser profiles).

1. Log in as `admin` in browser A.
2. Log in as a different user in browser B.
3. Perform an action in browser B.

**Expected:** Browser A session is unaffected. Each session has its own tokens.

---

## Known Limitations

| Limitation | Notes |
|------------|-------|
| No real-time push | Active table totals and order lists do not update automatically when another user adds orders. The Tables Board refetches every 30 s, but Table Detail requires a manual reload to see other users' changes. |
| Receipt IP shows internal Docker address | The IP column in the audit log shows the Docker network IP (e.g. `172.18.0.x`) when running locally, not the client's real IP. In production behind a reverse proxy, configure `X-Forwarded-For` forwarding. |
| Password reset | There is no self-service password reset. An admin must edit the user record to set a new password. |

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
3. Click **Sign in**.

**Expected:** Redirected to `/tables`. Sidebar shows all nav items. Top-left shows user name and role.

---

### TC-AUTH-02 — Wrong credentials

**Preconditions:** On the login page.

1. Enter login `admin`, password `wrongpass`.
2. Click **Sign in**.

**Expected:** Error message shown under the form. URL stays at `/login`. A "Login failed" entry is recorded in the audit log.

---

### TC-AUTH-03 — Empty fields

**Preconditions:** On the login page.

1. Leave both fields empty and click **Sign in**.

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

1. Click **Log out** in the bottom of the sidebar.

**Expected:** Redirected to `/login`. `localStorage` entry `bar-pos-auth` no longer contains a `refreshToken`. Navigating to any protected URL redirects back to `/login`.

---

## TC-TABLES: Tables Board

### TC-TABLES-01 — Open a new table

**Preconditions:** Logged in with `tables` permission.

1. Click **Tables** in the sidebar.
2. Click **+ Open Table**.
3. Enter a name (e.g. `Table 5`) and click **Open**.

**Expected:** New card appears in the grid with status "Active", total $0.00, 0 orders. Card has a **Close** button.

---

### TC-TABLES-02 — Filter by status

**Preconditions:** At least one Active and one Closed table exist.

1. Click **Active**.

**Expected:** Only Active cards shown.

2. Click **Closed**.

**Expected:** Only Closed cards shown.

3. Click **All**.

**Expected:** All cards shown.

---

### TC-TABLES-04 — Empty state

**Preconditions:** No tables in the DB.

1. Go to Tables Board.

**Expected:** Empty state icon and message shown. No table cards.

---

## TC-TD: Table Detail

### TC-TD-01 — View table detail

**Preconditions:** At least one Active table exists.

1. Click **View** on an active table card.

**Expected:** Table Detail page opens. Shows table name, status badge "Active", empty orders list, and **+ Add Item** button.

---

### TC-TD-02 — Add an order (happy path)

**Preconditions:** On Table Detail of an Active table. Menu items exist.

1. Click **+ Add Item**.
2. Type a partial item name in the search field.
3. Click on a matching item in the list.
4. Set quantity (default 1) and click **Add**.

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

1. Click **Close Table**.
2. Confirm in the dialog.

**Expected:** Status badge changes to "Closed". **+ Add Item** button disappears. Edit and delete icons disappear from all rows.

---

### TC-TD-07 — Closed table is read-only

**Preconditions:** Open detail of a Closed table.

**Expected:** No **+ Add Item** button. No edit or delete icons on order rows.

---

### TC-TD-08 — Download PDF receipt

**Preconditions:** Closed table with at least one order.

1. Click **Download Receipt** (or the receipt/download button).

**Expected:** A PDF file is downloaded. Opening it shows the table name, date, order lines with prices, and total.

---

## TC-MENU: Menu (Items)

### TC-MENU-01 — Create a menu item

**Preconditions:** Logged in with `items` permission.

1. Click **Menu** in the sidebar.
2. Click **+ Add Item**.
3. Enter Name = `Test Item`, Price = `9.99`, Category = `food`. Click **Save**.

**Expected:** Item appears in the list with correct name, price, and category badge.

---

### TC-MENU-02 — Edit a menu item

**Preconditions:** At least one item exists.

1. Click the edit (pencil) icon on any item.
2. Change the price.
3. Click **Save**.

**Expected:** Item row updates with the new price immediately.

---

### TC-MENU-03 — Toggle availability

**Preconditions:** At least one available item exists.

1. Click the edit icon on an item.
2. Uncheck **Available** and save.

**Expected:** Item shows a "Hidden" badge or greyed-out state. It no longer appears in the Add Order search on Table Detail.

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

1. Leave the Name field empty and click **Save**.

**Expected:** Form does not submit. Browser validation error shown on the Name field.

---

## TC-STOCK: Stock Management

### TC-STOCK-01 — Adjust stock up

**Preconditions:** Logged in with `stock` permission. At least one item with stock tracking enabled.

1. Click **Stock** in the sidebar.
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

**Expected:** Inline error message "Insufficient stock" shown in red next to the row buttons. Stock is not changed.

---

## TC-USERS: User Management

### TC-USERS-01 — Create a user

**Preconditions:** Logged in with `users` permission.

1. Click **Staff** in the sidebar.
2. Click **Add**.
3. Fill in: Name = `Test User`, Login = `testuser`, Password = `Pass1234!`, Role = `staff`.
4. Click **Save**.

**Expected:** User appears in the table with correct name, login, and role badge.

---

### TC-USERS-02 — Edit a user's role

**Preconditions:** A non-admin user exists.

1. Click the edit icon on the user.
2. Change the Role dropdown.
3. Click **Save**.

**Expected:** Role badge updates in the table.

---

### TC-USERS-03 — Edit leaves password unchanged when empty

**Preconditions:** A user exists.

1. Open edit modal.
2. Leave the password field empty.
3. Click **Save**.

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

**Expected:** The delete button on the row where "You" badge appears is **disabled** and cannot be clicked.

---

### TC-USERS-07 — Password validation

**Preconditions:** On the Create User modal.

1. Enter a password shorter than 8 characters or without a digit/special character.
2. Click **Save**.

**Expected:** API returns an error. Error message is displayed in the form.

---

## TC-ROLES: Role Management

### TC-ROLES-01 — Create a role

**Preconditions:** Logged in with `roles` permission.

1. Click **Roles** in the sidebar.
2. Click **New Role**.
3. Enter Name = `testrole`, Description = `Test`.
4. Check two permissions (e.g. **Tables & orders** and **Statistics**).
5. Click **Save**.

**Expected:** New role appears in the table with the selected permission badges.

---

### TC-ROLES-02 — Edit a role's permissions

**Preconditions:** A non-admin role exists.

1. Click the edit icon on the role.
2. Check or uncheck a permission.
3. Click **Save**.

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

**Expected:** The delete button on the admin row is **disabled** and shows tooltip "Can't delete admin". It cannot be clicked.

---

### TC-ROLES-05 — Role with no permissions

**Preconditions:** A role with no permissions assigned exists (e.g. `staff`).

**Expected:** The Permissions cell shows "no permissions" instead of empty badges.

---

## TC-STATS: Statistics

### TC-STATS-01 — View today's statistics

**Preconditions:** Logged in with `stats` permission. At least one closed table with orders today.

1. Click **Statistics** in the sidebar.

**Expected:** Date picker defaults to today. Summary cards are shown: Total Revenue, Locked, Running, Orders, Tables served. Bar chart shows items sold. Orders log table is populated.

---

### TC-STATS-02 — Revenue split: active vs closed

**Preconditions:** One active table (orders) and one closed table (orders) exist today.

1. Go to Stats.

**Expected:**
- "Total Revenue" = total of all orders.
- "Locked" = sum from closed tables only.
- "Running" = sum from active tables only.

---

### TC-STATS-03 — Empty state for a date with no data

**Preconditions:** No orders on a specific past date.

1. Change the date picker to `2020-01-01`.

**Expected:** All stat cards show 0. Bar chart and orders log are hidden. Message "No data for 2020-01-01" is shown.

---

### TC-STATS-04 — Date picker is capped at today

**Preconditions:** On the Stats page.

**Expected:** The date input has `max` set to today's date. The browser prevents selecting a future date.

---

## TC-AUDIT: Audit Log

### TC-AUDIT-01 — Audit log renders

**Preconditions:** Logged in with `roles` permission. Several logins/actions have been performed.

1. Click **Audit** in the sidebar.

**Expected:** Table shows events with columns: Time, User, Action (colored badge), Resource ID, IP.

---

### TC-AUDIT-02 — Filter by action type

**Preconditions:** Audit log has events of different types.

1. Select **Login failed** from the action filter dropdown.

**Expected:** Only rows with "Login failed" badge are shown. All other action types are hidden.

2. Select **All events**.

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
| Successful login | "Login" with correct username and IP |
| Failed login attempt | "Login failed" with no username, correct IP |
| Logout | "Logout" with username |
| Create a role | "Role created" with resource ID |
| Update a role | "Role updated" with resource ID |
| Delete a role | "Role deleted" with resource ID |
| Create a user | "User created" with resource ID |
| Update a user | "User updated" with resource ID |
| Delete a user | "User deleted" with resource ID |
| Create a discount policy | "Discount created" with resource ID |
| Update a discount policy | "Discount updated" with resource ID |
| Delete a discount policy | "Discount deleted" with resource ID |
| Add order with discount differing from active policy | "Discount overridden" with order ID |

---

## TC-DISCOUNTS: Discount Policies

### TC-DISCOUNTS-01 — Create a global discount policy

**Preconditions:** Logged in with `discounts` permission. Sidebar shows **Discounts** item.

1. Click **Discounts** in the sidebar.
2. Click **+ New discount**.
3. Enter Name = `Happy Hour`, Discount % = `15`.
4. Leave **All items** selected.
5. Set Valid from = now, leave Valid until blank.
6. Click **Save**.

**Expected:** Policy appears in the table with status badge "Active", percent `15%`, items "All items", no expiry shown.

---

### TC-DISCOUNTS-02 — Create an item-specific timed discount

**Preconditions:** At least two menu items exist.

1. Open **+ New discount**.
2. Enter Name = `Beer promo`, Discount % = `20`.
3. Select **Specific items** and check one or two items from the list.
4. Set Valid until = 1 hour from now.
5. Click **Save**.

**Expected:** Policy appears with status "Active" and `N items` badge showing the count.

---

### TC-DISCOUNTS-03 — Pause and resume a policy

**Preconditions:** At least one active policy exists.

1. Click the Pause button (⏸) on an active policy.

**Expected:** Status badge changes to "Paused". The discount is no longer applied to new orders.

2. Click the Resume button (▶) on the same policy.

**Expected:** Status badge returns to "Active".

---

### TC-DISCOUNTS-04 — Edit a policy

**Preconditions:** A policy exists.

1. Click the edit (pencil) icon on a policy.
2. Change the discount percent.
3. Click **Save**.

**Expected:** Percent column updates in the table.

---

### TC-DISCOUNTS-05 — Delete a policy

**Preconditions:** A policy exists.

1. Click the trash icon on a policy.
2. Confirm deletion.

**Expected:** Policy disappears from the list.

---

### TC-DISCOUNTS-06 — Active discount auto-applied in Add Order modal

**Preconditions:** An active global policy (e.g. 15%) exists. Open an active table.

1. Click **+ Add** on an active table.
2. Select any item from the list.

**Expected:** The Discount % field is pre-filled with `15`. The subtotal reflects the discounted price.

---

### TC-DISCOUNTS-07 — Override warning when barman changes discount

**Preconditions:** An active policy (e.g. 15%) exists. On the Add Order modal with an item selected.

1. Change the Discount % field from `15` to `0` (or any other value).

**Expected:** An amber warning banner appears: "Active policy «...» sets 15% discount. Your value differs — this will be logged."
The discount input border turns amber.

---

### TC-DISCOUNTS-08 — Override confirmation and audit log

**Preconditions:** Same as TC-DISCOUNTS-07, with discount changed away from policy value.

1. Click **Add**.

**Expected:** A confirmation modal opens: "Active policy «...» sets 15%. You are setting X%. This override will be recorded in the audit log."

2. Click **Override and add**.

**Expected:** Order is added with the custom discount. In the Audit log, a `discount_override` event appears linked to the new order ID.

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

**Expected:** Sidebar shows only **Tables**. Navigating directly to `/menu`, `/stock`, `/stats`, `/users`, `/roles`, `/audit` redirects to `/tables` (or shows an access-denied state).

---

### TC-SEC-04 — Refresh token revoked on logout

**Preconditions:** Logged in.

1. Note the refresh token value in localStorage (`bar-pos-auth` → `state.refreshToken`).
2. Click **Log out**.
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

## TC-I18N: Language Switching

### TC-I18N-01 — Switch language from English to Russian

**Preconditions:** Logged in. UI language is English (default).

1. Open the language selector (top of the sidebar or header).
2. Select **Русский**.

**Expected:** All sidebar labels, button text, form labels, and status badges switch to Russian immediately. Selected language is persisted — after page reload the UI remains in Russian (`bar-pos-lang` key in localStorage = `"ru"`).

---

### TC-I18N-02 — Switch language to Georgian

**Preconditions:** Logged in.

1. Select **ქართული** from the language selector.

**Expected:** UI switches to Georgian. Date formatting in Stats page changes to `ka-GE` locale (day/month ordering per Georgian convention).

---

### TC-I18N-03 — Language selection persists across sessions

**Preconditions:** Language set to Russian.

1. Log out and log back in.

**Expected:** UI is still in Russian. The `bar-pos-lang` localStorage key survives logout/login.

---

### TC-I18N-04 — Language selector is available on the login page

**Preconditions:** Logged out, on `/login`.

**Expected:** Language selector is visible and functional before authentication. Switching language changes the login form labels and button text immediately.

---

## TC-RECEIPT: Receipt PDF Details

### TC-RECEIPT-01 — Receipt content verification

**Preconditions:** Closed table with at least two order lines with Cyrillic item names and mixed prices.

1. Click **Download Receipt** on the closed table's detail page.
2. Open the downloaded PDF.

**Expected:** PDF contains:
- Table name (top)
- Date and time the table was opened and closed
- Each order line: item name, quantity, unit price, line total
- Grand total at the bottom
- All Cyrillic characters render correctly (no squares or fallback glyphs)

---

### TC-RECEIPT-02 — Receipt with QR code

**Preconditions:** `RECEIPT_QR` and `RECEIPT_QR_TITLE` env vars are set (e.g. `RECEIPT_QR=https://example.com`, `RECEIPT_QR_TITLE=Our website`). Container restarted after change.

1. Close a table with at least one order.
2. Download the PDF receipt.
3. Open the PDF.

**Expected:** A scannable QR code appears on the receipt. The caption text (value of `RECEIPT_QR_TITLE`) is printed below the QR code.

---

### TC-RECEIPT-03 — Receipt unavailable for active table

**Preconditions:** An active (not closed) table.

**Expected:** The **Download Receipt** button is not shown on the Table Detail page while the table is Active.

---

## TC-ORDERS: Order Edge Cases

### TC-ORDERS-01 — Price snapshot is immutable

**Preconditions:** Active table has an order for Item A at price $100.

1. Go to Menu and change Item A's price to $200.
2. Return to the Table Detail.

**Expected:** The existing order line still shows $100 (the price at order creation time). The running total is based on the original price, not the updated one.

---

### TC-ORDERS-02 — Cannot add order to a closed table (API)

**Preconditions:** A closed table exists. Use API docs at http://localhost:8000/docs.

1. Obtain a valid JWT (via `POST /api/v1/auth/login`).
2. Call `POST /api/v1/tables/{closed_id}/orders/` with a valid item payload.

**Expected:** `400 Bad Request` — response body indicates orders cannot be added to a closed table.

---

### TC-ORDERS-03 — Stock automatically adjusts when order quantity is edited

**Preconditions:** Item with `stock_qty = 10`. Order exists on an active table with quantity = 2 (so current stock is 8).

1. Click the edit icon on that order row.
2. Change quantity from 2 to 5.
3. Save.

**Expected:** Order quantity becomes 5. Item stock decreases by 3 (from 8 → 5). Verify in the Stock page.

4. Edit the order again, change quantity from 5 to 1.

**Expected:** Item stock increases by 4 (from 5 → 9).

---

### TC-ORDERS-04 — Cannot set order quantity below 1

**Preconditions:** Active table has an order. Use API docs.

1. Call `PATCH /api/v1/tables/{id}/orders/{order_id}` with `quantity: 0`.

**Expected:** `422 Unprocessable Entity` or `400 Bad Request` — quantity must be a positive integer.

---

## TC-STOCK-EXTENDED: Stock — Additional Cases

### TC-STOCK-05 — Untracked item stock cannot be adjusted

**Preconditions:** A menu item exists with stock tracking disabled (`stock_qty` is null — i.e., the item was created without enabling stock tracking). Use API docs.

1. Call `PATCH /api/v1/items/{id}/stock` with `delta: 5`.

**Expected:** `400 Bad Request` — stock adjustment is not allowed for items without stock tracking enabled.

---

### TC-STOCK-06 — Low stock threshold is ≤ 3 (not ≤ 5)

**Preconditions:** An item with stock tracking enabled.

1. Set item stock to 4 (via + adjustment in the Stock page).

**Expected:** Stock cell is displayed normally — no red/amber highlight.

2. Decrease stock to 3.

**Expected:** Stock cell turns red/amber (low-stock warning). The sidebar badge showing low-stock item count increments by 1.

---

## TC-DISCOUNTS-EXTENDED: Discount Policy — Additional Cases

### TC-DISCOUNTS-09 — Pending discount (valid_from in future)

**Preconditions:** On the Discounts page.

1. Create a new discount policy with Discount % = `10`, Valid from = 2 hours from now, Valid until = blank.

**Expected:** Policy appears in the table with status badge **"Pending"** (not "Active"). The discount is not pre-filled in the Add Order modal.

---

### TC-DISCOUNTS-10 — Expired discount

**Preconditions:** An active discount policy exists.

1. Edit the policy and set Valid until = 1 minute in the past (or a past datetime).

**Expected:** Policy status badge changes to **"Expired"**. It is no longer pre-filled in the Add Order modal.

---

### TC-DISCOUNTS-11 — Multiple overlapping policies — highest wins

**Preconditions:** Two active global discount policies exist: one at 10%, one at 20%.

1. Open an active table and click **+ Add**.
2. Select any item.

**Expected:** The Discount % field is pre-filled with `20` (the higher of the two applicable policies).

---

### TC-DISCOUNTS-12 — Item-specific policy takes effect for that item only

**Preconditions:** Two active policies: global 10%, item-specific 25% for Item A only.

1. Open Add Order modal, select Item A.

**Expected:** Discount pre-filled with `25`.

2. In the same modal, select Item B (not in the item-specific policy).

**Expected:** Discount pre-filled with `10` (global policy).

---

### TC-DISCOUNTS-13 — No override audit event when no active policy

**Preconditions:** No active discount policies exist. On the Add Order modal.

1. Manually enter any value in the Discount % field (e.g. `5`).
2. Click **Add**.

**Expected:** Order is added. No override warning banner is shown. No `discount_override` event appears in the Audit Log.

---

## TC-MENU-EXTENDED: Menu — Additional Cases

### TC-MENU-08 — Deleted item name preserved in existing orders

**Preconditions:** A closed table has at least one order for Item X. Item X exists in the menu.

1. Go to Menu and delete Item X (confirm deletion).
2. Go to Stats → Orders log and find the historical order.

**Expected:** The order line still shows Item X's original name (price snapshot preserved). The Stats page does not error out on missing item.

---

### TC-MENU-09 — Unavailable item excluded from order search

**Preconditions:** Item Y is marked unavailable (not checked as **Available**).

1. Open an active table → **+ Add Item**.
2. Search for Item Y by name.

**Expected:** Item Y does not appear in the search results. The item is hidden from order creation even if its exact name is typed.

---

## TC-USERS-EXTENDED: User Management — Additional Cases

### TC-USERS-08 — Duplicate username rejected

**Preconditions:** A user with login `bartender1` already exists.

1. Click **Add** to open the Create User modal.
2. Enter Login = `bartender1` (same as existing) and fill other required fields.
3. Click **Save**.

**Expected:** API returns an error. An error message is displayed in the form. No duplicate user is created.

---

### TC-USERS-09 — Password complexity on user update

**Preconditions:** A user exists.

1. Open the edit modal for that user.
2. Enter a new password `abcdefgh` (8 chars, no digit or special character).
3. Click **Save**.

**Expected:** API returns validation error. Error message describes the password policy (≥8 chars + digit or special character). User's password is not changed.

---

## TC-STATS-EXTENDED: Statistics — Additional Cases

### TC-STATS-05 — Top items chart

**Preconditions:** At least 3 different items have orders today (or on the selected date).

1. Go to **Statistics**.

**Expected:** A bar chart (top items) is displayed showing item names and quantities/revenue. Items are ordered from most to least sold. The list shows at most 10 items by default.

---

### TC-STATS-06 — Revenue split accuracy

**Preconditions:** Fresh DB seed. Create Table A (add 2× Item at $100 each = $200 total), keep it active. Create Table B (add 1× Item at $150), close it.

1. Go to **Statistics** → today.

**Expected:**
- "Total Revenue" = $350 (all orders)
- "Running" revenue = $200
- "Locked" revenue = $150

---

## TC-CURRENCY: Currency Display

### TC-CURRENCY-01 — Currency symbol reflects VITE_CURRENCY setting

**Preconditions:** `VITE_CURRENCY` is set to a non-default value in `.env`. Client container restarted (`docker compose restart client`).

1. Log in and navigate to Tables, Menu, Stats, and Table Detail.

**Expected:** All price displays use the configured currency symbol. Downloaded PDF receipt also reflects the configured symbol.

---

### TC-CURRENCY-02 — Default currency is $ (USD)

**Preconditions:** `VITE_CURRENCY` is not set (or set to `USD`).

**Expected:** All prices are displayed with the `$` symbol throughout the UI and in PDF receipts.

---

## TC-SEC-EXTENDED: Security — Additional Cases

### TC-SEC-06 — Login rate limiting

**Preconditions:** Logged out.

1. Submit 10 failed login attempts in rapid succession (wrong password, same IP).
2. Submit the 11th attempt.

**Expected:** The 11th request receives `429 Too Many Requests`. After waiting ~1 minute, a new attempt proceeds normally.

---

### TC-SEC-07 — Security headers in responses

**Preconditions:** App is running.

1. Run:
   ```bash
   curl -I http://localhost:8000/api/v1/auth/login
   ```

**Expected:** Response headers include:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

---

### TC-SEC-08 — API docs hidden in production mode

**Preconditions:** Set `DEBUG=false` in `.env`. Restart the app container.

1. Navigate to http://localhost:8000/docs.
2. Navigate to http://localhost:8000/openapi.json.

**Expected:** Both return 404 (docs endpoint is disabled). Reset `DEBUG=true` to restore.

---

### TC-SEC-09 — Barman can see discount for item but cannot manage discount policies

**Preconditions:** A user exists with only the `tables` permission (e.g. `barman` role). An active discount policy exists.

1. Log in as that user.

**Expected:** Sidebar does **not** show the **Discounts** navigation item. The Add Order modal still pre-fills the active discount percent correctly.

---

## Known Limitations

| Limitation | Notes |
|------------|-------|
| No real-time push | Active table totals and order lists do not update automatically when another user adds orders. The Tables Board refetches every 30 s, but Table Detail requires a manual reload to see other users' changes. |
| Receipt IP shows internal Docker address | The IP column in the audit log shows the Docker network IP (e.g. `172.18.0.x`) when running locally, not the client's real IP. In production behind a reverse proxy, configure `X-Forwarded-For` forwarding. |
| Password reset | There is no self-service password reset. An admin must edit the user record to set a new password. |

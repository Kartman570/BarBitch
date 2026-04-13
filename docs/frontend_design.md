# Frontend Design — BarPOS

## Purpose

This document describes the UI structure, screens, components, and user interactions
for the BarPOS web frontend. It is technology-agnostic — meant as a spec for any
SPA implementation (React, Vue, Svelte, etc.).

Target devices: tablet-first (bartenders at counter), secondary desktop.
No mobile-only layout required for MVP.

---

## Navigation

Fixed sidebar (collapsible on tablet).

| Item        | Icon     | Route       | Phase | Status      |
|-------------|----------|-------------|-------|-------------|
| Tables      | grid     | `/tables`   | 1     | ✅ Done     |
| Menu        | list     | `/menu`     | 1     | ✅ Done     |
| Staff       | people   | `/staff`    | 1     | ✅ Done     |
| Stats       | chart    | `/stats`    | 1     | ✅ Done     |
| Shifts      | clock    | `/shifts`   | 3     | ❌ Planned  |
| Profile     | user     | `/profile`  | 3     | ❌ Planned  |

Top bar shows: app name, current page title, logged-in user name (Phase 3 — hidden until auth).

---

## Screen 1 — Tables Board `/tables`

**Primary screen.** Barman lands here after opening the app.

### Layout

- Top row: page title "Tables", **[+ Open Table]** button (right-aligned)
- Filter bar below: three tab buttons — **All** | **Active** | **Closed** (default: All)
- Responsive card grid below

### Table Card

Each open/closed table is one card.

| Element | Details |
|---------|---------|
| Table name | Bold heading |
| Status badge | Green pill "Active" / Grey pill "Closed" |
| Order count | "N orders" |
| Running total | Currency amount (e.g. `$42.50`) — sum of all orders; `$0.00` if no orders yet |
| **[View]** button | Opens Table Detail screen |
| **[Close]** button | Visible only if status = Active. Opens Close Confirmation dialog |

Empty state (no tables): message "No tables yet — open one to get started."

### Open Table Dialog

Triggered by **[+ Open Table]**.

| Element | Details |
|---------|---------|
| Title | "Open New Table" |
| Text input | Label: "Table name", placeholder: "e.g. Table 3, Bar Tab, Terrace" — required, max 100 chars |
| **[Open]** button | Disabled until name is non-empty. Calls `POST /api/v1/tables/`. Closes dialog on success, new card appears in grid |
| **[Cancel]** button | Closes dialog without action |

### Close Confirmation Dialog

Triggered by **[Close]** on a card.

| Element | Details |
|---------|---------|
| Title | "Close table?" |
| Body | "Table: {name}" / "Total: {amount}" / "This will lock the bill and mark the table as closed." |
| **[Confirm Close]** button | Calls `POST /api/v1/tables/{id}/close`. Updates card status on success |
| **[Cancel]** button | Dismisses dialog |

---

## Screen 2 — Table Detail `/tables/{id}`

### Header

| Element | Details |
|---------|---------|
| Back link | "← Tables" — returns to Tables Board |
| Table name | Inline-editable: click pencil icon → text input → confirm (calls `PATCH /api/v1/tables/{id}`) |
| Status badge | "Active" (green) or "Closed" (grey) |
| Closed-at timestamp | Shown only when status = Closed. Format: `Closed on Apr 12, 2026 at 22:15` |

### Orders List

Displayed as a table.

| Column | Notes |
|--------|-------|
| # | Row number |
| Item | Item name (read-only) |
| Unit price | Price at time of order (read-only — snapshot) |
| Qty | Editable number input if table is Active. Calls `PATCH /api/v1/tables/{id}/orders/{oid}` on blur/confirm. Min 0.5. Disabled if Closed |
| Line total | `unit_price × qty`, updated live |
| **[×]** | Remove order line. Visible only if Active. Calls `DELETE /api/v1/tables/{id}/orders/{oid}`. Asks for confirmation if qty > 1 |

Empty state: "No orders on this table yet."

### Add Order Panel

Visible only if table status = Active. Collapsed by default; expands on **[+ Add Item]** button click.

| Element | Details |
|---------|---------|
| Item search/dropdown | Searchable list populated from `GET /api/v1/items/?available_only=true`. Shows item name + price. Required |
| Quantity input | Number input, min 0.5, step 0.5, default 1 |
| Unit price display | Read-only. Shows selected item's current price. Updates when item selection changes |
| Line total preview | `unit_price × quantity`, updates live |
| **[Add to Table]** button | Disabled until item is selected. Calls `POST /api/v1/tables/{id}/orders/` with `{item_id, quantity}`. Appends new row to orders list. Resets the form |
| **[Cancel]** link | Collapses the panel |

### Bill Footer

Always visible at the bottom of the orders list.

| Element | Details |
|---------|---------|
| Total | Sum of all line totals. Label: "Total" |
| **[Close Table]** button | Visible only if Active. Same behavior as Close on the Tables Board card |

---

## Screen 3 — Menu `/menu`

Manage the bar's item catalog.

### Layout

- Top row: "Menu" heading, **[+ Add Item]** button
- Filter bar:
  - Search input: "Search items…" — filters list by name in real time (client-side)
  - Category dropdown: "All categories" + dynamically populated list from existing items
  - Toggle: "Show unavailable" (default: off — only available items shown)
- Items table below

### Items Table

| Column | Notes |
|--------|-------|
| Name | Text |
| Price | Currency, e.g. `$5.00` |
| Category | Text or empty dash |
| Available | Toggle switch. Toggling calls `PUT /api/v1/items/{id}` with `{is_available: true/false}`. Unavailable items appear greyed out |
| Actions | **[Edit]** and **[Delete]** buttons per row |

Empty state: "No items — add your first menu item."

### Add / Edit Item Form

Displayed as a slide-over panel or modal. Same form for both actions.

| Element | Details |
|---------|---------|
| Title | "Add Item" or "Edit Item" |
| Name input | Text, required, max 100 chars |
| Price input | Number, required, min 0.01, 2 decimal places, prefix: `$` |
| Category input | Free-text input with datalist suggestions from existing categories (e.g. "beer", "cocktail", "food", "soft drink") |
| Available toggle | Default: on |
| **[Save]** button | On add: calls `POST /api/v1/items/`. On edit: calls `PUT /api/v1/items/{id}`. Closes panel on success |
| **[Cancel]** button | Closes panel, discards changes |

### Delete Item Confirmation

| Element | Details |
|---------|---------|
| Text | "Delete {name}? This cannot be undone." |
| Warning note | If item has orders: "This item is referenced in existing orders. Its name will remain in order history." (item deletion should be blocked by the API in that case — show the API error message) |
| **[Delete]** | Calls `DELETE /api/v1/items/{id}` |
| **[Cancel]** | Dismisses |

---

## Screen 4 — Staff `/staff`

Manage bar staff accounts (no auth yet — Phase 3 adds passwords).

### Layout

- Top row: "Staff" heading, **[+ Add Staff Member]** button
- Staff list

### Staff List

| Column | Notes |
|--------|-------|
| Name | Text |
| Role | Badge: "Admin" (blue), "Barman" (green), "Cook" (orange) |
| Actions | **[Edit]** / **[Delete]** buttons |

Empty state: "No staff members."

### Add / Edit Staff Member Form

| Element | Details |
|---------|---------|
| Name input | Text, required, max 50 chars |
| Role dropdown | Options: Barman (default), Cook, Admin |
| **[Save]** | `POST /api/v1/users/` or `PUT /api/v1/users/{id}` |
| **[Cancel]** | Closes form |

### Delete Confirmation

"Remove {name} from staff? This cannot be undone."

---

## Screen 5 — Stats `/stats`

View daily revenue and order activity. Read-only screen.

### Layout

- Top row: "Statistics" heading
- Date picker: label "Date", default today, max value today
- **[Refresh]** implicit — reloads when date changes

### Metrics Row

Five metric tiles displayed side by side:

| Tile | Value |
|------|-------|
| 💰 Total Revenue | Sum of all orders that day |
| 🔒 Locked | Revenue from closed tables |
| ⏳ Running | Revenue from still-active tables |
| 🧾 Orders | Total order line count |
| 🪑 Tables served | Count of distinct tables with orders |

### Items Sold

Side-by-side layout: bar chart (left) + data table (right).

- Bar chart: X axis = item name, Y axis = revenue ($). Sorted by revenue descending.
- Table columns: Item, Qty sold, Revenue ($)

Empty state: "No orders recorded for this date."

### Orders Log

Full chronological list of every order placed that day.

| Column | Notes |
|--------|-------|
| Time | `HH:MM` from `created_at` |
| Table | Table name |
| Item | Item name |
| Qty | Quantity ordered |
| Unit price | Snapshot price at time of order |
| Line total | `unit_price × qty` |

### API Call

| Action | Method | Endpoint |
|--------|--------|----------|
| Load stats | GET | `/api/v1/stats/daily?date=YYYY-MM-DD` |

---

## Global UI Elements

### Toast Notifications

Non-blocking feedback at bottom-right corner. Auto-dismiss after 4 s.

| Event | Type | Message |
|-------|------|---------|
| Table opened | Success | "Table opened" |
| Table closed | Success | "Table closed — Total: {amount}" |
| Order added | Success | "Added {item} ×{qty}" |
| Order deleted | Info | "Order removed" |
| Item saved | Success | "Item saved" |
| Any API error | Error | API error detail message |

### Confirmation Dialogs

All destructive actions (delete, close) require a confirmation dialog before the API call.

### Loading States

- Button shows spinner + disabled state while API call is in flight
- List areas show skeleton rows on initial load
- Item dropdown shows "Loading…" while fetching

### Error States

- API unavailable: full-page message "Cannot reach the server. Check your connection."
- 404 (e.g. navigating to a deleted table): "Not found — this table no longer exists." + link back
- Form validation errors: inline, below the relevant input field

---

## API Calls per Screen

| Screen / Action | Method | Endpoint |
|-----------------|--------|----------|
| Load Tables Board | GET | `/api/v1/tables/` |
| Filter by status | GET | `/api/v1/tables/?status=Active` |
| Open table | POST | `/api/v1/tables/` |
| Close table | POST | `/api/v1/tables/{id}/close` |
| Load Table Detail | GET | `/api/v1/tables/{id}` |
| Rename table | PATCH | `/api/v1/tables/{id}` |
| Delete table | DELETE | `/api/v1/tables/{id}` |
| Load orders for table | GET | `/api/v1/tables/{id}/orders/` |
| Add order | POST | `/api/v1/tables/{id}/orders/` |
| Update order qty | PATCH | `/api/v1/tables/{id}/orders/{oid}` |
| Remove order | DELETE | `/api/v1/tables/{id}/orders/{oid}` |
| Load item dropdown | GET | `/api/v1/items/?available_only=true` |
| Load Menu list | GET | `/api/v1/items/` |
| Create item | POST | `/api/v1/items/` |
| Update item | PUT | `/api/v1/items/{id}` |
| Delete item | DELETE | `/api/v1/items/{id}` |
| Load Staff list | GET | `/api/v1/users/` |
| Create user | POST | `/api/v1/users/` |
| Update user | PUT | `/api/v1/users/{id}` |
| Delete user | DELETE | `/api/v1/users/{id}` |
| Load daily stats | GET | `/api/v1/stats/daily?date=YYYY-MM-DD` |

---

## User Flows

### Opening a table and taking first round of orders

1. Barman taps **[+ Open Table]** on Tables Board
2. Types table name (e.g. "Table 5"), taps **[Open]**
3. New card appears — barman taps **[View]**
4. Table Detail opens, orders list is empty
5. Barman taps **[+ Add Item]**, selects "Beer" from dropdown, sets quantity 3, taps **[Add to Table]**
6. Order row appears: Beer × 3 @ $5.00 = $15.00
7. Barman adds more items as needed. Total updates after each add

### Closing a table

1. From Table Detail, barman taps **[Close Table]**
2. Confirmation dialog shows table name + total
3. Barman taps **[Confirm Close]**
4. Table status changes to Closed, Close Table button disappears, edit/delete controls on orders disabled
5. `closed_at` timestamp shown in header

### Updating menu prices before a shift

1. Barman/admin goes to Menu screen
2. Finds "Beer", taps **[Edit]**
3. Changes price from $5.00 to $5.50, taps **[Save]**
4. List updates immediately
5. All future orders will use the new price; existing order lines are unaffected (price snapshot)

### Marking an item unavailable (e.g. out of stock)

1. On Menu screen, find the item
2. Toggle the Available switch to off
3. Item greyed out in menu list
4. Item no longer appears in the Add Order dropdown on Table Detail

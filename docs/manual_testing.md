# Manual Testing Guide — BarPOS

This document is for QA testers. It covers the running environment, happy-path scripts,
edge cases, and known limitations.

---

## Environment Setup

1. Install Docker Desktop and start it.
2. Clone the repo and run:
   ```bash
   docker compose build
   docker compose up -d
   ```
3. Seed initial data:
   ```bash
   docker compose exec app python -m cli seed-all
   ```
4. Open the frontend: **http://localhost:8501**
5. API docs (for direct API testing): **http://localhost:8000/docs**

To reset data between test runs:
```bash
docker compose down -v   # wipes the DB volume
docker compose up -d
docker compose exec app python -m cli seed-all
```

---

## Screen: Tables Board

### TC-T01 — Open a new table

1. Click **Tables** in the sidebar.
2. Click **+ Open Table**.
3. Enter a name (e.g. `Table 5`) and click **Open**.

**Expected:** New card appears in the grid with status "Active", $0.00 total, 0 orders.

---

### TC-T02 — Filter tables by status

1. With at least one Active and one Closed table visible, use the filter buttons **All / Active / Closed**.

**Expected:** Each filter shows only the relevant cards. "All" shows everything.

---

### TC-T03 — Close a table from the board

1. Open a table (TC-T01) and add at least one order (TC-O01).
2. Return to Tables Board.
3. Click **Close** on the active card.
4. Confirm in the dialog.

**Expected:** Card status changes to "Closed". Close button disappears. Total reflects orders.

---

### TC-T04 — Empty state

1. Delete all tables (or use a fresh DB).
2. Go to Tables Board.

**Expected:** Message "No tables yet — open one to get started."

---

## Screen: Table Detail

### TC-TD01 — View table detail

1. Open a table.
2. Click **View** on the card.

**Expected:** Table Detail screen opens showing table name, Active status, empty orders list.

---

### TC-TD02 — Add an order

1. In Table Detail, click **+ Add Item**.
2. Select an item from the dropdown.
3. Adjust quantity if desired.
4. Click **Add to Table**.

**Expected:** Order row appears with correct item name, unit price, and line total (price × qty).

---

### TC-TD03 — Price snapshot

1. Add an order for item "Beer" at its current price.
2. Go to Menu, edit Beer's price to a different value.
3. Return to Table Detail.

**Expected:** The existing order still shows the *original* price. The new price only applies to future orders.

---

### TC-TD04 — Update order quantity

1. In Table Detail (Active table), find an order row.
2. Change the quantity spinner value.

**Expected:** Line total updates immediately. Total at the bottom updates.

---

### TC-TD05 — Delete an order line

1. In Table Detail (Active table), click **×** next to an order.
2. Confirm deletion.

**Expected:** Order row disappears. Total updates.

---

### TC-TD06 — Close table from detail

1. In Table Detail (Active table), click **Close Table**.
2. Confirm in the dialog.

**Expected:** Status badge changes to "Closed". Add Item panel and quantity spinners disappear. Close Table button disappears.

---

### TC-TD07 — Closed table is read-only

1. Open a closed table's detail.

**Expected:** No **+ Add Item** button. Qty spinners disabled. **×** delete buttons absent.

---

### TC-TD08 — Cannot add order to closed table (API-level)

Using API docs at http://localhost:8000/docs:

1. Find the ID of a Closed table.
2. `POST /api/v1/tables/{id}/orders/` with any valid `item_id`.

**Expected:** `400 Bad Request` — `"Cannot add order to a closed table."`

---

## Screen: Menu

### TC-M01 — Add a menu item

1. Click **Menu** in the sidebar.
2. Click **+ Add Item**.
3. Fill in: Name = `Test Item`, Price = `9.99`, Category = `food`.
4. Click **Save**.

**Expected:** Item appears in the list with correct name, price, and category.

---

### TC-M02 — Edit a menu item

1. Click **Edit** on any item.
2. Change the price.
3. Click **Save**.

**Expected:** Item row updates immediately with the new price.

> **Note:** Streamlit text inputs require pressing **Enter** after typing before clicking Save, otherwise the old value is submitted. This is a known Streamlit behavior.

---

### TC-M03 — Toggle item availability

1. Find an available item and toggle its Available switch to off.

**Expected:** Item appears greyed out in the list. It no longer appears in the Add Order dropdown on Table Detail.

2. Toggle it back on.

**Expected:** Item is fully visible and available again.

---

### TC-M04 — Search and filter

1. Type a partial name in the search box.
**Expected:** List filters in real time to matching items only.

2. Select a category from the dropdown.
**Expected:** Only items in that category are shown.

3. Enable "Show unavailable".
**Expected:** Unavailable items appear in the list (greyed out).

---

### TC-M05 — Delete a menu item

1. Click **Delete** on an item with no orders.
2. Confirm deletion.

**Expected:** Item disappears from the list.

---

### TC-M06 — Empty state

1. Delete all items.

**Expected:** Message "No items — add your first menu item."

---

## Screen: Staff

### TC-S01 — Add a staff member

1. Click **Staff** in the sidebar.
2. Click **+ Add Staff Member**.
3. Enter Name = `Jane`, Role = `Cook`.
4. Click **Save**.

**Expected:** Jane appears in the list with an orange Cook badge.

---

### TC-S02 — Edit a staff member

1. Click **Edit** next to a staff member.
2. Change the role to `Admin`.
3. Click **Save**.

**Expected:** Role badge updates to blue Admin.

---

### TC-S03 — Delete a staff member

1. Click **Delete** next to a staff member.
2. Confirm.

**Expected:** Member removed from the list.

---

### TC-S04 — Role badges

| Role   | Badge color |
|--------|-------------|
| Barman | 🟢 Green    |
| Admin  | 🔵 Blue     |
| Cook   | 🟠 Orange   |

---

## Screen: Stats

### TC-ST01 — View today's stats

1. Click **📊 Stats** in the sidebar.
2. Leave date picker on today's date.

**Expected:** Five metric tiles show correct values. If no orders today: all zeros, items chart is empty, log is empty.

---

### TC-ST02 — Stats with data

1. Open a table, add several different items, close the table.
2. Open another table, add items but leave it open.
3. Go to Stats.

**Expected:**
- "Total Revenue" = sum of all orders.
- "Locked" = sum of orders from the *closed* table only.
- "Running" = sum of orders from the *active* table only.
- Items chart shows all ordered items sorted by revenue descending.
- Orders log shows all order lines in chronological order.

---

### TC-ST03 — Stats for a past date

1. Use the date picker to select yesterday (or any past date with no data).

**Expected:** All metrics show 0, charts and log are empty with an "empty" message.

---

### TC-ST04 — Invalid date (API-level)

```bash
curl "http://localhost:8000/api/v1/stats/daily?date=not-a-date"
```

**Expected:** `400 Bad Request` — `"Invalid date format. Use YYYY-MM-DD."`

---

## API Smoke Tests

These can be run directly from http://localhost:8000/docs or with curl.

| Test | Request | Expected |
|------|---------|----------|
| List items | `GET /api/v1/items/` | 200, array |
| Filter available only | `GET /api/v1/items/?available_only=true` | 200, only available items |
| Create table | `POST /api/v1/tables/` `{"table_name":"T1"}` | 201, table object |
| Close non-existent table | `POST /api/v1/tables/99999/close` | 404 |
| Close already-closed table | `POST /api/v1/tables/{id}/close` twice | 400 second time |
| Add order — item not found | `POST /api/v1/tables/{id}/orders/` `{"item_id":99999,"quantity":1}` | 404 |
| Stats today | `GET /api/v1/stats/daily` | 200, DailyStats object |

---

## Known Limitations (Phase 1)

| Limitation | Notes |
|------------|-------|
| No authentication | All endpoints are open. Anyone on the network can read/write data. Auth is Phase 3. |
| Streamlit text input requires Enter | After typing in a text field, press **Enter** before clicking Save — otherwise the old value is used. This is a Streamlit framework constraint. |
| No real-time updates | The page does not auto-refresh. If another user opens a table, you need to manually reload. WebSockets are Phase 4. |
| Item deletion blocked by orders | The API currently allows deleting items that have orders (no FK constraint enforced at app level). The item name will show as missing in order history. |
| No stock tracking | Ordering an item does not decrement any stock. Stock management is Phase 2. |
| No payment records | Closing a table locks the bill but does not record a payment method. Payments are Phase 6. |

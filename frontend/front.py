import streamlit as st

# Stub methods for data fetching and sending

def get_clients():
    # TODO: implement API call to fetch clients
    return [
        {"id": 1, "name": "Client A"},
        {"id": 2, "name": "Client B"},
    ]


def get_client_orders(client_id):
    # TODO: implement API call to fetch orders for a client
    return [
        {"item": "Item 1", "quantity": 2, "price": 10.0},
        {"item": "Item 2", "quantity": 1, "price": 20.0},
    ]


def add_client(client_data):
    # TODO: implement API call to add a new client
    pass


def add_item(client_id, item_data):
    # TODO: implement API call to add a new order item for a client
    pass

# Callback functions

def new_client_add_item():
    st.session_state.new_client_items.append({"item": "", "quantity": 1, "price": 0.0})


def new_client_save():
    items = []
    for idx in range(len(st.session_state.new_client_items)):
        items.append({
            "item": st.session_state[f"new_item_{idx}_name"],
            "quantity": st.session_state[f"new_item_{idx}_qty"],
            "price": st.session_state[f"new_item_{idx}_price"],
        })
    add_client({"name": st.session_state.new_client_name, "orders": items})
    st.session_state.new_client_modal = False


def new_client_cancel():
    st.session_state.new_client_modal = False


def client_add_item(client_id):
    st.session_state[f"client_{client_id}_new_items"].append({"item": "", "quantity": 1, "price": 0.0})


def client_cancel():
    st.session_state.client_modal = None

# Initialize session state
if "new_client_modal" not in st.session_state:
    st.session_state.new_client_modal = False
if "new_client_items" not in st.session_state:
    st.session_state.new_client_items = []
if "client_modal" not in st.session_state:
    st.session_state.client_modal = None

st.title("Clients")

# 'Add Client' section
st.button("Add client", on_click=lambda: st.session_state.update({"new_client_modal": True, "new_client_items": []}), key="btn_add_client")

if st.session_state.new_client_modal:
    with st.expander("Add Client", expanded=True):
        st.text_input("Client Name", key="new_client_name")
        st.markdown("**Items:**")
        for idx in range(len(st.session_state.new_client_items)):
            col1, col2, col3 = st.columns(3)
            col1.text_input("Item", key=f"new_item_{idx}_name")
            col2.number_input("Quantity", key=f"new_item_{idx}_qty", min_value=1, value=1)
            col3.number_input("Price", key=f"new_item_{idx}_price", min_value=0.0, value=0.0, format="%.2f")
        cols = st.columns(3)
        cols[0].button("Add item", on_click=new_client_add_item, key="new_client_add_item")
        cols[1].button("Save client", on_click=new_client_save, key="new_client_save")
        cols[2].button("Cancel", on_click=new_client_cancel, key="new_client_cancel")

# Display client list
clients = get_clients()
for client in clients:
    st.button(client["name"], on_click=lambda cid=client["id"]: st.session_state.__setitem__('client_modal', cid), key=f"client_btn_{client['id']}")

# 'Client Orders' section
if st.session_state.client_modal is not None:
    client_id = st.session_state.client_modal
    client = next(c for c in clients if c["id"] == client_id)
    orig_key = f"client_{client_id}_orig_orders"
    new_key = f"client_{client_id}_new_items"
    if orig_key not in st.session_state:
        st.session_state[orig_key] = get_client_orders(client_id)
    if new_key not in st.session_state:
        st.session_state[new_key] = []

    with st.expander(f"Orders for {client['name']}", expanded=True):
        st.markdown("**Existing Orders:**")
        for idx, order in enumerate(st.session_state[orig_key]):
            col1, col2, col3 = st.columns(3)
            col1.text_input("Item", value=order["item"], disabled=True, key=f"{orig_key}_item_{idx}")
            col2.text_input("Quantity", value=str(order["quantity"]), disabled=True, key=f"{orig_key}_qty_{idx}")
            col3.text_input("Price", value=f"${order['price']:.2f}", disabled=True, key=f"{orig_key}_price_{idx}")
        st.markdown("**New Items:**")
        for idx in range(len(st.session_state[new_key])):
            col1, col2, col3 = st.columns(3)
            col1.text_input("Item", key=f"{new_key}_name_{idx}")
            col2.number_input("Quantity", min_value=1, value=1, key=f"{new_key}_qty_{idx}")
            col3.number_input("Price", min_value=0.0, value=0.0, format="%.2f", key=f"{new_key}_price_{idx}")
        cols = st.columns(2)
        cols[0].button("Add item", on_click=client_add_item, args=(client_id,), key=f"client_add_item_{client_id}")
        cols[1].button("Close", on_click=client_cancel, key=f"client_close_{client_id}")

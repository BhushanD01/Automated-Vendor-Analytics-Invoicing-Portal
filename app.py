import streamlit as st
import pandas as pd
from utils.db_func import (connect_to_database, get_basic_info, get_info_tables, add_product, get_categories,
get_suppliers, get_all_products, get_product_history, place_reorder,get_pending_reorders, mark_reorder_as_received)

st.sidebar.title("Inventory Management Dashboard")
option = st.sidebar.selectbox("Action Type",("Fetch Basic Information","Perform Operational Tasks"))

st.title("Vendor Analytics & Invoicing Portal")
db = connect_to_database()
cursor = db.cursor(dictionary=True)

# ---------------------------Basic Information Page---------------------------

if option == "Fetch Basic Information":
    st.header("Metrics")
    basic_info = get_basic_info(cursor)
    cols = st.columns(3)
    keys = list(basic_info.keys())

    for i in range(3):
        cols[i].metric(label=keys[i], value = basic_info[keys[i]])

    for i in range(3,6):
        cols[i-3].metric(label=keys[i], value = basic_info[keys[i]])

    st.divider()

    tables = get_info_tables(cursor)

    for label, value in tables.items():
        st.header(label)
        df = pd.DataFrame(value)
        st.dataframe(df)
        st.divider()

# ---------------------------Operational Tasks Page---------------------------

elif option == "Perform Operational Tasks":
    st.header("Operational Tasks")
    selected_task = st.selectbox("Select Task", ("Add New Product", "Product History", "Place Restock Order", "Receive Reorder"))

    if selected_task == "Add New Product":
        st.header("Add New Product")
        categories = get_categories(cursor)
        suppliers = get_suppliers(cursor)

        with st.form("Add Product Form"):
            product_name = st.text_input("Product Name")
            product_category = st.selectbox("Category", categories)
            product_price = st.number_input("Price", min_value=0)
            product_stocks = st.number_input("Stock Quantity", min_value=0, step=5)
            product_level = st.number_input("Reorder Level", min_value=0,step=5)

            supplier_dict = {item["supplier_name"]: item["supplier_id"] for item in suppliers}

            selected_name = st.selectbox(
                "Supplier",
                options=list(supplier_dict.keys())
            )

            backend_supplier_id = supplier_dict[selected_name]

            submit = st.form_submit_button("Add Product")
            if submit:
                if not product_name:
                    st.error("⚠️ Add Product Name")
                    
                else:
                    try:
                        add_product(cursor, db, product_name, product_category, product_price, product_stocks, product_level, backend_supplier_id)
                        st.success(f"🎉 Product {product_name} Added Successfully")

                    except Exception as e:
                        st.error(f"Error Adding Product {e}")


    if selected_task == "Product History":
        st.header("Product History")
        products = get_all_products(cursor)
        product_dict = {product["product_name"]:product["product_id"] for product in products}

        selected_product = st.selectbox(
            "Select Product",
            options=list(product_dict.keys())
        )

        backend_product_id = product_dict[selected_product]

        product_history_info = get_product_history(cursor, backend_product_id)

        if product_history_info:
            df = pd.DataFrame(product_history_info)
            st.dataframe(df)


    if selected_task == "Place Restock Order":
        st.header("Place an Reorder")

        products = get_all_products(cursor)
        product_dict = {product["product_name"]:product["product_id"] for product in products}
    
        selected_product = st.selectbox(
            "Select Product",
            options=list(product_dict.keys())
        )

        backend_product_id = product_dict[selected_product]

        reorder_qty=st.number_input("Reorder Quantity", min_value=1, step=1)

        if st.button("Place Reorder"):
            if not selected_product:
                st.error("⚠️ Please Select an Product")
            elif reorder_qty<=0:
                st.error("Reorder Quantity must be greater than 0")
            else:
                try:
                    place_reorder(cursor, db, backend_product_id, reorder_qty)
                    st.success(f"Order placed for {selected_product} with quantity {reorder_qty}")
                except Exception as e:
                    st.error(f"Error Placing reorder {e}")


    elif selected_task=="Receive Reorder":
        st.header("Mark Reorder as Received")
        pending_reorders= get_pending_reorders(cursor)

        if not pending_reorders:
            st.info("No Pending Orders to Receive")
        else:
            reorder_ids = [r['reorder_id'] for r in pending_reorders]
            reorder_labels=[f"ID {r['reorder_id']} - {r['product_name']}" for r in  pending_reorders]

            selected_label =st.selectbox("Select Reorder to mark as Received", options=reorder_labels)

            if selected_label:
                selected_reorder_id= reorder_ids[reorder_labels.index(selected_label)]

                if st.button("Mark as Received"):
                    try:
                       mark_reorder_as_received(cursor, db, selected_reorder_id)
                       st.success(f"Reorder ID {selected_reorder_id} marked as received")
                    except Exception as e:
                        st.error(f"Error {e}")

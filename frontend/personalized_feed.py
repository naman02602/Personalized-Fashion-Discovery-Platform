import streamlit as st
from sqlalchemy import create_engine
import random
import pinecone


def create_db_connection(db_url):
    engine = create_engine(db_url)
    return engine.connect()


db_url = "mysql+pymysql://root:root123@34.68.249.238/buyer"
connection = create_db_connection(db_url)

pinecone.init(api_key="6e0b7ddc-cec5-4df7-b06f-78a30dde865a", environment="gcp-starter")
index = pinecone.Index(index_name="damg7245-project")


def show_feed(username: str, firstname: str):
    st.write(f"Welcome to the app: {firstname}")
    category = fetch_latest_search(username, connection)
    if category is not None:
        st.write("Recently Viewed Similar Items")
        fetched_results = query_records(category)
        results = select_random_records(fetched_results)
        # st.write(results)
        # Create 3 columns for the metadata of the 3 closest products
        col1, col2, col3 = st.columns(3)

        # Iterate through the matches and display their metadata in separate columns
        for i, match in enumerate(
            results["matches"][:3]
        ):  # Assuming results["matches"] has at least 3 matches
            # Select the appropriate column based on the index
            if i == 0:
                col = col1
            elif i == 1:
                col = col2
            else:
                col = col3

            with col:
                st.write(f"ID: {match['id']}")
                # st.write(f"Score: {match['score']:.4f}")
                if st.button("View Info", key=f"wishlistl_{match['id']}"):
                    metadata = match.get("metadata", None)
                    if metadata:
                        for key, value in metadata.items():
                            # If the value is a list, join it into a string for display
                            if isinstance(value, list):
                                value = ", ".join(value)
                            st.write(f"{key.capitalize()}: {value}")

                            # Store the product_cat of the first most similar item
                            if i == 0 and key == "product_cat":
                                first_product_cat = value

                    else:
                        st.write("No metadata available.")
    else:
        st.write("No search history till now.")

    st.write("Wishlist")
    wishlist = fetch_wishlist(username, connection)
    if wishlist is not None:
        st.write(wishlist)
    else:
        st.write("Add items to your wishlist")


def fetch_latest_search(username, connection):
    try:
        # SQL query to select the latest record
        connection.begin()
        sql = """
        SELECT search_query 
        FROM user_search_history 
        WHERE username = %(username)s 
        ORDER BY search_timestamp DESC 
        LIMIT 1
        """
        result = connection.execute(sql, {"username": username}).fetchone()

        if result:
            return result[0]
        else:
            print("No recent search found for the user.")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def fetch_wishlist(username, connection):
    try:
        # SQL query to select the latest record
        connection.begin()
        sql = """
        SELECT pid 
        FROM user_wishlist 
        WHERE username = %(username)s 
        ORDER BY search_timestamp DESC 
        """
        result = connection.execute(sql, {"username": username}).fetchall()

        if result:
            return result
        else:
            print("No wishlist found for the user.")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None


# Function to query Pinecone and fetch records based on a filter
def query_records(product_cat, top_k=10):
    random_vec = [0.1] * 512
    results = index.query(
        vector=random_vec,
        filter={"product_cat": {"$eq": product_cat}},
        top_k=top_k,
        include_metadata=True,
    )
    return results


# Function to randomly select 2 records from the results
def select_random_records(results):
    matches = results.get("matches", [])
    # Randomly select 3 matches if there are enough, else return all matches
    selected_matches = random.sample(matches, 3) if len(matches) > 3 else matches

    # Return the results in a dictionary with a key 'matches'
    return {"matches": selected_matches}

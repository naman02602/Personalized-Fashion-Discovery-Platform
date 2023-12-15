import streamlit as st
from sqlalchemy import create_engine
import random
import pinecone
import boto3
from PIL import Image
import io


def create_db_connection(db_url):
    engine = create_engine(db_url)
    return engine.connect()


db_url = os.getenv("DATABASE_URL")
connection = create_db_connection(db_url)

pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment="gcp-starter")
index = pinecone.Index(index_name="damg7245-project")


def show_feed(username: str, firstname: str):
    st.write(f"Welcome to the app: {firstname}")
    category = fetch_latest_search(username, connection)

    s3_client = boto3.client(
        service_name="s3",
        region_name="us-east-1",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    if category is not None:
        st.write("Recently Viewed Similar Items")
        index = pinecone.Index(index_name="damg7245-project")
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
                # st.write(f"ID: {match['id']}")
                s3_bucket = "damg7245-4"  # Replace with your actual S3 bucket name
                pid = match["id"]
                try:
                    image = get_image_from_s3(s3_client, s3_bucket, pid)
                    st.image(image, caption=f"ID: {pid}")
                except Exception as e:
                    st.write("Error loading image:", e)
                # st.write(f"Score: {match['score']:.4f}")
                # if st.button("View Info", key=f"wishlistl_{match['id']}"):
                #     metadata = match.get("metadata", None)
                #     if metadata:
                #         for key, value in metadata.items():
                #             # If the value is a list, join it into a string for display
                #             if isinstance(value, list):
                #                 value = ", ".join(value)
                #             st.write(f"{key.capitalize()}: {value}")

                #             # Store the product_cat of the first most similar item
                #             if i == 0 and key == "product_cat":
                #                 first_product_cat = value

                #     else:
                #         st.write("No metadata available.")
    else:
        st.write("No search history till now.")

    st.markdown("""---""")
    # st.write("Wishlist")
    # wishlist = fetch_wishlist(username)
    # if wishlist:
    #     for item in wishlist:
    #         pid = item[0]  # Assuming the result is a tuple with PID at index 0
    #         try:
    #             image = get_image_from_s3(s3_client, "damg7245-4", pid)
    #             st.image(image, caption=f"Product ID: {pid}")
    #         except Exception as e:
    #             st.write(f"Error loading image for Product ID {pid}: {e}")
    # else:
    #     st.write("Your wishlist is currently empty.")
    st.write("Your Wishlist:")
    wishlist_items = fetch_wishlist(username)
    if wishlist_items:
        for item in wishlist_items:
            pid = item[0]  # Assuming the result is a tuple with PID at index 0

            # Create two columns: one for PID and one for the image
            col1, col2 = st.columns([1, 3])  # Adjust the ratio as needed

            with col1:
                st.write(pid)

            with col2:
                try:
                    image = get_image_from_s3(s3_client, "damg7245-4", pid)
                    custom_size = (200, 200)
                    resized_image = image.resize(custom_size)
                    st.image(resized_image)  # Adjust width as needed
                except Exception as e:
                    st.write(f"Error loading image for Product ID {pid}: {e}")
    else:
        st.write("Your wishlist is currently empty.")


def fetch_latest_search(username, connection):
    connection = create_db_connection(db_url)
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
    finally:
        connection.close()


def fetch_wishlist(username):
    connection = create_db_connection(db_url)
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
    finally:
        connection.close()


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


# Function to fetch image from S3
def get_image_from_s3(s3_client, bucket_name, pid, target_size=(300, 300)):
    # s3_client = boto3.client('s3')
    key = f"Images/{pid}.jpg"  # Construct the key
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    image = Image.open(io.BytesIO(response["Body"].read()))
    image = image.resize(target_size)
    return image

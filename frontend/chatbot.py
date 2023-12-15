import streamlit as st
import pymysql
from sqlalchemy import create_engine
from PIL import Image
import io
from transformers import CLIPProcessor, CLIPModel
from transformers import CLIPTokenizerFast, CLIPProcessor, CLIPModel
import pinecone
import boto3

# model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
# processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


def create_db_connection(db_url):
    engine = create_engine(db_url)
    return engine.connect()


db_url = "mysql+pymysql://root:root123@34.68.249.238/buyer"
connection = create_db_connection(db_url)
pinecone.init(api_key="6e0b7ddc-cec5-4df7-b06f-78a30dde865a", environment="gcp-starter")
index = pinecone.Index(index_name="damg7245-project")


def search_similar_items(embedding, top_k=9):
    # Convert ndarray embedding to a list for Pinecone
    embedding_list = embedding.tolist()
    # pinecone.init(api_key="6e0b7ddc-cec5-4df7-b06f-78a30dde865a", environment="gcp-starter")
    index = pinecone.Index(index_name="damg7245-project")
    # Query Pinecone for similar items
    query_results = index.query(embedding_list, top_k=top_k, include_metadata=True)
    # print(query_results)
    return query_results


def show_chatbot(username: str):
    # Handle file upload
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

    s3_client = boto3.client(
        service_name="s3",
        region_name="us-east-1",
        aws_access_key_id="AKIA5IE7JCG4E76C7THC",
        aws_secret_access_key="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",
    )

    # If an image is uploaded, display it
    if uploaded_file is not None:
        # To read image as bytes
        bytes_data = uploaded_file.getvalue()
        st.write("Uploaded image:")

        # To convert to a PIL Image object (if needed)
        image = Image.open(io.BytesIO(bytes_data))
        custom_size = (600, 600)
        resized_image = image.resize(custom_size)
        # Use columns to center the image
        left_column, center_column, right_column = st.columns(
            [1, 2, 1]
        )  # Adjust the ratio as necessary

        # Display the image in the center column
        with center_column:
            st.image(resized_image, caption="Uploaded Image")

        # st.image(resized_image, caption="Uploaded Image")

        embedding = get_image_embedding(image)
        # print(embedding)

        # Perform search in Pinecone
        results = search_similar_items(embedding)
        # print(results)

        # Check for product category outside the button click
        first_product_cat = None

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
            # col = [col1, col2, col3][i]
            with col:
                st.write(f"ID: {match['id']}")
                # st.write(f"Score: {match['score']:.4f}")
                # -------------------------------------------------------------------------------------------->adding code block to get images
                s3_bucket = "damg7245-4"  # Replace with your actual S3 bucket name
                pid = match["id"]
                try:
                    image = get_image_from_s3(s3_client, s3_bucket, pid)
                    st.image(image, caption=f"Image for ID: {pid}")
                except Exception as e:
                    st.write("Error loading image:", e)
                # -------------------------------------------------------------------------------------------->end code block to get images
                metadata = match.get("metadata", None)
                if metadata:
                    for key, value in metadata.items():
                        # Store the product_cat of the first most similar item
                        if i == 0 and key == "product_cat":
                            first_product_cat = value
                            break  # Break out of the loop once the first product_cat is found

                if st.button("View Info", key=f"wishlistk_{match['id']}"):
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
                            print(first_product_cat)
                    else:
                        st.write("No metadata available.")

                    # Add 'Add to Wishlist' button with a unique key
                if st.button("Add to Wishlist", key=f"wishlist_{match['id']}"):
                    pid = match["id"]
                    record_wishlist(username, pid)
                    st.write(f"Added ID: {match['id']} to wishlist")
                    st.experimental_rerun()
        left_spacer, center_column, right_spacer = st.columns([1, 1, 1])

        # Use the center column to display the button
        with center_column:
            if st.button(":arrow_down_small: View More Products :arrow_down_small: "):
                show_more = True
            else:
                show_more = False

        # If the button was clicked, display the next 3 products
        if show_more:
            # Create new columns for the additional images
            col4, col5, col6 = st.columns(3)

            # Iterate through the matches and display their metadata in separate columns
            for i, match in enumerate(
                results["matches"][3:6]
            ):  # Assuming results["matches"] has at least 3 matches
                # Select the appropriate column based on the index
                if i == 0:
                    col = col4
                elif i == 1:
                    col = col5
                else:
                    col = col6
                # col = [col1, col2, col3][i]
                with col:
                    st.write(f"ID: {match['id']}")
                    # st.write(f"Score: {match['score']:.4f}")
                    # -------------------------------------------------------------------------------------------->adding code block to get images
                    s3_bucket = "damg7245-4"  # Replace with your actual S3 bucket name
                    pid = match["id"]
                    try:
                        image = get_image_from_s3(s3_client, s3_bucket, pid)
                        st.image(image, caption=f"Image for ID: {pid}")
                    except Exception as e:
                        st.write("Error loading image:", e)
                    # -------------------------------------------------------------------------------------------->end code block to get images
                    if st.button("View Info", key=f"wishlistk_{match['id']}"):
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

                        # Add 'Add to Wishlist' button with a unique key
                    if st.button("Add to Wishlist", key=f"wishlistt_{match['id']}"):
                        pid = match["id"]
                        record_wishlist(username, pid)
                        st.write(f"Added ID: {match['id']} to wishlist")
                        st.experimental_rerun()

        record_search(username, first_product_cat)


def record_wishlist(username, pid):
    transaction = None  # Initialize transaction to None
    connection = create_db_connection(db_url)
    try:
        transaction = connection.begin()
        # SQL query to insert the record
        sql = "INSERT INTO user_wishlist (username, pid) VALUES (%(username)s, %(pid)s)"
        connection.execute(sql, {"username": username, "pid": pid})
        transaction.commit()
    except Exception as e:
        print(f"Error: {e}")
        if transaction:
            transaction.rollback()
    finally:
        connection.close()


def record_search(username, query):
    transaction = None  # Initialize transaction to None
    connection = create_db_connection(db_url)
    try:
        transaction = connection.begin()
        # SQL query to insert the record
        sql = "INSERT INTO user_search_history (username, search_query) VALUES (%(username)s, %(query)s)"
        connection.execute(sql, {"username": username, "query": query})
        transaction.commit()
    except Exception as e:
        print(f"Error: {e}")
        if transaction:
            transaction.rollback()
    finally:
        connection.close()


def get_image_embedding(image):
    # Process and resize the single image
    device = "cpu"
    model_id = "openai/clip-vit-base-patch32"

    # we initialize a tokenizer, image processor, and the model itself
    tokenizer = CLIPTokenizerFast.from_pretrained(model_id)
    processor = CLIPProcessor.from_pretrained(model_id)
    model = CLIPModel.from_pretrained(model_id).to(device)
    batch = processor(text=None, images=[image], return_tensors="pt", padding=True)[
        "pixel_values"
    ].to(device)

    # Get image embedding
    embedding = model.get_image_features(pixel_values=batch)

    # Convert to numpy array and return
    embedding = embedding.squeeze(0).cpu().detach().numpy()
    return embedding


# Function to fetch image from S3
def get_image_from_s3(s3_client, bucket_name, pid, target_size=(300, 300)):
    # s3_client = boto3.client('s3')
    key = f"Images/{pid}.jpg"  # Construct the key
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    image = Image.open(io.BytesIO(response["Body"].read()))
    image = image.resize(target_size)
    return image

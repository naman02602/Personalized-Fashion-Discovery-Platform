import streamlit as st
import pymysql
from sqlalchemy import create_engine
from PIL import Image
import io
from transformers import CLIPProcessor, CLIPModel

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


def create_db_connection(db_url):
    engine = create_engine(db_url)
    return engine.connect()


db_url = "mysql+pymysql://root:root123@34.68.249.238/buyer"
connection = create_db_connection(db_url)


def show_chatbot(username: str):
    st.write(f"Chatbot page coming soon for {username}")
    search_query = st.text_input("Search for products")
    if st.button("Search"):
        # Record the search in the database
        record_search(username, search_query, connection)
    # Inject custom styles with st.markdown

    # Handle file upload
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

    # If an image is uploaded, display it
    if uploaded_file is not None:
        # To read image as bytes
        bytes_data = uploaded_file.getvalue()
        st.write("Uploaded image:")

        # To convert to a PIL Image object (if needed)
        image = Image.open(io.BytesIO(bytes_data))
        st.image(image, caption="Uploaded Image", use_column_width=True)


def record_search(username, query, connection):
    try:
        with connection.begin() as transaction:
            # SQL query to insert the record
            sql = "INSERT INTO user_search_history (username, search_query) VALUES (%(username)s, %(query)s)"
            connection.execute(sql, {"username": username, "query": query})
            transaction.commit()
    except Exception as e:
        print(f"Error: {e}")
        transaction.rollback()
    connection.close()

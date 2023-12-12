import streamlit as st
import requests
import boto3
from streamlit_aws import upload_file_to_s3
import pandas as pd
import io

from chatbot import show_chatbot
from catalog_w_embedding import generate_csv_embedding

FASTAPI_SERVICE_URL = "http://127.0.0.1:8000"


def logout():
    st.session_state["logged_in"] = False
    st.session_state["role"] = None


def login_form():
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if username and password:
        if st.button("Login"):
            login_data = {"username": username, "password": password}
            response = requests.post(f"{FASTAPI_SERVICE_URL}/login", data=login_data)

            if response.status_code == 200:
                token_data = response.json()
                st.session_state["token"] = token_data["access_token"]
                st.session_state["logged_in"] = True
                st.session_state["username"] = token_data.get("username")
                st.session_state["firstname"] = token_data.get("firstname")
                st.session_state["role"] = "Buyer"
                st.success("Login successful! Redirecting...")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials. Please try again.")


def signup_form():
    st.title("Signup Page")

    username = st.text_input("Username", key="signup_username")
    firstname = st.text_input("First Name", key="signup_firstname")
    lastname = st.text_input("Last Name", key="signup_lastname")
    email_id = st.text_input("Email ID", key="signup_email")
    phone_number = st.text_input("Phone Number", key="signup_phone")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input(
        "Confirm Password", type="password", key="signup_confirm_password"
    )

    if confirm_password and password != confirm_password:
        st.warning("Passwords do not match.")
    elif confirm_password and password == confirm_password:
        st.success("Passwords match.")

    if st.button("Signup"):
        if password == confirm_password:
            url = f"{FASTAPI_SERVICE_URL}/signup"
            signup_data = {
                "username": username,
                "firstname": firstname,
                "lastname": lastname,
                "email_id": email_id,
                "phone_number": phone_number,
                "password": password,
            }
            response = requests.post(url, json=signup_data)

            if response.status_code == 200:
                st.success(f"User {username} created successfully!")
            else:
                st.error(f"An error occurred: {response.json()}")
        else:
            st.error("Cannot signup. Passwords do not match.")


def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["role"] = None

    st.title("DAMG-7245 Final Project")

    if st.session_state["logged_in"]:
        if st.sidebar.button("Logout"):
            logout()
            st.experimental_rerun()
        st.title("Welcome to the Buyer Home Page!")  # Home page after login
        tab1, tab2 = st.tabs(["Personalized feed", "Chatbot"])
        with tab1:
            show_wishlist(st.session_state["username"], st.session_state["firstname"])

        with tab2:
            show_chatbot(st.session_state["username"])

    else:
        user_role = st.sidebar.radio(
            "Select your role:", ("Buyer", "Store Owner/Catalog Manager")
        )

        if user_role == "Buyer":
            tab1, tab2 = st.tabs(["Login", "Sign Up"])
            with tab1:
                login_form()
            with tab2:
                signup_form()

        if user_role == "Store Owner/Catalog Manager":
            logout()
            tab1, tab2 = st.tabs(["Update Catalog", "Generate Catalog w Embeddings"])
            with tab1:
                s3_client = boto3.client(
                    service_name="s3",
                    region_name="us-east-1",
                    aws_access_key_id="AKIA37JWDCIQ6ZID6PVM",
                    aws_secret_access_key="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",
                )

                st.title("Update Product Catalog (via S3)")
                bucket_name = "damg7245-asng-team4"  # Hardcoded bucket name
                csv_folder_name = "product_catalog"
                image_folder_name = "product_images"

                uploaded_csv = st.file_uploader("Choose a CSV file", type="csv")
                uploaded_files = st.file_uploader(
                    "Choose images to upload",
                    accept_multiple_files=True,
                    type=["png", "jpg", "jpeg"],
                )

                if st.button("Validate and Upload to S3"):
                    if uploaded_csv is not None and uploaded_files:
                        csv_valid, csv_message = validate_csv(uploaded_csv)
                        st.write(csv_message)
                        try:
                            df = pd.read_csv(uploaded_csv)
                            print(len(uploaded_files))
                            print(len(df))
                            if len(df) != len(uploaded_files):
                                st.error(
                                    "The number of records in the CSV does not match the number of uploaded images."
                                )
                            else:
                                success = upload_file_to_s3(
                                    s3_client,
                                    bucket_name,
                                    uploaded_csv,
                                    csv_folder_name,
                                    uploaded_csv.name,
                                )
                                if success:
                                    print(
                                        f"File {uploaded_csv.name} successfully uploaded to {bucket_name}/{csv_folder_name}"
                                    )

                                else:
                                    st.error("Failed to upload file to S3.")

                                if uploaded_files:
                                    for uploaded_file in uploaded_files:
                                        # Show details of the file
                                        st.write("Filename:", uploaded_file.name)
                                        # Upload file to S3
                                        success = upload_file_to_s3(
                                            s3_client,
                                            bucket_name,
                                            uploaded_file,
                                            image_folder_name,
                                            uploaded_file.name,
                                        )
                                        if success:
                                            print(
                                                f"Files successfully uploaded to {bucket_name}/{image_folder_name}"
                                            )
                                        else:
                                            st.error(
                                                f"Failed to upload file {uploaded_file.name} to S3."
                                            )

                                # Image upload logic for each file in uploaded_files
                                st.success("Files successfully uploaded to S3.")
                        except Exception as e:
                            st.error(f"Error processing CSV file: {e}")
                    else:
                        st.warning("Please upload both a CSV file and images.")

            with tab2:
                st.write("Coming Soon")
                # st.title("Generate Image Embeddings for the new products")
                # bucket_name = "damg7245-asng-team4"  # Hardcoded bucket name
                # csv_folder_name = "product_catalog"
                # image_folder_name = "product_images"

                # uploaded_csv = st.file_uploader(
                #     "Choose a CSV file", type="csv", key="uploader_bt_2"
                # )
                # df_without_embedding = pd.read_csv(uploaded_csv)
                # df_w_embeddings = generate_csv_embedding(df_without_embedding)
                # csv_e = df_w_embeddings.to_csv(index=False)

                # with open("temp_file.csv", "w") as file:
                #     file.write(csv_e)

                # # Streamlit download button
                # st.download_button(
                #     label="Download CSV",
                #     data=csv_e,
                #     file_name="data.csv",
                #     mime="text/csv",
                # )


def validate_csv(uploaded_csv):
    stringio = io.StringIO(uploaded_csv.getvalue().decode("utf-8"))
    df = pd.read_csv(stringio)

    required_columns = {
        "asin",
        "Title",
        "MainImage",
        "Rating",
        "NumberOfReviews",
        "Price",
        "AvailableSizes",
        "AvailableColors",
        "BulletPoints",
        "SellerRank",
        "ProductCat",
    }

    if not required_columns.issubset(df.columns):
        return False, "Missing required columns in CSV."
    return True, "CSV validation successful."


def show_wishlist(username: str, firstname: str):
    st.write(f"Welcome to the app: {firstname}")


if __name__ == "__main__":
    main()

import streamlit as st
import requests
import boto3
from streamlit_aws import upload_file_to_s3
import pandas as pd
import io
from sqlalchemy import create_engine
from chatbot import show_chatbot
from personalized_feed import show_feed
import pinecone
from botocore.exceptions import ClientError
from testt import main as test_main


FASTAPI_SERVICE_URL = "http://127.0.0.1:8000"

pinecone.init(
    api_key="6e0b7ddc-cec5-4df7-b06f-78a30dde865a",
    environment="gcp-starter",
)
index = pinecone.Index(index_name="damg7245-project")


def create_db_connection(db_url):
    engine = create_engine(db_url)
    return engine.connect()


db_url = "mysql+pymysql://root:root123@34.68.249.238/buyer"
connection = create_db_connection(db_url)


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
        tab1, tab2, tab3 = st.tabs(["Image Search", "Chatbot", "Personalized Feed"])

        with tab1:
            show_chatbot(st.session_state["username"])

        with tab2:
            test_main()

        with tab3:
            show_feed(st.session_state["username"], st.session_state["firstname"])

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
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            tab1, tab2, tab3 = st.tabs(
                [
                    "Catalog Management(add/update)",
                    "Delete Product",
                    "Templates and Instructions",
                ]
            )
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
                    if username == "master" and password == "root":
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
                    else:
                        st.error("Unauthorised attempt to access catalog")
            with tab2:
                st.write("Delete Product from Catalog(Pinecone)")

                product_ids = st.text_input("Enter Product IDs (separated by commas):")
                if not product_ids:
                    # Display a warning message
                    st.warning("Please enter Product ID to continue.")
                    # Disable further actions
                    st.stop()
                else:
                    # Continue with the rest of your code
                    # For example, if you have a button to delete products:
                    if st.button("Delete Products"):
                        success, message = delete_products(product_ids)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                delete_images_from_s3("damg7245-4", product_ids)

            with tab3:
                st.write("Coming Soon")
                # Your modified Google Drive direct download link
                google_drive_link = "https://drive.google.com/uc?export=download&id=1U7626kb6D__vwR-gOffo1GBdOj0JpmYJ"

                # Button in Streamlit
                if st.button("Download template CSV File"):
                    st.markdown(
                        f"[Click here to download the template]({google_drive_link})",
                        unsafe_allow_html=True,
                    )


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


def delete_products(product_ids):
    delete_product_list = [pid.strip() for pid in product_ids.split(",") if pid.strip()]
    print("Product IDs to delete:", delete_product_list)

    if not delete_product_list:
        return False, "No product IDs provided."

    try:
        # Perform the delete operation
        response = index.delete(ids=delete_product_list)
        # print("Delete response:", response)
        if response == {}:
            return True, "Deletion was successful."

        # Here you might need to check the response structure to confirm deletion
        else:
            return False, "Deletion was not successful."
    except Exception as e:
        return False, f"Error in deletion: {e}"


def delete_images_from_s3(bucket_name, product_ids_str):
    # Initialize the S3 client
    s3_client = boto3.client(
        service_name="s3",
        region_name="us-east-1",
        aws_access_key_id="AKIA5IE7JCG4E76C7THC",
        aws_secret_access_key="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",
    )

    # Split the input string by commas and strip whitespace
    product_ids = [pid.strip() for pid in product_ids_str.split(",") if pid.strip()]

    # Store results
    delete_results = {"success": [], "failed": []}

    # Iterate over the product IDs and delete each corresponding image
    for pid in product_ids:
        image_key = f"{pid}.jpg"  # Construct the key for each image

        try:
            # Perform the delete operation
            s3_client.delete_object(Bucket=bucket_name, Key=image_key)
            print(f"Successfully deleted '{image_key}' from '{bucket_name}'.")
            delete_results["success"].append(image_key)
        except ClientError as e:
            error_message = e.response["Error"]["Message"]
            print(f"Failed to delete '{image_key}': {error_message}")
            delete_results["failed"].append((image_key, error_message))
        except Exception as e:
            print(f"An error occurred: {e}")
            delete_results["failed"].append((image_key, str(e)))

    return delete_results


if __name__ == "__main__":
    main()

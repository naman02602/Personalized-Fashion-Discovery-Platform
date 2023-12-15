from datetime import datetime, timedelta
from airflow import DAG
from airflow.models import Connection
from airflow import settings
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.utils.context import Context
import pandas as pd
from io import BytesIO
import boto3
from PIL import Image
from io import BytesIO
import os
from tqdm import tqdm
from transformers import CLIPTokenizerFast, CLIPProcessor, CLIPModel
import torch
import pinecone
from email.message import EmailMessage
import ssl
import smtplib
from airflow.models import Variable


class S3CsvFileSensor(S3KeySensor):
    def poke(self, context):
        hook = S3Hook(aws_conn_id=self.aws_conn_id)

        # List all files in the specified bucket and prefix
        files = hook.list_keys(bucket_name=self.bucket_name, prefix=self.bucket_key)

        for file in files:
            if file.endswith(".csv"):
                self.log.info(f"Detected CSV file: {file}")
                if isinstance(context, Context):
                    context["ti"].xcom_push(key="file_name", value=file)
                return True

        return False


def get_image_embeddings(**kwargs):
    ti = kwargs["ti"]
    device = "cpu"
    model_id = "openai/clip-vit-base-patch32"

    # we initialize a tokenizer, image processor, and the model itself
    tokenizer = CLIPTokenizerFast.from_pretrained(model_id)
    processor = CLIPProcessor.from_pretrained(model_id)
    model = CLIPModel.from_pretrained(model_id).to(device)

    # Function to get images from S3 bucket
    def get_images_from_s3_bucket(bucket_name, folder_prefix):
        s3_hook = S3Hook(aws_conn_id="my_aws_conn")
        s3_client = s3_hook.get_conn()

        # List all objects in the specified folder
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)

        # Extract image file paths
        image_paths = [
            obj["Key"]
            for obj in response.get("Contents", [])
            if obj["Key"].endswith((".jpg", ".jpeg", ".png"))
        ]

        return s3_client, image_paths

    # Replace these with your actual bucket name and image folder path
    bucket_name = "damg7245-4"  # Your S3 bucket name
    folder_prefix = "product_images/"  # Your folder prefix

    # Get S3 client and image list
    s3_client, s3_images = get_images_from_s3_bucket(bucket_name, folder_prefix)

    embeddings_dict = {}

    batch_size = 16  # Set your batch size

    if s3_images:
        for i in tqdm(range(0, len(s3_images), batch_size)):
            batch_paths = s3_images[i : i + batch_size]
            batch_images = []

            for path in batch_paths:
                try:
                    response = s3_client.get_object(Bucket=bucket_name, Key=path)
                    image_bytes = response["Body"].read()
                    image = Image.open(BytesIO(image_bytes)).convert("RGB")
                    batch_images.append(image)
                except Exception as e:
                    print(f"Error processing image {path}: {e}")
                    continue

            # Process and resize images
            batch = processor(
                text=None, images=batch_images, return_tensors="pt", padding=True
            )["pixel_values"].to(device)

            # Get image embeddings
            batch_emb = model.get_image_features(pixel_values=batch)

            # Convert to numpy array
            batch_emb = batch_emb.squeeze(0)
            batch_emb = batch_emb.cpu().detach().numpy()

            # Store embeddings in dictionary
            for path, emb in zip(batch_paths, batch_emb):
                file_name = os.path.basename(path).split(".")[0]
                embeddings_dict[file_name] = emb.tolist()

    # Push the embeddings dictionary to XCom for use in subsequent tasks
    ti.xcom_push(key="embeddings_dict", value=embeddings_dict)


def process_csv_file(**kwargs):
    ti = kwargs["ti"]
    file_name = ti.xcom_pull(task_ids="check_s3_for_csv_file", key="file_name")
    print(f"CSV file detected in S3 bucket: {file_name}. Processing the file...")


def read_csv_and_get_embeddings(**kwargs):
    ti = kwargs["ti"]
    file_name = ti.xcom_pull(task_ids="check_s3_for_csv_file", key="file_name")
    embeddings_dict = ti.xcom_pull(
        task_ids="get_image_embeddings", key="embeddings_dict"
    )

    # Initialize the S3 hook
    s3_hook = S3Hook(aws_conn_id="my_aws_conn")

    # Read the CSV file from S3 into a pandas DataFrame
    csv_buffer = BytesIO()
    s3_hook.get_key(file_name, bucket_name="damg7245-4").download_fileobj(
        csv_buffer
    )
    csv_buffer.seek(0)  # Reset buffer pointer
    csv_df = pd.read_csv(csv_buffer)

    idf = pd.DataFrame(list(embeddings_dict.items()), columns=["asin", "img_embedding"])
    csv_df["Rating"] = csv_df["Rating"].astype("str")

    edf = csv_df.merge(idf, on="asin", how="outer")

    # Push the DataFrame and embeddings dictionary to XCom
    ti.xcom_push(key="e_df", value=edf)
    # ti.xcom_push(key="embeddings_dict", value=embeddings_dict)

    print(
        f"CSV file {file_name} read and DataFrame created. Embeddings dictionary pulled."
    )


def insert_vectors_in_batches(**kwargs):
    # pinecone_api_key = os.environ["PINECONE_API_KEY"]
    pinecone_api_key = Variable.get('pinecone_api_key')

    pinecone.init(api_key=pinecone_api_key, environment="gcp-starter")
    index = pinecone.Index(index_name="damg7245-project")
    ti = kwargs["ti"]
    df = ti.xcom_pull(task_ids="read_csv_and_get_embeddings", key="e_df")

    batch_size = 100  # Set the batch size
    total_vectors = len(df)

    for start_idx in range(0, total_vectors, batch_size):
        end_idx = start_idx + batch_size
        batch_df = df.iloc[start_idx:end_idx]

        meta = [
            {
                "title": x[0],
                "rating": x[1],
                "review": x[2],
                "size": x[3],
                "color": x[4],
                "product_cat": x[5],
            }
            for x in zip(
                batch_df["Title"],
                batch_df["Rating"],
                batch_df["NumberOfReviews"],
                batch_df["AvailableSizes"],
                batch_df["AvailableColors"],
                batch_df["ProductCat"],
            )
        ]

        try:
            index_status = index.upsert(
                vectors=zip(batch_df["asin"], batch_df["img_embedding"], meta)
            )
        except Exception as e:
            continue


def convert_csv_to_parquet(**kwargs):
    ti = kwargs["ti"]
    file_name = ti.xcom_pull(task_ids="check_s3_for_csv_file", key="file_name")

    # Initialize the S3 hook
    s3_hook = S3Hook(aws_conn_id="my_aws_conn")

    # Define the path for the Parquet file
    parquet_file_name = file_name.replace(".csv", ".parquet")
    parquet_file_path = f"processed_csv_files/{parquet_file_name}"

    # Check if the Parquet file already exists
    if not s3_hook.check_for_key(parquet_file_path, bucket_name="damg7245-4"):
        # Read the CSV file from S3 into a pandas DataFrame
        csv_buffer = BytesIO()
        s3_hook.get_key(file_name, bucket_name="damg7245-4").download_fileobj(
            csv_buffer
        )
        csv_buffer.seek(0)  # Reset buffer pointer
        csv_file = pd.read_csv(csv_buffer)

        # Convert the DataFrame to a Parquet file
        parquet_buffer = BytesIO()
        csv_file.to_parquet(parquet_buffer, index=False)
        parquet_buffer.seek(0)  # Reset buffer pointer

        # Upload the Parquet file to S3
        s3_hook.load_file_obj(
            parquet_buffer, parquet_file_path, bucket_name="damg7245-4"
        )
        print(f"Uploaded {parquet_file_name} to {parquet_file_path}")
    else:
        print(f"Parquet file {parquet_file_name} already exists. Skipping upload.")


def delete_csv_file(**kwargs):
    ti = kwargs["ti"]
    file_name = ti.xcom_pull(task_ids="check_s3_for_csv_file", key="file_name")

    # Initialize the S3 hook
    s3_hook = S3Hook(aws_conn_id="my_aws_conn")

    # Delete the file
    s3_hook.delete_objects(bucket="damg7245-4", keys=[file_name])
    print(f"Deleted {file_name} from S3 bucket")

def send_email_functionality():
    # Email sender details
    email_sender = 'jagruti190600@gmail.com'
    email_password = Variable.get("EMAIL_APP_PASSWORD")

    # Email receiver details
    email_receiver = 'jagruti1906@gmail.com'

    # Defining the subject
    subject = 'Catalog Successfully Updated'

    # Getting the latest date and time
    time = datetime.datetime.now()

    # Defining the body of the mail
    body = f"""
    Hello,\n
    I hope this message finds you well. I wanted to inform you that the images you recently uploaded have been successfully added to your catalog at {time}. You can view them to ensure everything looks accurate.
    """

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context = context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())



default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# AWS Connection
conn_id = "my_aws_conn"
conn_type = "s3"
login = Variable.get("AWS_ACCESS_KEY_ID")
password = Variable.get("AWS_SECRET_ACCESS_KEY")
session = settings.Session()
new_conn = Connection(
    conn_id=conn_id, conn_type=conn_type, login=login, password=password
)
if not (session.query(Connection).filter(Connection.conn_id == conn_id).first()):
    session.add(new_conn)
    session.commit()

dag = DAG(
    "s3_csv_file_detection_dag",
    default_args=default_args,
    schedule_interval=timedelta(minutes=5),
)

s3_sensor = S3CsvFileSensor(
    task_id="check_s3_for_csv_file",
    bucket_key="product_catalog/",
    bucket_name="damg7245-4",
    aws_conn_id=conn_id,
    # timeout=18 * 60 * 60,
    poke_interval=120 * 60,
    wildcard_match=True,
    dag=dag,
)

get_embeddings = PythonOperator(
    task_id="get_image_embeddings",
    python_callable=get_image_embeddings,
    provide_context=True,
    dag=dag,
)


file_processor = PythonOperator(
    task_id="process_csv_file",
    python_callable=process_csv_file,
    provide_context=True,
    dag=dag,
)


read_csv_embeddings = PythonOperator(
    task_id="read_csv_and_get_embeddings",
    python_callable=read_csv_and_get_embeddings,
    provide_context=True,
    dag=dag,
)

insert_vectors_task = PythonOperator(
    task_id="insert_vectors_in_batches",
    python_callable=insert_vectors_in_batches,
    provide_context=True,
    dag=dag,
)


convert_to_parquet = PythonOperator(
    task_id="convert_csv_to_parquet",
    python_callable=convert_csv_to_parquet,
    provide_context=True,
    dag=dag,
)

delete_csv = PythonOperator(
    task_id="delete_csv_file",
    python_callable=delete_csv_file,
    provide_context=True,
    dag=dag,
)

email_functionality = PythonOperator(
    task_id="send_email_to_vendor",
    python_callable=send_email_functionality,
    provide_context=True,
    dag=dag,
)

(
    s3_sensor
    >> get_embeddings
    >> file_processor
    >> read_csv_embeddings
    >> insert_vectors_task
    >> convert_to_parquet
    >> delete_csv
    >> email_functionality
)

from transformers import CLIPTokenizerFast, CLIPProcessor, CLIPModel
import torch
import pandas as pd
import os
import numpy as np
from tqdm.auto import tqdm
from PIL import Image
import boto3
from io import BytesIO
from tqdm import tqdm


device = (
    "cuda"
    if torch.cuda.is_available()
    else ("mps" if torch.backends.mps.is_available() else "cpu")
)
model_id = "openai/clip-vit-base-patch32"

# we initialize a tokenizer, image processor, and the model itself
tokenizer = CLIPTokenizerFast.from_pretrained(model_id)
processor = CLIPProcessor.from_pretrained(model_id)
model = CLIPModel.from_pretrained(model_id).to(device)


def generate_csv_embedding(df):
    batch_size = 16
    print("Entered generate_csv_embedding function")
    # print(df)
    embeddings_dict = process_and_get_embeddings_from_s3(
        model, processor, batch_size, device
    )
    idf = pd.DataFrame(list(embeddings_dict.items()), columns=["asin", "img_embedding"])
    print(idf)
    edf = df.merge(idf, on="asin", how="outer")
    # print(edf)
    return edf


def get_images_from_s3_bucket(
    bucket_name="damg7245-4", folder_prefix="product_images/"
):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    # List all objects in the specified folder
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)
    print(response)
    # Extract image file paths
    image_paths = [
        obj["Key"]
        for obj in response.get("Contents", [])
        if obj["Key"].endswith((".jpg", ".jpeg", ".png"))
    ]

    return s3, image_paths


def process_and_get_embeddings_from_s3(model, processor, batch_size, device):
    # Get all images from the specified S3 bucket's folder
    s3, s3_images = get_images_from_s3_bucket()

    embeddings_dict = {}

    for i in tqdm(range(0, len(s3_images), batch_size)):
        # select batch of image file paths
        batch_paths = s3_images[i : i + batch_size]

        # load images using PIL
        batch_images = []
        for path in batch_paths:
            response = s3.get_object(Bucket="damg7245-4", Key=path)
            image_bytes = response["Body"].read()
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            batch_images.append(image)

        # process and resize
        batch = processor(
            text=None, images=batch_images, return_tensors="pt", padding=True
        )["pixel_values"].to(device)

        # get image embeddings
        batch_emb = model.get_image_features(pixel_values=batch)

        # convert to numpy array
        batch_emb = batch_emb.squeeze(0)
        batch_emb = batch_emb.cpu().detach().numpy()

        # store embeddings in dictionary
        for path, emb in zip(batch_paths, batch_emb):
            file_name = os.path.basename(path).split(".")[0]
            embeddings_dict[file_name] = emb.tolist()

    return embeddings_dict

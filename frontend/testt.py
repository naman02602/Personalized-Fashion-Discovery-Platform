import openai
import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import boto3

openai_api_key = "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"

from transformers import CLIPTokenizerFast, CLIPProcessor, CLIPModel
import torch
from chatbot import search_similar_items, get_image_from_s3

device = "cpu"

model_id = "openai/clip-vit-base-patch32"
model = CLIPModel.from_pretrained(model_id).to(device)
# we initialize a tokenizer, image processor, and the model itself
tokenizer = CLIPTokenizerFast.from_pretrained(model_id)
s3_client = boto3.client(
    service_name="s3",
    region_name="us-east-1",
    aws_access_key_id="AKIA5IE7JCG4E76C7THC",
    aws_secret_access_key="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",
)

aiprompt = [
    """You are an expert fashion product discovery chatbot.
You are supposed to ask the user what they are looking for today.""",
    """ask if the user has any specific requirements in the product.""",
    """Once the user answers questions, extract the keywords from the
answer and return a summarized statement of keywords to search in the product catalog.
The summarized statement should include keywords about product and it's specifications
that user is looking for. The summarized statement should start with "Looking for ".""",
]

# aiprompt1 = """Once the user answers both questions, extract the keywords from the
# answer and return a summarized statement of keywords to search in the product catalog.
# The summarized statement should include keywords about product and it's specifications
# that user is looking for. The summarized statement should start with "Looking for "."""


def get_text():
    is_disabled = st.session_state["count"] == 3
    input_text = st.text_input(
        "You: ",
        st.session_state["input"],
        key="input",
        placeholder="Your Clothing assistant here! Ask me anything...",
        label_visibility="hidden",
        disabled=is_disabled,
    )
    return input_text


def main():
    if "generated" not in st.session_state:
        st.session_state["generated"] = []  # output
    if "past" not in st.session_state:
        st.session_state["past"] = []  # past
    if "input" not in st.session_state:
        st.session_state["input"] = ""
    if "stored_session" not in st.session_state:
        st.session_state["stored_session"] = []
    if "count" not in st.session_state:
        st.session_state["count"] = 0
    model = ChatOpenAI(openai_api_key=openai_api_key)

    user_input = get_text()
    st.session_state["last_bot_msg"] = None

    for i in range(len(st.session_state["past"]) + 1):
        if i == 0:
            prompt = ChatPromptTemplate.from_template(aiprompt[i])
            chain = prompt | model
            output = chain.invoke({""}).content
            st.chat_message("assistant").write(output)
            st.session_state.generated.append(output)
            st.session_state.past.append(user_input)

            if user_input:
                st.chat_message("user").write(st.session_state["past"][i + 1])

        if i > 0 and i < 3:
            prompt = ChatPromptTemplate.from_template(
                aiprompt[i] + str(st.session_state["past"])
            )
            chain = prompt | model
            output = chain.invoke({""}).content
            st.chat_message("assistant").write(output)
            st.session_state.generated.append(output)
            if user_input != st.session_state["past"][i]:
                st.session_state.past.append(user_input)
                st.chat_message("user").write(st.session_state["past"][i + 1])
        st.session_state["last_bot_msg"] = st.session_state.generated[-1]
        print(st.session_state["last_bot_msg"])
        st.session_state["count"] += 1
    st.markdown("""---""")
    if st.session_state["count"] == 6:
        st.write(st.session_state["last_bot_msg"])
        fetch_from_vector_db(st.session_state["last_bot_msg"])


def fetch_from_vector_db(query: str):
    inputs = tokenizer(query, return_tensors="pt")
    text_emb = model.get_text_features(**inputs)
    # print(type(text_emb))
    results = search_similar_items(text_emb, 3)
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
                    # If the value is a list, join it into a string for display
                    if isinstance(value, list):
                        value = ", ".join(value)
                    st.write(f"{key.capitalize()}: {value}")
            else:
                st.write("No metadata available.")


if __name__ == "__main__":
    main()

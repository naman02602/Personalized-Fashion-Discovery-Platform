import openai
import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

openai_api_key = "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"

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
    input_text = st.text_input(
        "You: ",
        st.session_state["input"],
        key="input",
        placeholder="Your Clothing assistant here! Ask me anything...",
        label_visibility="hidden",
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

    model = ChatOpenAI(openai_api_key=openai_api_key)

    user_input = get_text()
    last_bot_msg = None
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
        last_bot_message = st.session_state.generated[-1]
    st.markdown("""---""")
    st.write(last_bot_message)


if __name__ == "__main__":
    main()

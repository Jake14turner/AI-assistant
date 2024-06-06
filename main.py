import os
from dotenv import load_dotenv
import openai
import requests
import json
import time
import logging
from datetime import datetime
import streamlit as st

#ngrok http http://localhost:8514 


load_dotenv().

#input your own key into the argument
#openai.api_key = os.environ.get("")

client = openai.OpenAI()

model = "gpt-3.5-turbo"



thread_id = "thread_b5GrU9vdpTWTaskVx7vZaKF9"
assistant_id = "asst_9nsSNE3QD5g4bpHP1MR1gddh"

#initialize all the sessions
if "file_id_list" not in st.session_state:
    st.session_state.file_id_list = []

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None


#set up UI
st.set_page_config(
    page_title="Reformed Scholar",
    page_icon = ":books:"
)

#function definitions
def upload_to_openai(filepath):
    with open(filepath, "rb") as file:
        response = client.files.create(file = file.read(), purpose = "assistants")
    return response.id

#create a side bar where users can upload files
file_uploaded = st.sidebar.file_uploader(
    "Add your own text documents to be part of the knoledge base",
    key = "file_upload"
)

#upload file button - store file id
if st.sidebar.button("Upload file"):
    if file_uploaded:
        with open(f"{file_uploaded.name}", "wb") as f:
            f.write(file_uploaded.getbuffer())
        another_file_id = upload_to_openai(f"{file_uploaded.name}")
        st.session_state.file_id_list.append(another_file_id)
        st.sidebar.write(f"FileID:: {another_file_id}")

#display those file id's
#if st.session_state.file_id_list:
#    st.sidebar.write("Uploaded File IDs:")
#    for file_id in st.session_state.file_id_list:
#        st.sidebar.write(file_id)
#        # Associate each file id with the current assistant
#        assistantt_file = client.beta.assistants.files.create(
#            assistant_id=assistant_id, file_id=file_id
#        )

#button to initiate the chat session

    #else:
    #    st.sidebar.warning("No files found, please upload at least one file to get started")
         


def process_message_with_citations(message):
    """Extract content and annotations from the message and format citations as footnotes."""
    message_content = message.content[0].text
    annotations = (
        message_content.annotations if hasattr(message_content, "annotations") else []
    )
    citations = []

    # Iterate over the annotations and add footnotes
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content.value = message_content.value.replace(
            annotation.text, f" [{index + 1}]"
        )

        # Gather citations based on annotation attributes
        if file_citation := getattr(annotation, "file_citation", None):
            # Retrieve the cited file details (dummy response here since we can't call OpenAI)
            cited_file = {
                "filename": "cryptocurrency.pdf"
            }  # This should be replaced with actual file retrieval
            citations.append(
                f'[{index + 1}] {file_citation.quote} from {cited_file["filename"]}'
            )
        elif file_path := getattr(annotation, "file_path", None):
            # Placeholder for file download citation
            cited_file = {
                "filename": "cryptocurrency.pdf"
            }  # TODO: This should be replaced with actual file retrieval
            citations.append(
                f'[{index + 1}] Click [here](#) to download {cited_file["filename"]}'
            )  # The download link should be replaced with the actual download path

    # Add footnotes to the end of the message content
    full_response = message_content.value #+ "\n\n" + "\n".join(citations)
    return full_response





#the main interface

st.title("Reformed Scholar")
st.write("Reformed Theology pennington approved")


#check sessions

#if st.session_state.start_chat:
#    if "openai_model" not in st.session_state:
#        st.session_state.openai_model = "gpt-3.5-turbo"
#    if "messages" not in st.session_state:
#        st.session_state.messages = []
#
#    for message in st.session_state.messages:
#        with st.chat_message(message["role"]):
#            st.markdown(message["content"])

#chat input for the user
if prompt := st.chat_input("Ask me your practical and theological questions"):
        #add user message to the state and display on the screen
    st.session_state.messages.append(
        {
                "role": "user", 
                "content": prompt
        }
    )
    with st.chat_message("user"):
        st.markdown(prompt)

            #add the use's message to the xisting thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role = "user",
        content = prompt
    )

        #create a run with additional instrucitons
    run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id= assistant_id,
            instructions= "Please answer the question with the information provided in the files. WHen adding additional informatin, please use bold text."
    )

        #show a spinner while the assistant is thinking
    with st.spinner("Generating response..."):
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id= st.session_state.thread_id,
                run_id = run.id
            )
            #retreive messages added by the assistant
        messages = client.beta.threads.messages.list(
            thread_id= st.session_state.thread_id
        )
            #process and dislpay assistant messages
        assistant_messages_for_run = [
            message for message in messages
            if message.run_id == run.id and message.role == "assistant"
                
        ]
        for message in assistant_messages_for_run:
            full_response = process_message_with_citations(message=message)
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
            with st.chat_message("assistant"):
                st.markdown(full_response, unsafe_allow_html=True)

    #else:
    #    # Promopt users to start chat
    #    st.write(
    #        "Please upload at least a file to get started by clicking on the 'Start Chat' button"
    #    )



if st.button("Start chatting"):
    #if st.session_state.file_id_list:
    st.session_state.start_chat = True

    #create a new thread
    chat_thread = client.beta.threads.create()
    st.session_state.thread_id = chat_thread.id
    st.write("Thread ID: ", chat_thread.id)
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-3.5-turbo"
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Import necessary modules and define env variables

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import os
import io
import chainlit as cl
import PyPDF2
from io import BytesIO


from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY= os.environ['OPENAI_API_KEY']
DOC_LOCATION= os.environ['DOC_LOCATION']

# text_splitter and system template

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

system_template = """Use the following pieces of context to answer the users question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
ALWAYS return a "SOURCES" part in your answer.
The "SOURCES" part should be a reference to the source of the document from which you got your answer.

Example of your response should be:

```
The answer is foo
SOURCES: xyz
```

Begin!
----------------
{summaries}"""


messages = [
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template("{question}"),
]
prompt = ChatPromptTemplate.from_messages(messages)
chain_type_kwargs = {"prompt": prompt}


@cl.on_chat_start
async def on_chat_start():

    # Define the folder where the PDF files are stored
    pdf_folder = DOC_LOCATION

    # Get a list of all PDF files in the folder
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]
	
    msg = cl.Message(content=f"Initializing...")
    await msg.send()
    # Process each PDF file in the folder
    for pdf_file in pdf_files:
        file_path = os.path.join(pdf_folder, pdf_file)
        msg = cl.Message(content=f"...")
        await msg.send()

        # Read the PDF file
        with open(file_path, "rb") as f:
            pdf = PyPDF2.PdfReader(f)
            pdf_text = ""
            for page in pdf.pages:
                pdf_text += page.extract_text()
        # Split the text into chunks
        texts = text_splitter.split_text(pdf_text)

        # Create metadata for each chunk
        metadatas = [{"source": f"{i}-py"} for i in range(len(texts))]

        # Create a Chroma vector store
        embeddings = OpenAIEmbeddings()
        docsearch = await cl.make_async(Chroma.from_texts)(
            texts, embeddings, metadatas=metadatas
        )

        # Create a chain that uses the Chroma vector store
        chain = RetrievalQAWithSourcesChain.from_chain_type(
            ChatOpenAI(temperature=0),
            chain_type="stuff",
            retriever=docsearch.as_retriever(),
        )

        # Save the metadata and texts in the user session
        cl.user_session.set("metadatas", metadatas)
        cl.user_session.set("texts", texts)

        # Let the user know that the system is ready
        msg.content = f"."
        await msg.update()

        cl.user_session.set("chain", chain)
    msg.content = f"Hello! 👋, Welcome to NCAssist, your friendly AI assistant. I'm here to help you with any questions or tasks you may have. Whether you need some information, a chat, or assistance with a task, I'm here to assist you."
    await msg.update()




@cl.on_message
async def main(message:str):

    chain = cl.user_session.get("chain")  # type: RetrievalQAWithSourcesChain
    cb = cl.AsyncLangchainCallbackHandler(
        stream_final_answer=True, answer_prefix_tokens=["FINAL", "ANSWER"]
    )
    cb.answer_reached = True
    res = await chain.acall(message, callbacks=[cb])

    answer = res["answer"]
    sources = res["sources"].strip()
    source_elements = []
    
    # Get the metadata and texts from the user session
    metadatas = cl.user_session.get("metadatas")
    all_sources = [m["source"] for m in metadatas]
    texts = cl.user_session.get("texts")

    if sources:
        found_sources = []

        # Add the sources to the message
        for source in sources.split(","):
            source_name = source.strip().replace(".", "")
            # Get the index of the source
            try:
                index = all_sources.index(source_name)
            except ValueError:
                continue
            text = texts[index]
            found_sources.append(source_name)
            # Create the text element referenced in the message
            source_elements.append(cl.Text(content=text, name=source_name))

        if found_sources:
            answer += f"\nSources: {', '.join(found_sources)}"
        else:
            answer += "\nNo sources found"

    if cb.has_streamed_final_answer:
        cb.final_stream.elements = source_elements
        await cb.final_stream.update()
    else:
        await cl.Message(content=answer, elements=source_elements).send()
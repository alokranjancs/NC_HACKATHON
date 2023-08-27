import pandas as pd
import numpy as np
import openai
import os

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']
 
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import CSVLoader
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import DocArrayInMemorySearch

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.indexes import VectorstoreIndexCreator

file  = "Cleaned_NCTMSfile.csv"
tms_loader = CSVLoader(file_path=file,encoding='utf-8')
tms_docs= tms_loader.load()


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 400,
    chunk_overlap = 20,
    separators=["\n\n", "\n", "(?<=\.)", " ", ""]
)

tms_splits = text_splitter.split_documents(tms_docs)

# bass page docs
bassdoc_loader = PyPDFLoader("D:/hackathon/NC_HACKATHON/AI_Chabot/solution/NCAssist/O2UK-DI-ePOS-PMT-006-ScanPLUCapability-260823-0424-738.pdf") 
desing_pages = bassdoc_loader.load()

pdf_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap = 20,
    separators=["\n\n", "\n", "(?<=\.)", " ", ""]
)

desing_pdf_splits = pdf_text_splitter.split_documents(desing_pages[4:])

bassdoc_loader = PyPDFLoader("D:/hackathon/NC_HACKATHON/AI_Chabot/solution/NCAssist/Rakuten_ERT - Production_Monitoring.pdf") 
ert_pages = bassdoc_loader.load()

pdf_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap = 50,
    separators=["\n\n", "\n", "(?<=\.)", " ", ""]
)

ert_pdf_splits = pdf_text_splitter.split_documents(ert_pages[3:])

all_docs= tms_splits[0:10]+ desing_pdf_splits + ert_pdf_splits



all_index = VectorstoreIndexCreator(
    vectorstore_cls=DocArrayInMemorySearch
).from_documents(all_docs)


def main():

    while True:
        user_query = input("You: ").strip().lower()

        if user_query == "exit":
            print("Chatbot: Goodbye!")
            break
        response = all_index.query(user_query)
        print(f"Chatbot: {response}")

if __name__ == '__main__':
    main()



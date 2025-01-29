from src.config.config import CHILD_CHUNK_SIZE, PARENT_CHUNK_SIZE
import logging
from typing import List, Optional
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain.storage._lc_store import create_kv_docstore
from langchain.storage import LocalFileStore

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers import ParentDocumentRetriever

from src.services.rag.loader import Loader
from src.config.creds import OPENAI_API_KEY, PINECONE_API_KEY
from src.config.config import COMPANY_DATA_QUERY
from src.services.llm.llm import extract_keywords
import os
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



class Retriever:
    def __init__(self, user_id):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=OPENAI_API_KEY)

        self.parent_splitter = RecursiveCharacterTextSplitter(chunk_size=PARENT_CHUNK_SIZE)
        self.child_splitter = RecursiveCharacterTextSplitter(chunk_size=CHILD_CHUNK_SIZE)
        self.index_name = "company-data"
        self.pc = Pinecone(
            pinecone_api_key=PINECONE_API_KEY,
        )
        
        

        if self.index_name in self.pc.list_indexes().names():
            self.vectorstore = PineconeVectorStore.from_existing_index(
                index_name=self.index_name,
                embedding=self.embeddings,
                namespace=user_id,
            )
        else:
            logging.info(f"Creating new index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1",
                    )
            )
                # wait for index to be initialized
            while not self.pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)
            self.vectorstore = PineconeVectorStore.from_existing_index(
                index_name=self.index_name,
                embedding=self.embeddings,
                namespace=user_id,
            )

        docstore_path = f"src/docstore/{user_id}/data"
        if not os.path.exists(f"src/docstore/{user_id}"):
            os.mkdir(f"src/docstore/{user_id}")
        
        fs = LocalFileStore(docstore_path)
        docstore = create_kv_docstore(fs)
        
        self.retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=docstore,
            child_splitter=self.child_splitter,
            parent_splitter=self.parent_splitter,
        )
        
    def add_documents(self, documents: List[str]) -> None:
        """
        Add documents to the retriever.

        Args:
            documents (List[str]): A list of documents to add to the retriever.
        """
        self.retriever.add_documents(documents)

    def get_query_docs(self, query: str, k: int = 1) -> Optional[str]:
        """
        Retrieve relevant documents based on the given query and documents.

        Args:
            query (str): The query string to search for relevant documents.
            docs (List[str]): A list of documents to search within.
            k (int): The number of relevant documents to retrieve (default: 1).

        Returns:
            Optional[str]: A string containing the concatenated page content of the relevant documents,
                or None if no relevant documents are found.
        """
        try:
            if self.index_name in self.pc.list_indexes().names():
                relevant_docs = self.retriever.get_relevant_documents(query, k=k)

                if relevant_docs:
                    return '\n'.join([doc.page_content for doc in relevant_docs[:k]])
                else:
                    logging.warning("No relevant documents found for the given query.")
                    return None
            else:
                logging.warning("Index does not exist for the user.")
                return None

        except Exception as e:
            logging.error(f"Error retrieving documents: {e}")
            return None
    
    def get_keywords(self, max_length: int) -> None:
        """
        Extract keywords from a company description using a language model.

        Args:
            company_description (str): The description of the company.
        """
        docs = self.get_query_docs(COMPANY_DATA_QUERY, k=3)
        return extract_keywords(docs, max_length)
        
        
# Example usage
if __name__ == "__main__":
    user_id = "123"
    retriever = Retriever(user_id)
    query = "What is the company's mission?"
    
    loader = Loader()
    docs = loader.load_documents(["/home/bert/work/bigkittylabs/RFPScrapper_Global/backend/company.pdf"])
    
    
    retriever.add_documents(docs)
    
    
    # relevant_docs = retriever.get_query_docs(query, k=3)
    # print(relevant_docs)
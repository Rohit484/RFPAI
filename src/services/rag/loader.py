from langchain_community.document_loaders import PyMuPDFLoader

class Loader():
    def __init__(self):
        pass
        
    def load_document(self, path):
        self.loader = PyMuPDFLoader(path)
        return self.loader.load()
    
    def load_documents(self, paths):
        docs = []
        for path in paths:
            docs.extend(self.load_document(path))
        return docs
    
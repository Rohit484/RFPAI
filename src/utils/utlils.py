import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity




def hash(password: str):
    return hashlib.md5((password).encode()).hexdigest()



def semantic_similarity(company_description, rfp_description):
    
    print(company_description)
    print(rfp_description)
    
    # Create a corpus
    corpus = [company_description, rfp_description]

    # Compute TF-IDF vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Calculate cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])

    # Scale the similarity score
    similarity_score = (cosine_sim[0][0] + 1) * 50

    return int(similarity_score)
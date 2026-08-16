from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from data.models import udahub
from sqlalchemy import create_engine
from utils import get_session

engine = create_engine("sqlite:///data/core/udahub.db")


def search_knowledge_base(query: str) -> list[dict]:
    """
    Search the udahub knowledge base for articles relevant to a user's
    question, using TF-IDF + cosine similarity over each article's
    title, content and tags combined — so natural-language questions
    are matched by keyword relevance, not by requiring the whole query
    to appear as a literal substring.

    Input:
        query (str): free-text search terms.

    Output:
        list of dicts, each with: title (str), content (str), tags (str),
        confidence (float, the cosine similarity). Empty list if nothing
        matches. Sorted by confidence, highest first.
    """
    with get_session(engine) as session:
        knowledge_articles = session.query(udahub.Knowledge).all()

        if not knowledge_articles:
            return []

        documents = [
            f"{article.title} {article.content} {article.tags or ''}"
            for article in knowledge_articles
        ]

        vectorizer = TfidfVectorizer(stop_words="english")
        article_vectors = vectorizer.fit_transform(documents)
        query_vector = vectorizer.transform([query])

        similarities = cosine_similarity(query_vector, article_vectors)[0]

        articles = [
            {
                "title": article.title,
                "content": article.content,
                "tags": article.tags,
                "confidence": float(score),
            }
            for article, score in zip(knowledge_articles, similarities)
            if score > 0
        ]

        articles.sort(key=lambda a: a["confidence"], reverse=True)
        return articles

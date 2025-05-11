from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os

# LangChain and Embeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import webbrowser


# Load environment variables
load_dotenv()

# Load Google API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Load books CSV
books = pd.read_csv("books_with_emotions.csv")
books["large_thumbnail"] = books["thumbnail"] + "&fife=w800"
books["large_thumbnail"] = np.where(
    books["large_thumbnail"].isna(),
    "cover-not-found.jpg",
    books["large_thumbnail"],
)

# Load documents and create vector database
raw_documents = TextLoader("tagged_description.txt", encoding='utf-8').load()
text_splitter = CharacterTextSplitter(separator="\n", chunk_size=0, chunk_overlap=0)
documents = text_splitter.split_documents(raw_documents)

db_books = FAISS.from_documents(
    documents,
    embedding=GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key="AIzaSyAxbZQ9c0hHrA5MB5f2gqz3ymRVCizJdnI"
    )
)

# Create FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request body model
class RequestBody(BaseModel):
    query: str
    category: str
    tone: str

# Semantic recommendation logic
def retrieve_semantic_recommendations(query, category, tone, initial_top_k=50, final_top_k=16):
    recs = db_books.similarity_search(query, k=initial_top_k)
    books_list = [int(rec.page_content.strip('"').split()[0]) for rec in recs]
    book_recs = books[books["isbn13"].isin(books_list)].head(initial_top_k)

    if category != "All":
        book_recs = book_recs[book_recs["simple_categories"] == category].head(final_top_k)
    else:
        book_recs = book_recs.head(final_top_k)

    if tone == "Happy":
        book_recs = book_recs.sort_values(by="joy", ascending=False)
    elif tone == "Surprising":
        book_recs = book_recs.sort_values(by="surprise", ascending=False)
    elif tone == "Angry":
        book_recs = book_recs.sort_values(by="anger", ascending=False)
    elif tone == "Suspenseful":
        book_recs = book_recs.sort_values(by="fear", ascending=False)
    elif tone == "Sad":
        book_recs = book_recs.sort_values(by="sadness", ascending=False)

    return book_recs

# POST: Book recommendations
@app.post("/recommend")
def recommend_books(request: RequestBody):
    recommendations = retrieve_semantic_recommendations(
        request.query, request.category, request.tone
    )
    results = []

    for _, row in recommendations.iterrows():
        description = row.get("description", "No description available.")
        truncated_description = " ".join(description.split()[:30]) + "..."

        authors_split = row["authors"].split(";")
        if len(authors_split) == 2:
            authors_str = f"{authors_split[0]} and {authors_split[1]}"
        elif len(authors_split) > 2:
            authors_str = f"{', '.join(authors_split[:-1])}, and {authors_split[-1]}"
        else:
            authors_str = row["authors"]

        caption = row['title']

        results.append({
            "id": int(row["isbn13"]),
            "thumbnail": row["large_thumbnail"],
            "caption": caption
        })

    return results

# GET: Available categories
@app.get("/categories")
def get_categories():
    unique_categories = sorted(books["simple_categories"].dropna().unique().tolist())
    return ["All"] + unique_categories

# ✅ NEW GET: Book details by ISBN13
@app.get("/book/{isbn13}")
def get_book(isbn13: int):
    book = books[books["isbn13"] == isbn13]

    if book.empty:
        raise HTTPException(status_code=404, detail="Not Found")

    row = book.iloc[0]

    authors_split = row["authors"].split(";")
    if len(authors_split) == 2:
        authors_str = f"{authors_split[0]} and {authors_split[1]}"
    elif len(authors_split) > 2:
        authors_str = f"{', '.join(authors_split[:-1])}, and {authors_split[-1]}"
    else:
        authors_str = row["authors"]

    return {
        "id": int(row["isbn13"]),
        "caption": f"{row['title']} by {authors_str}",
        "description": row.get("description", "No description available."),
        "category": row.get("simple_categories", "Unknown"),
        "emotion": row.get("dominant_emotion", "N/A"),
        "thumbnail": row["large_thumbnail"],
        "quote": row.get("quote", "No quote available."),
        "source": row.get("authors", "Unknown")
    }

# Serve static files (like HTML, JS)
app.mount("/", StaticFiles(directory=".", html=True), name="root")


# Serve index.html at root "/"
@app.get("/")
def serve_index():
    return FileResponse("index.html")

webbrowser.open("http://127.0.0.1:8000")

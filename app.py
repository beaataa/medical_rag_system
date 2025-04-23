from flask import Flask, request, jsonify, render_template, send_from_directory
# Updated import paths for LangChain
from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
# LlamaIndex imports 
from llama_index.core import VectorStoreIndex, Document
from llama_index.embeddings.openai import OpenAIEmbedding
import os
import requests
import xml.etree.ElementTree as ET
import json

# Import from config file
from config import OPENAI_API_KEY, PUBMED_EMAIL

# Set OpenAI API key
import openai
openai.api_key = OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY  # Set environment variable too

app = Flask(__name__, static_folder='frontend/medical-assistant/build/static', template_folder='frontend/medical-assistant/build')

# Function to fetch and parse PubMed data
def fetch_pubmed_data(search_term, max_results=10):
    """Fetch medical data from PubMed API and parse into LlamaIndex Documents"""
    documents = []
    
    try:
        print(f"Fetching PubMed data for: {search_term}")
        # Step 1: Search for IDs
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": search_term,
            "retmode": "json",
            "retmax": str(max_results),
            "email": PUBMED_EMAIL  # Added email for better rate limits
        }
        
        search_response = requests.get(search_url, params=search_params)
        if search_response.status_code != 200:
            print(f"Error searching PubMed: {search_response.status_code}")
            print(search_response.text)
            return documents
            
        search_data = search_response.json()
        
        # Get article IDs
        ids = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not ids:
            print("No PubMed IDs found")
            return documents
            
        print(f"Found {len(ids)} articles")
        
        # Step 2: Fetch details for each ID
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
            "email": PUBMED_EMAIL  # Added email for better rate limits
        }
        
        fetch_response = requests.get(fetch_url, params=fetch_params)
        
        if fetch_response.status_code != 200:
            print(f"Error fetching article details: {fetch_response.status_code}")
            print(fetch_response.text)
            return documents
            
        # Parse XML response
        root = ET.fromstring(fetch_response.text)
        
        # Extract articles
        articles = root.findall(".//PubmedArticle")
        
        for article in articles:
            # Extract article ID
            pmid = article.find(".//PMID").text if article.find(".//PMID") is not None else "Unknown"
            
            # Extract title
            title_element = article.find(".//ArticleTitle")
            title = title_element.text if title_element is not None else "No title available"
            
            # Extract abstract
            abstract_texts = article.findall(".//AbstractText")
            abstract = " ".join([text.text for text in abstract_texts if text.text]) if abstract_texts else "No abstract available"
            
            # Extract authors
            author_elements = article.findall(".//Author")
            authors = []
            for author in author_elements:
                last_name = author.find("LastName")
                fore_name = author.find("ForeName")
                if last_name is not None and fore_name is not None:
                    authors.append(f"{fore_name.text} {last_name.text}")
                elif last_name is not None:
                    authors.append(last_name.text)
            author_string = ", ".join(authors) if authors else "Unknown authors"
            
            # Extract journal info
            journal_element = article.find(".//Journal/Title")
            journal = journal_element.text if journal_element is not None else "Unknown journal"
            
            # Extract publication date
            year_element = article.find(".//PubDate/Year")
            year = year_element.text if year_element is not None else "Unknown year"
            
            # Create document text
            doc_text = f"""Title: {title}
            
Authors: {author_string}

Journal: {journal}, {year}

Abstract: {abstract}

PubMed ID: {pmid}
URL: https://pubmed.ncbi.nlm.nih.gov/{pmid}/
"""
            
            # Create LlamaIndex document
            doc = Document(
                text=doc_text,
                metadata={
                    "source": "PubMed",
                    "pmid": pmid,
                    "title": title,
                    "authors": author_string
                }
            )
            documents.append(doc)
            
    except Exception as e:
        print(f"Error fetching PubMed data: {e}")
        
    return documents

# Initialize components with PubMed data
def initialize_rag_system():
    try:
        # 1. Fetch documents from PubMed
        # Start with some common medical topics to populate the index
        search_terms = [
            "diabetes treatment", 
            "hypertension guidelines", 
            "cancer immunotherapy",
            "infectious disease antibiotics",
            "mental health therapy"
        ]
        
        all_documents = []
        for term in search_terms:
            documents = fetch_pubmed_data(term, max_results=5)
            all_documents.extend(documents)
        
        if not all_documents:
            print("WARNING: No documents retrieved from PubMed")
            # Create a minimal fallback document
            fallback_doc = Document(
                text="No medical information available. Please try again with a more specific query.",
                metadata={"source": "fallback"}
            )
            all_documents = [fallback_doc]
        
        print(f"Total documents loaded: {len(all_documents)}")
        
        # 2. Use OpenAI embeddings
        embed_model = OpenAIEmbedding(
            model="text-embedding-ada-002",
            api_key=OPENAI_API_KEY
        )
        
        # 3. Create LlamaIndex with OpenAI embeddings
        index = VectorStoreIndex.from_documents(
            all_documents,
            embed_model=embed_model
        )
        
        # 4. Create query engine
        query_engine = index.as_query_engine()
        
        # 5. Initialize LangChain components with OpenAI
        llm = OpenAI(api_key=OPENAI_API_KEY, temperature=0.2)
        
        # Create a prompt template
        template = """
        You are a helpful medical information assistant. Use the following medical information retrieved from PubMed to answer the user's question.
        If you can't find an answer in the provided information, say so clearly and suggest they consult a healthcare professional.
        Always mention that the information is from PubMed and is for informational purposes only.
        
        Retrieved Information:
        {context}
        
        User Question: {question}
        
        Answer:
        """
        
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )
        
        # Create the chain with OpenAI
        chain = LLMChain(llm=llm, prompt=prompt)
        
        return query_engine, chain
    
    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        # Create a fallback system that returns a simple response
        class FallbackQueryEngine:
            def query(self, text):
                class Response:
                    def __init__(self):
                        self.response = "Sorry, the system is currently experiencing issues with PubMed data retrieval."
                return Response()
        
        # Create a simple chain
        class FallbackChain:
            def run(self, context=None, question=None):
                return "I'm sorry, but I couldn't retrieve medical information at this time. Please try again later or consult a healthcare professional."
        
        return FallbackQueryEngine(), FallbackChain()

# API endpoint to search PubMed directly
@app.route("/api/medical-data/pubmed/search", methods=["GET"])
def search_pubmed():
    """Search PubMed and return results as JSON"""
    try:
        query = request.args.get("q", "")
        max_results = int(request.args.get("max", "10"))
        
        if not query:
            return jsonify({"error": "Search query required"}), 400
            
        # Use the esearch endpoint of PubMed
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": str(max_results),
            "email": PUBMED_EMAIL
        }
        
        search_response = requests.get(search_url, params=search_params)
        search_data = search_response.json()
        
        # Get article IDs
        ids = search_data.get("esearchresult", {}).get("idlist", [])
        
        if not ids:
            return jsonify({"results": [], "count": 0, "query": query})
            
        # Get article summaries
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json",
            "email": PUBMED_EMAIL
        }
        
        summary_response = requests.get(summary_url, params=summary_params)
        summary_data = summary_response.json()
        
        # Extract relevant information
        results = []
        for article_id in ids:
            article = summary_data.get("result", {}).get(article_id, {})
            if article:
                results.append({
                    "id": article_id,
                    "title": article.get("title", "No title"),
                    "authors": article.get("authors", []),
                    "journal": article.get("fulljournalname", "Unknown journal"),
                    "pubdate": article.get("pubdate", "Unknown date"),
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/"
                })
            
        return jsonify({
            "query": query,
            "results": results,
            "count": len(results)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to get full article details
@app.route("/api/medical-data/pubmed/article/<article_id>", methods=["GET"])
def get_pubmed_article(article_id):
    """Get full article details from PubMed"""
    try:
        # Fetch the article using the efetch endpoint
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": article_id,
            "retmode": "xml",
            "email": PUBMED_EMAIL
        }
        
        fetch_response = requests.get(fetch_url, params=fetch_params)
        
        if fetch_response.status_code != 200:
            return jsonify({"error": "Article not found"}), 404
            
        # Parse XML response
        root = ET.fromstring(fetch_response.text)
        
        # Extract article
        article = root.find(".//PubmedArticle")
        
        if article is None:
            return jsonify({"error": "Article not found in response"}), 404
            
        # Extract title
        title_element = article.find(".//ArticleTitle")
        title = title_element.text if title_element is not None else "No title available"
        
        # Extract abstract
        abstract_texts = article.findall(".//AbstractText")
        abstract = " ".join([text.text for text in abstract_texts if text.text]) if abstract_texts else "No abstract available"
        
        # Extract authors
        author_elements = article.findall(".//Author")
        authors = []
        for author in author_elements:
            last_name = author.find("LastName")
            fore_name = author.find("ForeName")
            if last_name is not None and fore_name is not None:
                authors.append(f"{fore_name.text} {last_name.text}")
            elif last_name is not None:
                authors.append(last_name.text)
        
        # Extract journal info
        journal_element = article.find(".//Journal/Title")
        journal = journal_element.text if journal_element is not None else "Unknown journal"
        
        # Extract publication date
        year_element = article.find(".//PubDate/Year")
        year = year_element.text if year_element is not None else "Unknown year"
        
        return jsonify({
            "pmid": article_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "journal": journal,
            "year": year,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to update the RAG index with new PubMed data
@app.route("/api/medical-data/update-index", methods=["POST"])
def update_index():
    """Update the RAG index with new PubMed data"""
    try:
        data = request.json
        query = data.get("query", "")
        max_results = data.get("max_results", 10)
        
        if not query:
            return jsonify({"error": "Search query required"}), 400
            
        # Fetch new documents
        new_documents = fetch_pubmed_data(query, max_results)
        
        if not new_documents:
            return jsonify({"error": "No documents found for the query"}), 404
            
        # Update the index
        global medical_query_engine, llm_chain
        
        # Use OpenAI embeddings
        embed_model = OpenAIEmbedding(
            model="text-embedding-ada-002",
            api_key=OPENAI_API_KEY
        )
        
        # Create a new index with the new documents
        new_index = VectorStoreIndex.from_documents(
            new_documents,
            embed_model=embed_model
        )
        
        # Update the query engine
        medical_query_engine = new_index.as_query_engine()
        
        return jsonify({
            "message": "Index updated successfully",
            "documents_added": len(new_documents)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/api/ask", methods=["POST"])
def ask():
    try:
        question = request.json["question"]
        
        # Step 1: Use LlamaIndex for retrieval from existing index
        retrieved_context = medical_query_engine.query(question)
        
        # Step 2: For medical questions, enhance with fresh PubMed data
        # This ensures the most up-to-date information
        new_docs = fetch_pubmed_data(question, max_results=3)
        if new_docs:
            # Add fresh data to the context
            fresh_context = "\n\n".join([doc.text for doc in new_docs])
            combined_context = f"{retrieved_context.response}\n\nAdditional recent information:\n{fresh_context}"
        else:
            combined_context = retrieved_context.response
        
        # Step 3: Use LangChain for generation
        final_response = llm_chain.run(
            context=combined_context,
            question=question
        )
        
        return jsonify({
            "response": final_response,
            "sources": [doc.metadata.get("pmid") for doc in new_docs] if new_docs else []
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Serve React App - this will catch all routes not defined above
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.template_folder, 'index.html')


# Initialize system at startup
print("Initializing RAG system with PubMed data...")
medical_query_engine, llm_chain = initialize_rag_system()
print("RAG system initialized!")

if __name__ == "__main__":
    app.run(debug=True)
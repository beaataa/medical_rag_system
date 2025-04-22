# Medical Information Assistant

A Flask-based web application that uses Retrieval-Augmented Generation (RAG) with OpenAI and PubMed data to answer medical questions.
Users can ask any medical question and receive up-to-date, referenced information from PubMed articles, powered by large language models.

## Features
- Ask medical questions and get answers based on real PubMed articles.
- Retrieval-Augmented Generation (RAG): Combines document retrieval with OpenAI LLMs for accurate, referenced responses.
- Fresh PubMed data: Fetches and parses the latest articles for each query.
- Web interface: Simple, responsive frontend for user interaction.
- API endpoints: For advanced queries and updating the knowledge base.

## Demo
![App Screenshot](screenshots/screenshot.png)

1. Clone the repository
```bash
git clone <repository-url>
cd medical_rag_system
```

2. Set Up API Keys and Configuration in config.py
```bash
OPENAI_API_KEY=your_openai_api_key (get from OpenAI dashboard)
PUBMED_EMAIL=your_email@example.com (for PubMed E-utilities, recommended for higher rate limits)
```
3. Install Dependencies and activate a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Run the Application
```bash
python app.py
```
The app will be available at http://localhost:5000.

## Usage
- Enter your medical question in the search box and click "Search".
- The assistant will retrieve relevant PubMed articles and generate an answer.
- Sources are listed below each answer with direct links to PubMed.

## API Endpoints
- POST /ask — Ask a medical question (JSON: { "question": "..." })
- GET /api/medical-data/pubmed/search?q=... — Search PubMed for articles.
- GET /api/medical-data/pubmed/article/<article_id> — Get full details for an article.
- POST /api/medical-data/update-index — Update the RAG index with new PubMed data.

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

def preprocess_text(text):
    """Preprocess text by tokenizing, removing stopwords, and lemmatizing."""
    # Tokenize
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    return tokens

def extract_medical_entities(text):
    """Extract medical entities from text using simple keyword matching.
    In a real application, you would use a more sophisticated NER model."""
    medical_keywords = {
        'disease': ['diabetes', 'cancer', 'asthma', 'hypertension'],
        'symptom': ['fever', 'pain', 'cough', 'fatigue'],
        'treatment': ['surgery', 'medication', 'therapy', 'vaccine']
    }
    
    tokens = preprocess_text(text)
    entities = {}
    
    for category, keywords in medical_keywords.items():
        matches = [token for token in tokens if token in keywords]
        if matches:
            entities[category] = matches
            
    return entities
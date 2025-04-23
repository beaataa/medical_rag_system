import React, { useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import SearchForm from './components/SearchForm';
import ResponseDisplay from './components/ResponseDisplay';

function App() {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState('');
  const [sources, setSources] = useState([]);

  return (
    <div className="container mt-5">
      <h1 className="text-center mb-4">Medical Information Assistant</h1>
      
      <div className="card shadow-sm">
        <div className="card-body">
          <p className="card-text">Ask any medical question and get information from PubMed:</p>
          
          <SearchForm 
            setResponse={setResponse} 
            setLoading={setLoading} 
            setSources={setSources} 
          />
          
          {loading && (
            <div className="text-center my-4">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="mt-2">Searching medical databases...</p>
            </div>
          )}
          
          <ResponseDisplay response={response} sources={sources} />
        </div>
      </div>
    </div>
  );
}

export default App;
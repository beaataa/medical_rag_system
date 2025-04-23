// src/components/ResponseDisplay.js
import React from 'react';

function ResponseDisplay({ response, sources }) {
  if (!response) return null;

  return (
    <div className="response-container">
      <div className="response-text">
        {response.split('\n').map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>
      
      {sources && sources.length > 0 && (
        <div className="sources">
          <p><strong>Sources:</strong></p>
          <ul>
            {sources.map(pmid => (
              <li key={pmid}>
                <a 
                  href={`https://pubmed.ncbi.nlm.nih.gov/${pmid}/`} 
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  PubMed ID: {pmid}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default ResponseDisplay;



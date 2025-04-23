// src/components/SearchForm.js
import React, { useState } from 'react';
import axios from 'axios';

function SearchForm({ setResponse, setLoading, setSources }) {
  const [question, setQuestion] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setResponse('');
    setSources([]);

    try {
      const res = await axios.post('/api/ask', { question });
      setResponse(res.data.response);
      setSources(res.data.sources || []);
    } catch (err) {
      console.error('Error fetching data:', err);
      setResponse('Error: Could not retrieve information. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="search-container">
      <div className="input-group mb-3">
        <input
          type="text"
          className="form-control"
          placeholder="Enter your medical question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button className="btn btn-primary" type="submit">
          Search
        </button>
      </div>
    </form>
  );
}

export default SearchForm;

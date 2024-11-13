"use client";

import { useState } from "react";
import './styles.css'; // Import the CSS file

export default function Home() {
  const [query, setQuery] = useState(""); // State for capturing query input
  const [results, setResults] = useState<any>(null); // State for storing results

  // Function to handle Arxiv search
  const searchArxiv = async () => {
    const maxResults = 5; // Set the number of results you want

    const requestData = {
      query: query,
      max_results: maxResults,
    };

    try {
      const response = await fetch("http://localhost:8000/copilotkit_remote", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      const data = await response.json(); // Assuming the response is JSON
      if (data.results) {
        setResults(data.results); // Update the state with the results
      } else {
        setResults([{ title: "Error", summary: "No results found." }]);
      }
    } catch (error) {
      console.error("Error:", error);
      setResults([{ title: "Error", summary: "Something went wrong." }]);
    }
  };

  // Function to handle RAG search
  const searchRag = async () => {
    const maxResults = 5; // Set the number of results you want

    const requestData = {
      query: query,
      max_results: maxResults,
    };

    try {
      const response = await fetch("http://localhost:8000/rag-search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      const data = await response.json(); // Assuming the response is JSON
      if (data.choices && data.choices[0] && data.choices[0].message) {
        const content = data.choices[0].message.content; // Extract the content
        setResults([{ title: "RAG Search Result", summary: content }]); // Update the state with the content
      } else {
        setResults([{ title: "Error", summary: "No results found." }]);
      }
    } catch (error) {
      console.error("Error:", error);
      setResults([{ title: "Error", summary: "Something went wrong." }]);
    }
  };

  return (
    <div className="container">
      {/* Sidebar */}
      <div className="sidebar">
        <h1>Search</h1>
        <input
          type="text"
          id="searchInput"
          placeholder="Enter search query"
          value={query}
          onChange={(e) => setQuery(e.target.value)} // Update query state
        />
        <button onClick={searchArxiv}>Search Arxiv</button>
        <button onClick={searchRag}>Search RAG</button>
      </div>

      {/* Main content area for displaying results */}
      <div className="main-content">
        {results && (
          <div className="results-container">
            {results.map((result: any, index: number) => (
              <div key={index} className="card">
                <h3>{result.title}</h3>
                <p>{result.summary}</p>
                
                {/* Display the PDF link for Arxiv results */}
                {result.pdf_url && (
                  <div>
                    <a
                      href={result.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="pdf-link"
                    >
                      Download PDF
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

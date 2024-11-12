"use client";

import { useState } from "react";

// Define the response structure
interface Message {
  content: string;
}

interface SearchResponse {
  messages?: Message[];
  error?: string;
}

export default function Home() {
  const [query, setQuery] = useState<string>("");
  const [results, setResults] = useState<Message[] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Function to handle the search query
  const searchQuery = async () => {
    const requestData = {
      input: query,
      state: {}, // Initialize with an empty state
    };

    setLoading(true);
    setResults(null);

    try {
      // Send request to the FastAPI backend
      const response = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      const data: SearchResponse = await response.json();

      // Set the results based on the backend response
      if (data.messages) {
        setResults(data.messages);
      } else if (data.error) {
        setResults([{ content: `Error: ${data.error}` }]);
      }
    } catch (error) {
      console.error("Error:", error);
      setResults([{ content: "An error occurred while fetching results." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Research Paper Search</h1>
      <input
        type="text"
        placeholder="Enter search query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={searchQuery} disabled={loading}>
        {loading ? "Searching..." : "Search"}
      </button>

      {results && (
        <div>
          <h2>Results:</h2>
          <ul>
            {results.map((message, index) => (
              <li key={index}>{message.content}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

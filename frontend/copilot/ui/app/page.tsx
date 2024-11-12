// app/page.tsx
"use client";

import { useState } from "react";

interface ArxivResult {
  title: string;
  authors: string[];
  summary: string;
}

export default function Home() {
  const [query, setQuery] = useState<string>("");
  const [results, setResults] = useState<ArxivResult[] | null>(null);

  const searchArxiv = async () => {
    const maxResults = 5;

    const requestData = {
      messages: [{ content: query }], // Wrap query in messages array
      max_results: maxResults,
    };

    try {
      // page.tsx (or ChatComponent.tsx)
      const response = await fetch("http://localhost:8000/copilotkit_remote", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div>
      <h1>Hello, World from Next.js!</h1>
      <input
        type="text"
        placeholder="Enter search query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={searchArxiv}>Search</button>

      {results && (
        <div>
          <h2>Results:</h2>
          <ul>
            {results.map((result, index) => (
              <li key={index}>
                <strong>{result.title}</strong> - {result.authors.join(", ")}
                <p>{result.summary}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

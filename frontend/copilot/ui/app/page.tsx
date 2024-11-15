"use client";

import { useState, createContext, useContext } from "react";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotReadable } from "@copilotkit/react-core";
import { marked } from 'marked'; // Updated import for marked
import "./styles.css"; // Import the CSS file

// Create context for sharing search results
const SearchContext = createContext<any>(null);

export function useSearchContext() {
  const context = useContext(SearchContext);
  if (!context) {
    throw new Error("useSearchContext must be used within a SearchProvider");
  }
  return context;
}

export default function Home() {
  const [query, setQuery] = useState(""); // State for capturing query input
  const [results, setResults] = useState<any[]>([]); // Initialize results as an empty array
  const [combinedData, setCombinedData] = useState<string>(""); // State to store combined data

  // Share `results` with CopilotKit using `useCopilotReadable`
  useCopilotReadable({
    description: "Search results from the user's query",
    value: results,
    id: "search-results", // Unique identifier for the shared state
  });

  // Function to handle Arxiv search
  const searchArxiv = async () => {
    const maxResults = 5;
    const requestData = { query, max_results: maxResults };

    try {
      const response = await fetch("http://localhost:8000/copilotkit_remote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      const arxivResults = data.results || [{ title: "Error", summary: "No results found." }];

      // Update both results and combinedData
      setResults((prevResults) => [...prevResults, ...arxivResults]);
      updateCombinedData(arxivResults, 'arxiv'); // Append Arxiv results to combined data with specific formatting
    } catch (error) {
      console.error("Error:", error);
      setResults((prevResults) => [...prevResults, { title: "Error", summary: "Something went wrong." }]);
    }
  };

  // Function to handle RAG search
  const searchRag = async () => {
    const maxResults = 5;
    const requestData = { query, max_results: maxResults };

    try {
      const response = await fetch("http://localhost:8000/rag-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      const content = data.choices?.[0]?.message?.content;
      const ragResults = content ? [{ title: "RAG Search Result", summary: content }] : [{ title: "Error", summary: "No results found." }];

      // Update both results and combinedData
      setResults((prevResults) => [...prevResults, ...ragResults]);
      updateCombinedData(ragResults, 'rag'); // Append RAG results to combined data with specific formatting
    } catch (error) {
      console.error("Error:", error);
      setResults((prevResults) => [...prevResults, { title: "Error", summary: "Something went wrong." }]);
    }
  };

  // Function to handle Web Search using Tavily
  const searchWeb = async () => {
    const requestData = { query };

    try {
      const response = await fetch("http://localhost:8000/web-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      const webResults = data.context ? [{ title: "Web Search Result", summary: data.context }] : [{ title: "Error", summary: "No results found." }];

      // Update both results and combinedData
      setResults((prevResults) => [...prevResults, ...webResults]);
      updateCombinedData(webResults, 'web'); // Append Web search results to combined data with specific formatting
    } catch (error) {
      console.error("Error:", error);
      setResults((prevResults) => [...prevResults, { title: "Error", summary: "Something went wrong." }]);
    }
  };

  // Function to update combined data whenever new results are fetched
  const updateCombinedData = (newResults, source) => {
    let combinedText = "";

    // Add a newline before the query
    combinedText += `<br>**Query:** ${query}<br>`;

    // Format results based on their source
    newResults.forEach(result => {
      if (source === 'arxiv') {
        combinedText += `<br>**${result.title}**<br>**Summary:**\n${result.summary}`;
        if (result.pdf_url) {
          combinedText += `<br><a href="${result.pdf_url}" style="color: blue;">[Download PDF]</a>\n\n`;
        }
      } else if (source === 'rag') {
        combinedText += `${result.title}<br><br>${result.summary}<br>\n\n`;
      } else if (source === 'web') {
        combinedText += `${result.title}<br><br>**Response:**<br>${result.summary}<br>`;
        if (result.url) {
          combinedText += `[Read More](${result.url})\n\n`;
        }
      }
    });

    // Update combinedData with markdown-formatted content
    setCombinedData(prev => prev + combinedText);
  };

  // Convert the entire combinedData to Markdown format and render HTML
  const markdownContent = marked(combinedData);

  // Function to download combinedData as a .md file
  const downloadMarkdown = () => {
    const blob = new Blob([combinedData], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "combined_output.md";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <SearchContext.Provider value={{ results }}>
      <CopilotSidebar
        defaultOpen={true}
        instructions="You are assisting the user as best as you can. Answer in the best way possible given the data you have."
        labels={{
          title: "Sidebar Assistant",
          initial: "How can I help you today?",
        }}
      >
        <div className="container">
          <div className="sidebar">
            <h1>Search</h1>
            <input
              type="text"
              id="searchInput"
              placeholder="Enter search query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button onClick={searchArxiv}>Search Arxiv</button>
            <button onClick={searchRag}>Search RAG</button>
            <button onClick={searchWeb}>Search Web</button>
            <button onClick={downloadMarkdown}>Download Markdown</button>
          </div>

          <div className="main-content">
            {Array.isArray(results) && results.length > 0 ? (
              <div className="results-container">
                {results.map((result, index) => (
                  <div key={index} className="card">
                    <h3>{result.title}</h3>
                    <p>{result.summary}</p>

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
            ) : (
              <p>No results to display.</p>
            )}

            <div className="card combined-data-container">
              <h2>Combined Output (Markdown)</h2>
              <div dangerouslySetInnerHTML={{ __html: markdownContent }} />
            </div>
          </div>
        </div>
      </CopilotSidebar>
    </SearchContext.Provider>
  );
}

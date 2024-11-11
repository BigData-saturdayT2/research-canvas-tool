import { useState } from "react";

export default function Home() {
  const [query, setQuery] = useState(""); // State for capturing query input
  const [results, setResults] = useState<any>(null); // State for storing results

  // Function to handle the form submission
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
      setResults(data.results); // Update the state with the results
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div>
      <h1>Hello, World from Next.js!</h1>
      <p>This is a basic Next.js setup located in frontend/copilot/ui/.</p>

      <input
        type="text"
        id="searchInput"
        placeholder="Enter search query"
        value={query}
        onChange={(e) => setQuery(e.target.value)} // Update query state
      />
      <button onClick={searchArxiv}>Search</button>

      <div>
        {results && (
          <div>
            <h2>Results:</h2>
            <ul>
              {results.map((result: any, index: number) => (
                <li key={index}>{result}</li> // Assuming the result is a list
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

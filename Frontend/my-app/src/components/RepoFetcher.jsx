/*import React, { useState, useEffect, useRef } from 'react';

function RepoFetcher() {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState('');
  const vizRef = useRef(null);  // Reference to the div where the graph will be rendered

  // Function to draw the Neo4j graph using Neovis.js
  const drawGraph = () => {
    const config = {
      container_id: vizRef.current,  // Use the ref to target the div
      //server_url: "bolt://127.0.0.1:7687",  // Adjust the Neo4j connection
      server_url: "bolt://localhost:7687/neo4j",
      server_user: "neo4j",
      server_password: "horizon3",
      labels: {
        "Directory": { "caption": "name" },
        "File": { "caption": "name" }
      },
      relationships: {
        "CONTAINS": { "caption": false }
      },
      initial_cypher: "MATCH (n)-[r:CONTAINS]->(m) RETURN n,r,m"
    };

    const viz = new window.NeoVis.default(config);
    viz.render();
  };

  // API call to the backend when the user clicks "Fetch Repo"
  const handleFetch = async () => {
    setStatus('Fetching...');

    try {
      // Call to your backend API to process the GitHub repository
      const response = await fetch('/api/fetch-repo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('Successfully stored in Neo4j!');
        drawGraph();  // Draw the graph after successful storage
      } else {
        setStatus(`Error: ${data.message}`);
      }
    } catch (error) {
      setStatus('An error occurred.');
    }
  };

  // Load Neovis.js script dynamically
  useEffect(() => {
    const script = document.createElement('script');
    script.src = "https://unpkg.com/neovis.js@2.0.2/dist/neovis.js";
    script.async = true;
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);  // Clean up script on component unmount
    };
  }, []);

  return (
    <div>
      <h1>Fetch GitHub Repository</h1>
      <input
        type="text"
        placeholder="GitHub Repository URL"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />
      <button onClick={handleFetch}>Fetch Repo</button>
      <p>{status}</p>

      
      <div ref={vizRef} style={{ width: '400px', height: '300px', marginTop: '100px' }}></div>
    </div>
  );
}

export default RepoFetcher; */



import React, { useState } from 'react';

function RepoFetcher() {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState('');

  const handleFetch = async () => {
    setStatus('Fetching...');

    try {
      // API call to the backend
      const response = await fetch('/api/fetch-repo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('Successfully stored in Neo4j!');
        //drawGraph();
      } else {
        setStatus(`Error: ${data.message}`);
      }
    } catch (error) {
      setStatus('An error occurred.');
    }
  };

  return (
    <div>
      <h1>Fetch GitHub Repository</h1>
      <input
        type="text"
        placeholder="GitHub Repository URL"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />
      <button onClick={handleFetch}>Fetch Repo</button>
      <p>{status}</p>
    </div>
  );
}

export default RepoFetcher; 

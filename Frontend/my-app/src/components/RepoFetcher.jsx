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
        //visualizeGraph();
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


/*import React, { useState, useRef } from 'react';
import NeoVis from 'neovis.js'; // Import Neovis.js

function RepoFetcher() {
    const [url, setUrl] = useState(''); // State for the repository URL input
    const [status, setStatus] = useState(''); // State for status messages
    const vizRef = useRef(null); // Reference to the div where the graph will be rendered

    const drawGraph = () => {
        const config = {
            container_id: vizRef.current, // ID of the container to render the graph
            server_url: "bolt://127.0.0.1:7687", // Neo4j connection details
            server_user: "neo4j",
            server_password: "horizon3",
            labels: {
                "Directory": { "caption": "name" }, // Label configurations
                "File": { "caption": "name" }
            },
            relationships: {
                "CONTAINS": { "caption": false } // Relationship configurations
            },
            initial_cypher: "MATCH (n)-[r:CONTAINS]->(m) RETURN n,r,m" // Initial Cypher query
        };

        const viz = new NeoVis(config); // Create a new Neovis instance

        // Handle errors and completion events
        viz.registerOnEvent('error', (err) => {
            console.error('Error while rendering Neo4j graph:', err);
            setStatus('Error rendering Neo4j graph.');
        });

        viz.registerOnEvent('completed', () => {
            if (!viz.network.body.data.nodes.length) {
                setStatus('No graph data available.');
            } else {
                setStatus('Graph rendered successfully!');
            }
        });

        viz.render(); // Render the graph
    };

    const handleFetch = async () => {
        setStatus('Fetching...');

        try {
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
                drawGraph(); // Draw the graph after successful storage
            } else {
                setStatus(`Error: ${data.message}`);
            }
        } catch (error) {
            setStatus('An error occurred while fetching the repo.');
        }
    };

    // No need for useEffect to load Neovis since it's imported
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

            <div ref={vizRef} style={{ width: '800px', height: '600px', marginTop: '20px' }}></div> 
        </div>
    );
}

export default RepoFetcher; */





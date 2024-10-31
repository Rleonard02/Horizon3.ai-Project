import React, { useState } from 'react';

//const QueryForm = () => {
function QueryForm() {
    const [formData, setFormData] = useState({
        name: '',
        path: '',
        type: '',
        size: '',
        sha: ''
    });
    const [results, setResults] = useState([]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prevData) => ({
            ...prevData,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const queryParams = new URLSearchParams(formData).toString();
        
        // Send request to backend API
        const response = await fetch(`/api/query-metadata`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ formData }),
            //body: JSON.stringify({ queryParams }),

        });
        const data = await response.json();
        setResults(data);  // Store results in state
    };

    return (
        <div>
            <h1>Metadata Query</h1>
            <form onSubmit={handleSubmit}>
                <label>
                    Name:
                    <input type="text" name="name" value={formData.name} onChange={handleChange} />
                </label><br />
                
                <label>
                    Path:
                    <input type="text" name="path" value={formData.path} onChange={handleChange} />
                </label><br />
                
                <label>
                    Type:
                    <input type="text" name="type" value={formData.type} onChange={handleChange} />
                </label><br />
                
                <label>
                    Size:
                    <input type="number" name="size" value={formData.size} onChange={handleChange} />
                </label><br />
                
                <label>
                    SHA:
                    <input type="text" name="sha" value={formData.sha} onChange={handleChange} />
                </label><br />
                
                <button type="submit">Submit</button>
            </form>

            <h2>Query Results:</h2>
            <div>
                {results.length > 0 ? (
                    results.map((item, index) => (
                        <div key={index}>
                            <p><strong>Name:</strong> {item.name}</p>
                            <p><strong>Path:</strong> {item.path}</p>
                            <p><strong>Type:</strong> {item.type}</p>
                            <p><strong>Size:</strong> {item.size}</p>
                            <p><strong>SHA:</strong> {item.sha}</p>
                            <hr />
                        </div>
                    ))
                ) : (
                    <p>No results found.</p>
                )}
            </div>
        </div>
    );
};

export default QueryForm;

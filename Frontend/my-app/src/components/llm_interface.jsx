import React, { useState } from 'react';

function QueryLLM() {
    const [formData, setFormData] = useState({
        Vulnerability: '',
    });
    const [results, setResults] = useState([]);

    // Update form state on input change
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prevData) => ({
            ...prevData,
            [name]: value
        }));
    };

    // Handle form submission
    const handleSubmit = async (e) => {
        e.preventDefault();

        // Construct query params based on form data
        const queryParams = new URLSearchParams(formData).toString();
        
        // Send request to backend API with the search query
        const response = await fetch(`/api/query-LLM?${queryParams}`, {
            method: 'GET',
        });
        const data = await response.json();
        setResults(data); // Store results in state
    };

    return (
        <div>
            <h1>Search LLM Reports</h1>
            <form onSubmit={handleSubmit}>
                <label>
                    Vulnerability:
                    <input type="text" name="Vulnerability" value={formData.Vulnerability} onChange={handleChange} />
                </label><br />
                
                <button type="submit">Search</button>
            </form>

            <h2>Search Results:</h2>
            <div>
                {results.length > 0 ? (
                    results.map((item, index) => (
                        <div key={index}>
                            {Object.entries(item).map(([key, value]) => (
                                <p key={key}><strong>{key}:</strong> {value}</p>
                            ))}
                            <hr />
                        </div>
                    ))
                ) : (
                    <p>No results found.</p>
                )}
            </div>
        </div>
    );
}

export default QueryLLM;

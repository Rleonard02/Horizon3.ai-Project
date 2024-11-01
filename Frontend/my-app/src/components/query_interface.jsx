import React, { useState } from 'react';

function QueryInterface() {
    const [formData, setFormData] = useState({
        author: '',
        date: '',
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
        const response = await fetch(`/api/query-metadata?${queryParams}`, {
            method: 'GET',
        });
        const data = await response.json();
        setResults(data); // Store results in state
    };

    return (
        <div>
            <h1>Search Documents</h1>
            <form onSubmit={handleSubmit}>
                <label>
                    Author:
                    <input type="text" name="author" value={formData.author} onChange={handleChange} />
                </label><br />
                
                <label>
                    Date:
                    <input type="text" name="date" value={formData.date} onChange={handleChange} />
                </label><br />
                
                <button type="submit">Search</button>
            </form>

            <h2>Search Results:</h2>
            <div>
                {results.length > 0 ? (
                    results.map((item, index) => (
                        <div key={index}>
                            <p><strong>Author:</strong> {item.author}</p>
                            <p><strong>Date:</strong> {item.date}</p>
                            <p><strong>Hash:</strong> {item.hash}</p>
                            <p><strong>Message:</strong> {item.message}</p>
                            <p><strong>Tree:</strong> {item.tree}</p>
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

export default QueryInterface;

// frontend/src/components/OutputFiles.js

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';

function OutputFiles({ files }) {
  const [selectedFileContent, setSelectedFileContent] = useState('');
  const [selectedFileName, setSelectedFileName] = useState('');

  const handleFileClick = (filename) => {
    fetch(`http://localhost:8000/output_files/${filename}`)
      .then(response => {
        if (response.ok) {
          return response.text();
        } else {
          throw new Error('Error fetching file content');
        }
      })
      .then(data => {
        setSelectedFileName(filename);
        setSelectedFileContent(data);
      })
      .catch(error => console.error('Error fetching file content:', error));
  };

  const handleDownload = (filename) => {
    const link = document.createElement('a');
    link.href = `http://localhost:8000/output_files/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      <ul>
        {files.map((filename) => (
          <li key={filename}>
            <button onClick={() => handleFileClick(filename)}>{filename}</button>
            <button onClick={() => handleDownload(filename)}>Download</button>
          </li>
        ))}
      </ul>
      {selectedFileContent && (
        <div>
          <h3>{selectedFileName}</h3>
          {selectedFileName.endsWith('.md') ? (
            <ReactMarkdown>{selectedFileContent}</ReactMarkdown>
          ) : (
            <pre>{selectedFileContent}</pre>
          )}
        </div>
      )}
    </div>
  );
}

export default OutputFiles;

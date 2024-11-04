import React, { useState } from 'react';

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

  return (
    <div>
      <ul>
        {files.map((filename) => (
          <li key={filename}>
            <button onClick={() => handleFileClick(filename)}>{filename}</button>
          </li>
        ))}
      </ul>
      {selectedFileContent && (
        <div>
          <h3>{selectedFileName}</h3>
          <pre>{selectedFileContent}</pre>
        </div>
      )}
    </div>
  );
}

export default OutputFiles;

import React, { useEffect, useState } from 'react';
import ServiceStatus from './ServiceStatus';
import OutputFiles from './OutputFiles';

function Dashboard() {
  const [services, setServices] = useState([]);
  const [outputFiles, setOutputFiles] = useState([]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setServices(data.services);
    };
    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    fetch('http://localhost:8000/output_files')
      .then(response => response.json())
      .then(data => setOutputFiles(data.files))
      .catch(error => console.error('Error fetching output files:', error));
  }, []);

  return (
    <div>
      <h1>Pipeline Status</h1>
      {services.map((service) => (
        <ServiceStatus key={service.service} service={service} />
      ))}
      <h2>Output Files</h2>
      <OutputFiles files={outputFiles} />
    </div>
  );
}

export default Dashboard;

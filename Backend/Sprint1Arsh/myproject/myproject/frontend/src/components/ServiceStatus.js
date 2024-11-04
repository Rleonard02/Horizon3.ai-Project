// frontend/src/components/ServiceStatus.js

import React from 'react';

function ServiceStatus({ service }) {
  return (
    <div style={{ border: '1px solid #ccc', padding: '10px', margin: '10px' }}>
      <h2>{service.service}</h2>
      <p>Status: {service.status}</p>
      <p>Progress: {service.progress}%</p>
      <p>Message: {service.message}</p>
    </div>
  );
}

export default ServiceStatus;

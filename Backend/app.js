const express = require('express');
const apiRouter = require('./api');
const { driver } = require('./neo4jHandler'); 
const { client } = require('./mongodb.js');
const app = express();
const port = 4000;

// Middleware to parse JSON bodies
app.use(express.json());
//app.use(cors());

// Use the API router
app.use('/api', apiRouter);

// Start the server
app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});

// Optional: Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('Shutting down server...');
  // Perform any cleanup if necessary
  await client.close();
  await driver.close();
  process.exit();
});

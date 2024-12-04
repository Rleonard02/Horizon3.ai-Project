const express = require('express');
const { fetchGithubRepo, parseGithubUrl } = require('./githubRepoHandler');
const { storeRepoInNeo4j } = require('./neo4jHandler');
const { exec } = require('child_process'); // Correctly importing exec
const { MongoClient } = require('mongodb');
require('dotenv').config();
const { connectToMeta } = require('./mongodb');
const { connectToLLM } = require('./mongoLLM');


const dest_url = process.env.LOCAL_DEST;

const router = express.Router();

//Save LLM Module output to MongoDB in Analysis/llmAnalysis
router.post('/save-to-LLM', async (req, res) => {
  console.log('Request received at /save-to-llm');
  const { report } = req.body;

  try {
    const db = await connectToLLM(); // Connect to MongoDB
    const collection = db.collection('llmAnalysis'); // Choose a collection (e.g., 'commits')
    
    const results = await collection.insertOne(report);
    res.status(200).json(results);

  
} catch (error) {
    console.error('Error saving the LLM report to mongo');
    res.status(200).json({ message: 'Report saved successfully', result });
    //res.status(500).json({ error: 'Failed to save report' })
}

});

router.get('/query-LLM', async (req, res) => {
  console.log('Request received at /query-llm');
  

  try {
    const db = await connectToLLM(); // Connect to MongoDB
    const collection = db.collection('llmAnalysis'); // Choose a collection (e.g., 'commits')
    //const { name, path, type, sha } = req.body;
    // build the query
    const query = {};
    if (req.query.Vulnerability) query.Vulnerability = req.query.Vulnerability;
        // Dynamically add fields to the query if present in the request
        //if (name) query.author = name;
        //if (req.query.name) query.author = req.query.name;
        //if (req.query.path) query.path = req.query.path;
        //if (req.query.type) query.type = req.query.type;
        //if (req.query.size) query.size = parseInt(req.query.size); // If you want exact size match
        //if (req.query.sha) query.sha = req.query.sha;
        console.log(`query:`, JSON.stringify(query));
        // Perform the MongoDB query
        const results = await collection.find(query).toArray();
        console.log(`results: ${results}`);
        res.status(200).json(results);

  
} catch (error) {
    console.error('Error querying the LLM report');
}

});

router.get('/query-metadata', async (req, res) => {
  console.log('Request received at /query-metadata');
  

  try {
    const db = await connectToMeta(); // Connect to MongoDB
    const collection = db.collection('metadata'); // Choose a collection (e.g., 'commits')
    //const { name, path, type, sha } = req.body;
    // build the query
    const query = {};
    if (req.query.author) query.author = req.query.author;
    console.log(`author: ${req.query.author}`);
    if (req.query.date) query.date = req.query.date;
    if (req.query.hash) query.hash = req.query.hash;
        // Dynamically add fields to the query if present in the request
        //if (name) query.author = name;
        //if (req.query.name) query.author = req.query.name;
        //if (req.query.path) query.path = req.query.path;
        //if (req.query.type) query.type = req.query.type;
        //if (req.query.size) query.size = parseInt(req.query.size); // If you want exact size match
        //if (req.query.sha) query.sha = req.query.sha;

        // Perform the MongoDB query
        const results = await collection.find(query).toArray();
        console.log(`results: ${results}`);
        res.status(200).json(results);

  
} catch (error) {
    console.error('Error querying the metadata');
}

});


// POST endpoint to fetch a GitHub repo and store it in Neo4j
router.post('/fetch-repo', async (req, res) => {
  console.log('Request received at /fetch-repo');
  const { url } = req.body;

  try {

    //input functionality to clone repository here
    const cloneRepo = (url, dest_url) => {
      return new Promise((resolve, reject) => {
        // Command to clone the repo
        const command = `git -C "${dest_url}" pull || git clone "${url}" "${dest_url}"`;
        
        exec(command, (error, stdout, stderr) => {
          if (error) {
            console.error(`Error cloning repository: ${stderr}`);
            reject(`Error: ${stderr}`);
          } else {
            resolve(stdout);
          }
        });
      });
    };
    await cloneRepo(url, dest_url);
    const getCommits = (dest_url) => {
      return new Promise((resolve, reject) => {
        const command = `git -C "${dest_url}" log --pretty=format:'%H:%T:%an:%ad:%s'`; // Customize the format as needed
    
        exec(command, (error, stdout, stderr) => {
          if (error) {
            console.error(`Error fetching commits: ${stderr}`);
            reject(`Error: ${stderr}`);
          } else {
            resolve(stdout.split('\n')); // Split the output into an array of commits
          }
        });
      });
    };

    async function saveCommitsToMongo(commits) {
      try {
          const db = await connectToMeta(); // Connect to MongoDB
          const collection = db.collection('metadata'); // Choose a collection (e.g., 'commits')
          //console.log('in saveCommitstoMongo after getting metadata collection');
          // Insert all commit objects into MongoDB at once
          await collection.createIndex({ hash: 1 }, { unique: true });
          const result = await collection.insertMany(commits, {ordered: false});
          console.log('Commits successfully saved to MongoDB:', result);
      } catch (error) {
          if (error.code === 11000) {
            console.log('Duplicate hashes detected, ignore duplicates')
          }
          console.error('Error saving commits to MongoDB:', error);
      }
  }
/*
    async function saveCommitsToMongo(commits) {
      try {
          const db = await connectToDB(); // Connect to MongoDB
          const collection = db.collection('metadata'); // Choose a collection (e.g., 'commits')
          //console.log('in saveCommitstoMongo after getting metadata collection');
          // Insert all commit objects into MongoDB at once
          const result = await collection.insertMany(commits);
          console.log('Commits successfully saved to MongoDB:', result);
      } catch (error) {
          console.error('Error saving commits to MongoDB:', error);
      }
  }
*/
    // now add functionality to loop over all commits?
    getCommits(dest_url)
    .then(commits => {
        // Loop through the commits array
        const commitObjects = commits.map(commit => {
            const [hash, tree, author, date, message] = commit.split(':');
            return {
              hash,
                tree,
                author,
                date,
                message
            };
        });

        saveCommitsToMongo(commitObjects);
    })
    .catch(error => {
        console.error('Failed to retrieve commits:', error);
    });

    // Parse the GitHub URL to extract owner and repo
    const { owner, repo } = parseGithubUrl(url);
    console.log('Owner:', owner, 'Repo:', repo);

    // Fetch the repository structure
    const {nodes, relationships} = await fetchGithubRepo(owner, repo);
    //console.log('Repository Structure:', JSON.stringify(repoStructure,null,2));

    // Store the repository structure in Neo4j
    await storeRepoInNeo4j(nodes, relationships);

    res.status(200).json({ message: 'Repository structure stored successfully' });

    //need to call the graph visualization here
  } catch (error) {
    console.error('Error fetching repository:', error);
    res.status(500).json({ error: 'Failed to fetch or store the repository structure' });
  }
});


module.exports = router;

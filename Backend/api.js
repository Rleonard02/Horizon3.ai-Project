const express = require('express');
const { fetchGithubRepo, parseGithubUrl } = require('./githubRepoHandler');
const { storeRepoInNeo4j } = require('./neo4jHandler');
const { exec } = require('child_process'); // Correctly importing exec
const { MongoClient } = require('mongodb');
require('dotenv').config();
const { connectToDB } = require('./mongodb');




const router = express.Router();

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
    const dest_url = "C:/Users/kahow/Documents/Senior Project/Sample Repo/ClonePath";
    await cloneRepo(url, dest_url);
    const repoPath = "C:/Users/kahow/Documents/Senior Project/Sample Repo/ProjectHierarchy";
    const getCommits = (repoPath) => {
      return new Promise((resolve, reject) => {
        const command = `git -C "${repoPath}" log --pretty=format:'%H:%T:%an:%ad:%s'`; // Customize the format as needed
    
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
          const db = await connectToDB(); // Connect to MongoDB
          const collection = db.collection('metadata'); // Choose a collection (e.g., 'commits')
          
          // Insert all commit objects into MongoDB at once
          const result = await collection.insertMany(commits);
          console.log('Commits successfully saved to MongoDB:', result);
      } catch (error) {
          console.error('Error saving commits to MongoDB:', error);
      }
  }

    // now add functionality to loop over all commits?
    getCommits(repoPath)
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

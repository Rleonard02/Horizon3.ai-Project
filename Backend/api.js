const express = require('express');
const { fetchGithubRepo, parseGithubUrl } = require('./githubRepoHandler');
const { storeRepoInNeo4j } = require('./neo4jHandler');
const { exec } = require('child_process'); // Correctly importing exec

const router = express.Router();

// POST endpoint to fetch a GitHub repo and store it in Neo4j
router.post('/fetch-repo', async (req, res) => {
  console.log('Request received at /fetch-repo');
  const { url } = req.body;

  try {
    //input functionality to clone repository here
    const cloneRepo = (url) => {
      return new Promise((resolve, reject) => {
        // Command to clone the repo
        const command = `git clone ${url} ./repository`;
        
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

    await cloneRepo(url);

    // now add functionality to loop over all commits?

    
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

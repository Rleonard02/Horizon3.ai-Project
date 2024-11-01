const axios = require('axios');

// Helper function to parse the GitHub repository URL
function parseGithubUrl(url) {
  // Remove .git if present
  console.log('url: ', url);
  if (url.endsWith('.git')) {
    url = url.slice(0, -4); // Remove the last 4 characters
  }

  const regex = /github\.com\/([^/]+)\/([^/.]+)/; // Updated regex to exclude .git
  const match = url.match(regex);
  if (!match) {
    throw new Error('Invalid GitHub URL'); // Error for invalid URL format
  }
  console.log('owner = ', match[1]);
  console.log('repo = ', match[2]);
  return { owner: match[1], repo: match[2] }; // Return owner and repo name
}

// Function to fetch the repository data from GitHub
async function fetchGithubRepo(owner, repo, path = '') {
  try {
    const apiUrl = `https://api.github.com/repos/${owner}/${repo}/git/trees/main?recursive=1`;

    // Make an HTTP GET request to the GitHub API
    const response = await axios.get(apiUrl);
    const contents = response.data;
    console.log('contents', contents)


    //new changes could break it
    //const structure = [];
    const nodes = [];
    const relationships = [];

    for (const item of contents.tree) {
        const parts = item.path.split('/');
        let parentPath = null;
    
        parts.forEach((part, index) => {
          const currentPath = parts.slice(0, index + 1).join('/');
          const isFile = index === parts.length - 1 && item.type === 'blob';
    
          // Create node if it doesn't exist
          if (!nodes.find(node => node.path === currentPath)) {
            nodes.push({
              name: part,
              path: currentPath,
              type: isFile ? 'file' : 'directory',
              size: item.size,
              sha: item.sha,
              
            });
          }
    
          // Create relationship to the parent node
          if (parentPath) {
            relationships.push({
              parentPath,
              childPath: currentPath,
            });
          }
    
          // Update parentPath for the next level
          parentPath = currentPath;
        });
      }
    
    // Return the repository file structure
    return {nodes, relationships};
  } catch (error) {
    console.error('Error fetching GitHub repository:', error);
    throw error;
  } 
}

module.exports = {
  fetchGithubRepo, parseGithubUrl
};

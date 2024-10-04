const neo4j = require('neo4j-driver');

// Replace with your Neo4j credentials
const neo4jUri = 'bolt://localhost:7687'; 
const neo4jUser = 'neo4j'; 
const neo4jPassword = 'horizon3'; // Update your password here

// Initialize Neo4j driver
const driver = neo4j.driver('bolt://127.0.0.1:7687', neo4j.auth.basic('neo4j', 'horizon3'),
{encrypted: 'ENCRYPTION_OFF'}
);
//const session = driver.session();
// Function to add nodes (files and directories) to Neo4j
async function addNode(session, path, type, size = null) {
  const query = `
    MERGE (n:${type} {path: $path})
    SET n.size = $size
  `;
  try {
    await session.run(query, { path, size });
  } catch (error) {
    console.error('Error running Neo4j query:', error);
    throw error;
  }
} 

// Function to add relationships (edges) between nodes in Neo4j
async function addEdge(session, fromPath, toPath) {
  const query = `
    MATCH (a {path: $fromPath}), (b {path: $toPath})
    MERGE (a)-[:CONTAINS]->(b)
  `;
  try {
    await session.run(query, { fromPath, toPath });
  } catch (error) {
    console.error('Error running Neo4j query:', error);
    throw error;
  }
}

//new test store function
async function storeRepoInNeo4j(nodes, relationships) {
  const session = driver.session();
  try {
    for (const node of nodes) {
      const name = node.path.split('/').pop();
      await session.run(
        'MERGE (n {name: $name, path: $path, type: $type}) RETURN n',
        {
          name: name,
          path: node.path,
          type: node.type,
          sha: node.sha,
        }
      );
    }
  
    // Then, store the relationships
    for (const rel of relationships) {
      await session.run(
        'MATCH (parent {path: $parentPath}), (child {path: $childPath}) ' +
        'MERGE (parent)-[:CONTAINS]->(child)',
        {
          parentPath: rel.parentPath,
          childPath: rel.childPath,
        }
      );
    }
  } catch (error) {
    console.error('Error storing data in Neo4j:', error);
    throw error; // Rethrow the error to be handled by the caller
  } finally {
    await session.close(); // Close the session
  }
}

// Export functions for use in other modules
module.exports = {
  storeRepoInNeo4j,
  driver // Export the driver if you need to close it later
};

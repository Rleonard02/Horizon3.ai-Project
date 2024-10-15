const neo4j = require('neo4j-driver');
require('dotenv').config(); // Load environment variables from .env file

const neo_name = process.env.NEO_NAME;
const neo_pass = process.env.NEO_PASS;

// Initialize Neo4j driver
const driver = neo4j.driver('bolt://127.0.0.1:7687', neo4j.auth.basic(neo_name, neo_pass),
{encrypted: 'ENCRYPTION_OFF'}
);
//const session = driver.session();


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

// mongodb.js
//https://github.com/Kace33/ProjectHierarchy.git
const { MongoClient, ServerApiVersion } = require('mongodb');
require('dotenv').config(); // Load environment variables from .env file
const uri = process.env.MONGO_URI;

/*const client = new MongoClient(uri, {
    serverApi: {
      version: ServerApiVersion.v1,
      strict: true,
      deprecationErrors: true,
    }
  }); */

  const client2 = new MongoClient(uri, {
    //tls: true,  // Explicitly enable TLS
    useNewUrlParser: true,
    useUnifiedTopology: true,  // Or try setting this to false if needed
    serverApi: {
      version: ServerApiVersion.v1,
      strict: true,
      deprecationErrors: true,
    },
  });
//closing connection before I get to send the data
  async function connectToLLM() {
    try {
      // Connect the client to the server	(optional starting in v4.7)
      await client2.connect();
      //console.log("trying to connect here");
      // Send a ping to confirm a successful connection
      //does admin need to be switched out for Horizon3?
      await client2.db("admin").command({ ping: 1 });
      console.log("Pinged your deployment. You successfully connected to MongoDB!");

      //the following line previously had metadata instead of horizon3
      return client2.db("Analysis");
    } catch (error) {
        console.error("Error connecting to MongoDB:", error);
        throw error;
    }
  }
module.exports = { connectToLLM, client2 };

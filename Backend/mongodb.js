// mongodb.js
const { MongoClient, ServerApiVersion } = require('mongodb');
require('dotenv').config(); // Load environment variables from .env file
const uri = process.env.MONGO_URI;
//const uri = `mongodb+srv://mongoDB:${MONGO_PASS}@metadata.hymc1.mongodb.net/?retryWrites=true&w=majority`;

/*const client = new MongoClient(uri, {
    serverApi: {
      version: ServerApiVersion.v1,
      strict: true,
      deprecationErrors: true,
    }
  }); */

  const client = new MongoClient(uri, {
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
  async function connectToDB() {
    try {
      // Connect the client to the server	(optional starting in v4.7)
      await client.connect();
      // Send a ping to confirm a successful connection
      await client.db("admin").command({ ping: 1 });
      console.log("Pinged your deployment. You successfully connected to MongoDB!");
      return client.db("metadata");
    } catch (error) {
        console.error("Error connecting to MongoDB:", error);
        throw error;
    }
  }
module.exports = { connectToDB, client };

const express = require("express");
const router = express.Router();
const {
  runStaticAnalysis,
} = require("../controllers/staticAnalysisController");

router.get("/", (req, res) => {
  res.send("Hello world!");
});

// POST route for triggering analysis
router.post("/analyze", runStaticAnalysis);

module.exports = router;

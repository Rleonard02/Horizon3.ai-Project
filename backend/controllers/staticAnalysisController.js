const { exec } = require("child_process");
const { runSonarQube } = require("../services/sonarqubeService");

const runStaticAnalysis = (req, res) => {
  const { githubUrl } = req.body;

  // Step 1: Clone the repo using the Python script
  const cloneCommand = `python3 ./backend/scripts/clone_repo.py ${githubUrl}`;

  exec(cloneCommand, (err, stdout, stderr) => {
    if (err) {
      console.error(`Error cloning repo: ${stderr}`);
      return res.status(500).json({ message: "Repository cloning failed." });
    }

    const repoName = githubUrl.split("/").pop();
    const repoPath = `./backend/cloned_repos/${repoName}`;

    console.log(`Repository ready at ${repoPath}, proceeding with analysis...`);

    // Step 2: Run SonarQube analysis
    runSonarQube(repoPath)
      .then((sonarResults) => {
        return res.status(200).json({
          message: "Static analysis complete",
          results: sonarResults,
        });
      })
      .catch((error) => {
        return res
          .status(500)
          .json({ message: "SonarQube analysis failed", error });
      });
  });
};

module.exports = {
  runStaticAnalysis,
};

const { exec } = require("child_process");
const { runSonarQube } = require("../services/sonarqubeService"); // Make sure this path is correct

const runStaticAnalysis = (req, res) => {
  const githubUrl = req.body.githubUrl; // Get the GitHub URL from the request body

  console.log(`Received GitHub URL: ${githubUrl}`);

  // Use absolute path to the Python script
  const scriptPath =
    "/Users/ming/Documents/Projects/407 Project/Horizon3.ai-Project/backend/scripts/clone_repo.py";
  console.log(`Running Python script at: ${scriptPath}`);

  // Prepare the command to run the Python script
  const cloneCommand = `python3 "${scriptPath}" ${githubUrl}`;

  // Execute the clone command
  exec(cloneCommand, (err, stdout, stderr) => {
    if (err) {
      console.error(`Error cloning repo: ${stderr}`);
      return res.status(500).json({ message: "Repository cloning failed." });
    }

    // Extract repo name and define the local path to the cloned repo
    const repoName = githubUrl.split("/").pop().replace(".git", "");
    const repoPath = `/Users/ming/Documents/Projects/407 Project/Horizon3.ai-Project/backend/cloned_repos/${repoName}`;

    console.log(`Repository ready at ${repoPath}, proceeding with analysis...`);

    // Step 2: Run SonarQube analysis
    runSonarQube(repoPath, repoName)
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

console.log("Static analysis controller loaded!"); // Debug log to ensure this file is loaded

module.exports = {
  runStaticAnalysis,
};

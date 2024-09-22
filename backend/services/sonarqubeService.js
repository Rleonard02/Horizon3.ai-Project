const { exec } = require("child_process");
const axios = require("axios");

const runSonarQube = (repoPath, projectKey) => {
  return new Promise((resolve, reject) => {
    // Start the SonarQube analysis
    const sonarCommand = `docker run -v $(pwd)/${repoPath}:/usr/src -p 9000:9000 sonarqube:latest -Dsonar.projectKey=${projectKey} -Dsonar.sources=.`;

    exec(sonarCommand, async (err, stdout, stderr) => {
      if (err) {
        console.error(`SonarQube error: ${stderr}`);
        reject("SonarQube analysis failed.");
      }

      try {
        // Fetch the analysis results via SonarQube's Web API
        const response = await axios.get(
          `http://localhost:9000/api/issues/search?projectKeys=${projectKey}`
        );
        resolve(response.data); // Send the result back
      } catch (apiError) {
        console.error(`Error fetching results from SonarQube API: ${apiError}`);
        reject("Failed to retrieve analysis results.");
      }
    });
  });
};

module.exports = {
  runSonarQube,
};

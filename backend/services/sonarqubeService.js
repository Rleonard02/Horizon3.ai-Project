const { exec } = require("child_process");
const axios = require("axios");

const runSonarQube = (repoPath, projectKey) => {
  return new Promise((resolve, reject) => {
    // SonarQube command to run analysis
    const sonarCommand = `docker run -v "${repoPath}:/usr/src" -p 9000:9000 sonarqube:latest -Dsonar.projectKey=${projectKey} -Dsonar.sources=/usr/src`;

    exec(sonarCommand, async (err, stdout, stderr) => {
      if (err) {
        console.error(`SonarQube error: ${stderr}`);
        return reject("SonarQube analysis failed.");
      }

      try {
        // Fetch the analysis results via SonarQube's Web API
        const response = await axios.get(
          `http://localhost:9000/api/issues/search?projectKeys=${projectKey}`,
          {
            headers: {
              Authorization: `Basic ${Buffer.from("admin:admin").toString(
                "base64"
              )}`, // Replace with your actual credentials or token
            },
          }
        );
        resolve(response.data); // Return the analysis result
      } catch (apiError) {
        console.error(`Error fetching results from SonarQube API: ${apiError}`);
        reject("Failed to retrieve analysis results.");
      }
    });
  });
};

console.log("SonarQube service loaded!"); // Debug log to ensure this file is loaded

module.exports = {
  runSonarQube,
};

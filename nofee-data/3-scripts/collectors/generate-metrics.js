const fs = require('fs');
const path = require('path');

// Read commit data
const frontCommits = JSON.parse(fs.readFileSync('./commits/nofee-front-commits.json', 'utf8'));
const springbootCommits = JSON.parse(fs.readFileSync('./commits/nofee-springboot-commits.json', 'utf8'));

// Read deployment data
const frontDeployments = JSON.parse(fs.readFileSync('./deployments/nofee-front-deployments.json', 'utf8'));
const springbootDeployments = JSON.parse(fs.readFileSync('./deployments/nofee-springboot-deployments.json', 'utf8'));

// Calculate metrics
const metrics = {
  generated_at: new Date().toISOString(),
  repositories: {
    "nofee-front": {
      type: "Next.js Frontend",
      total_commits: frontCommits.length,
      total_files: 168,
      total_lines: 15309,
      contributors: [...new Set(frontCommits.map(c => c.author))],
      first_commit: frontCommits[frontCommits.length - 1]?.date,
      last_commit: frontCommits[0]?.date,
      deployments: frontDeployments
    },
    "nofee-springboot": {
      type: "Spring Boot Backend",
      total_commits: springbootCommits.length,
      total_files: 338,
      total_lines: 35732,
      contributors: [...new Set(springbootCommits.map(c => c.author))],
      first_commit: springbootCommits[springbootCommits.length - 1]?.date,
      last_commit: springbootCommits[0]?.date,
      deployments: springbootDeployments
    }
  },
  overall_stats: {
    total_commits: frontCommits.length + springbootCommits.length,
    total_files: 168 + 338,
    total_lines: 15309 + 35732,
    total_contributors: [...new Set([...frontCommits.map(c => c.author), ...springbootCommits.map(c => c.author)])].length
  }
};

// Write to file
fs.writeFileSync('./metrics/overall-metrics.json', JSON.stringify(metrics, null, 2));
console.log('Metrics generated successfully!');

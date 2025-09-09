// check_compromised.js
// Script to check for installed packages with compromised versions
// Usage: node check_compromised.js


const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const compromisedPackagesFile = path.join(__dirname, 'compromised_versions.json');
const installedPackagesFile = path.join(__dirname, 'packagesversions.txt');

function generatePackagesVersions() {
  // Read compromised_versions.json and extract unique names
  const grepCmd = `./grep.sh`;
  try {
    console.log('Retrieving the versions of the affected packages ...');
    execSync(grepCmd, { stdio: 'inherit', cwd: __dirname, shell: '/bin/bash' });
    console.log('packagesversions.txt generated.');
  } catch (err) {
    console.error('Error when retrieving the versions of the affected packages:', err.message);
    cleanPackagesVersionsFile();
    process.exit(1);
  }
}

// Read and parse compromised versions
function getCompromisedList() {
  const data = fs.readFileSync(compromisedPackagesFile, 'utf8');
  const list = JSON.parse(data);
  // Map: { 'name@version': true }
  const map = new Map();
  for (const entry of list) {
    map.set(`${entry.name}@${entry.version}`, true);
  }
  return map;
}

// Parse installed packages from grep output (2 lines per package: name, version)
function getInstalledList() {
  const lines = fs.readFileSync(installedPackagesFile, 'utf8').split(/\r?\n/);
  const installed = [];
  for (let i = 0; i < lines.length; i += 2) {
    const nameMatch = lines[i] && lines[i].match(/"name":\s*"([^"]+)"/);
    const versionMatch = lines[i + 1] && lines[i + 1].match(/"version":\s*"([^"]+)"/);
    if (nameMatch && versionMatch) {
      installed.push({ name: nameMatch[1], version: versionMatch[1], raw: lines[i] + '\n' + lines[i + 1] });
    }
  }
  return installed;
}

function cleanPackagesVersionsFile() {
  try {
    fs.unlinkSync(installedPackagesFile);
  } catch (err) {
    console.warn('Warning: Could not remove packagesversions.txt:', err.message);
  }
}

function main() {
  generatePackagesVersions();
  const compromised = getCompromisedList();
  const installed = getInstalledList();
  const found = [];

  for (const pkg of installed) {
    if (compromised.has(`${pkg.name}@${pkg.version}`)) {
      found.push(pkg);
    }
  }

  if (found.length === 0) {
    console.log('No compromised packages found.');
    cleanPackagesVersionsFile();
    return;
  }

  const reportLines = ['Compromised packages found:', ''];
  for (const pkg of found) {
    const line = `- ${pkg.name}@${pkg.version}`;
    reportLines.push(line);
    reportLines.push(pkg.raw);
    reportLines.push('');
  }
  cleanPackagesVersionsFile();

  const report = reportLines.join('\n');
  console.log(report);
}

main();

# NPM Package Vulnerability Checker

This directory contains a tool to check for compromised NPM packages in your Node.js projects, specifically targeting packages that were identified as compromised in a major security incident.

## Background

This script was created in response to significant vulnerabilities discovered in widely-used NPM packages, including popular libraries like `debug`, `chalk`, and others. These packages are dependencies for thousands of other libraries, making the potential impact of any compromise extremely widespread.

**Sources**: 
- [NPM Debug and Chalk packages compromised - Aikido Security](https://www.aikido.dev/blog/npm-debug-and-chalk-packages-compromised)
- [DuckDB npm account compromised in continuing supply chain attack - Socket Security](https://socket.dev/blog/duckdb-npm-account-compromised-in-continuing-supply-chain-attack)

The vulnerabilities affected numerous high-profile packages that are extensively used across the JavaScript ecosystem, potentially exposing countless applications to security risks. This represents part of a broader pattern of supply chain attacks targeting the npm ecosystem.

## Files Description

- **`check_compromised.js`** - Main Node.js script that checks for compromised package versions
- **`compromised_versions.json`** - JSON file containing the list of known compromised package names and versions
- **`grep.sh`** - Bash script that searches through `node_modules` to extract package information
- **`packagesversions.txt`** - Temporary file (auto-generated and cleaned up) containing extracted package versions

## Usage

### Prerequisites

- Node.js installed on your system
- A Node.js project with `node_modules` directory
- Unix-like environment (macOS, Linux) for bash script execution

### Running the Checker

1. Navigate to your Node.js project root directory (where `node_modules` is located)
2. Copy this entire `check_vulns` directory to your project
3. Run the vulnerability checker:

```bash
cd check_vulns
node check_compromised.js
```

### How It Works

1. **Package Discovery**: The script runs `grep.sh` which searches through your `node_modules` directory for packages that match the compromised package names
2. **Version Extraction**: It extracts the exact versions of installed packages and creates a temporary `packagesversions.txt` file
3. **Vulnerability Matching**: The script compares your installed packages against the known compromised versions in `compromised_versions.json`
4. **Report Generation**: If compromised packages are found, it displays a detailed report with package names, versions, and file locations
5. **Cleanup**: The temporary `packagesversions.txt` file is automatically removed after execution

### Output

- **No vulnerabilities found**: The script will report "No compromised packages found."
- **Vulnerabilities detected**: The script will display a detailed list of compromised packages including:
  - Package name and version
  - Raw package.json entries showing where the packages were found

## Example Output

```
Retrieving the versions of the affected packages ...
Compromised packages found:

- debug@4.3.0
"name": "debug",
"version": "4.3.0",

- chalk@5.1.2
"name": "chalk",
"version": "5.1.2",

```

## Important Notes

- This tool only checks for the specific compromised versions listed in `compromised_versions.json`
- Having these packages doesn't necessarily mean your application is compromised, but they should be updated immediately
- The script requires execution from a directory containing `node_modules`
- Make sure to update your package versions and review your dependencies after running this check

## Security Recommendations

If compromised packages are found:

1. **Immediate action**: Update all affected packages to their latest secure versions
2. **Dependency audit**: Run `npm audit` or `yarn audit` for additional security checks
3. **Lock file review**: Check your `package-lock.json` or `yarn.lock` for any suspicious changes
4. **Environment scanning**: Run this tool across all your Node.js projects
5. **Monitoring**: Implement ongoing dependency monitoring in your CI/CD pipeline

## Updating the Compromised List

To update the list of compromised packages, edit the `compromised_versions.json` file following the existing format:

```json
[
  {
    "name": "package-name",
    "version": "x.x.x"
  }
]
```

---

**Stay vigilant and keep your dependencies updated!**

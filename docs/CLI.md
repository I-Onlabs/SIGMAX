# SIGMAX CLI Documentation

The SIGMAX Command-Line Interface provides a powerful terminal-based interface for interacting with the SIGMAX trading system.

## Installation

### Install SIGMAX with CLI support

```bash
# Clone the repository
git clone https://github.com/I-Onlabs/SIGMAX.git
cd SIGMAX

# Install with CLI dependencies
pip install -e ".[cli]"
```

### Verify installation

```bash
sigmax --version
```

## Quick Start

### 1. Configure API Access

```bash
# Set your API key (required)
sigmax config set api_key YOUR_API_KEY

# Set custom API URL (optional, defaults to http://localhost:8000)
sigmax config set api_url https://api.sigmax.io

# View current configuration
sigmax config list
```

### 2. Check System Status

```bash
sigmax status
```

### 3. Analyze a Trading Pair

```bash
# Basic analysis
sigmax analyze BTC/USDT

# With custom risk profile
sigmax analyze ETH/USDT --risk balanced

# Streaming mode with live progress
sigmax analyze SOL/USDT --stream

# JSON output
sigmax analyze BTC/USDT --format json
```

## Commands Reference

### analyze

Analyze a trading pair and get AI-powered recommendations.

```bash
sigmax analyze <symbol> [OPTIONS]

Options:
  --risk, -r       Risk profile: conservative, balanced, aggressive [default: conservative]
  --mode, -m       Trading mode: paper, live [default: paper]
  --format, -f     Output format: text, json, table [default: text]
  --stream, -s     Enable streaming mode with live updates
```

**Examples:**
```bash
# Conservative analysis with text output
sigmax analyze BTC/USDT

# Balanced risk, streaming mode
sigmax analyze ETH/USDT --risk balanced --stream

# Aggressive analysis, JSON output
sigmax analyze SOL/USDT --risk aggressive --format json
```

### status

Display current SIGMAX system status.

```bash
sigmax status [OPTIONS]

Options:
  --format, -f     Output format: text, json, table [default: text]
  --verbose, -v    Show detailed status information
```

**Examples:**
```bash
# Basic status
sigmax status

# Verbose output with details
sigmax status --verbose

# JSON format for scripting
sigmax status --format json
```

### propose

Create a trade proposal.

```bash
sigmax propose <symbol> [OPTIONS]

Options:
  --size, -s       Position size in USD [optional]
  --risk, -r       Risk profile [default: conservative]
  --mode, -m       Trading mode [default: paper]
  --format, -f     Output format [default: text]
```

**Examples:**
```bash
# Create proposal with default size
sigmax propose BTC/USDT

# Specify position size
sigmax propose ETH/USDT --size 1000

# Balanced risk profile
sigmax propose SOL/USDT --risk balanced
```

### approve

Approve a pending trade proposal.

```bash
sigmax approve <proposal_id> [OPTIONS]

Options:
  --format, -f     Output format [default: text]
```

**Examples:**
```bash
sigmax approve PROP-abc123def456
```

### execute

Execute an approved trade proposal.

```bash
sigmax execute <proposal_id> [OPTIONS]

Options:
  --format, -f     Output format [default: text]
```

**Examples:**
```bash
sigmax execute PROP-abc123def456
```

### proposals

List all trade proposals.

```bash
sigmax proposals [OPTIONS]

Options:
  --format, -f     Output format [default: table]
  --status, -s     Filter by status: pending, approved, all
```

**Examples:**
```bash
# List all proposals
sigmax proposals

# Only pending proposals
sigmax proposals --status pending

# JSON format for scripting
sigmax proposals --format json
```

### config

Manage CLI configuration.

```bash
sigmax config <action> [KEY] [VALUE]

Actions:
  list             Show all configuration values
  get <key>        Get a specific configuration value
  set <key> <val>  Set a configuration value
```

**Examples:**
```bash
# View all configuration
sigmax config list

# Get specific value
sigmax config get api_url

# Set configuration value
sigmax config set api_key sk-1234567890abcdef
sigmax config set default_risk_profile balanced
```

**Available Configuration Keys:**
- `api_url` - SIGMAX API endpoint (default: http://localhost:8000)
- `api_key` - Your API authentication key (required)
- `default_risk_profile` - Default risk profile (conservative, balanced, aggressive)
- `default_mode` - Default trading mode (paper, live)
- `default_format` - Default output format (text, json, table)

### shell

Start an interactive SIGMAX shell (REPL).

```bash
sigmax shell
```

**Interactive Shell Features:**
- Command history (saved to ~/.sigmax/shell_history.txt)
- Tab completion for commands
- Simplified command syntax (no need to type "sigmax")
- Persistent session

**Shell Commands:**
```
sigmax> analyze BTC/USDT
sigmax> status
sigmax> propose ETH/USDT --risk balanced
sigmax> approve PROP-abc123
sigmax> proposals
sigmax> help
sigmax> exit
```

## Output Formats

### Text (Default)

Human-readable formatted output with colors and panels:

```bash
sigmax analyze BTC/USDT
```

### JSON

Machine-readable JSON for scripting and automation:

```bash
sigmax analyze BTC/USDT --format json
```

### Table

Structured table format for easy scanning:

```bash
sigmax proposals --format table
```

## Streaming Mode

For real-time analysis updates:

```bash
sigmax analyze BTC/USDT --stream
```

**Features:**
- Live progress updates during analysis
- Real-time agent reasoning steps
- Visual progress indicators
- Final comprehensive results

## Configuration File

Configuration is stored in `~/.sigmax/config.json`:

```json
{
  "api_url": "http://localhost:8000",
  "api_key": "sk-1234567890abcdef",
  "default_risk_profile": "conservative",
  "default_mode": "paper",
  "default_format": "text"
}
```

## Authentication

The CLI requires an API key for authentication. Set it using:

```bash
sigmax config set api_key YOUR_API_KEY
```

Or set the `SIGMAX_API_KEY` environment variable:

```bash
export SIGMAX_API_KEY=YOUR_API_KEY
sigmax status
```

## Scripting and Automation

### Example: Automated Analysis Pipeline

```bash
#!/bin/bash
# analyze-portfolio.sh

SYMBOLS=("BTC/USDT" "ETH/USDT" "SOL/USDT")

for symbol in "${SYMBOLS[@]}"; do
    echo "Analyzing $symbol..."
    sigmax analyze "$symbol" --format json > "analysis_${symbol//\//_}.json"
    sleep 2  # Rate limiting
done

echo "Analysis complete. Results saved."
```

### Example: Monitor and Auto-Approve

```bash
#!/bin/bash
# auto-approve.sh

# Get pending proposals
PROPOSALS=$(sigmax proposals --status pending --format json)

# Parse and approve proposals with high confidence
echo "$PROPOSALS" | jq -r '.[] | select(.confidence > 0.85) | .proposal_id' | \
while read -r pid; do
    echo "Auto-approving high-confidence proposal: $pid"
    sigmax approve "$pid"
done
```

### Example: Daily Status Report

```bash
#!/bin/bash
# daily-report.sh

{
    echo "SIGMAX Daily Report - $(date)"
    echo "=============================="
    echo ""
    sigmax status --verbose
    echo ""
    echo "Pending Proposals:"
    sigmax proposals --status pending
} | mail -s "SIGMAX Daily Report" trader@example.com
```

## Error Handling

The CLI provides clear error messages and exit codes:

- `0` - Success
- `1` - General error (invalid arguments, configuration error)
- `2` - API error (connection failed, authentication failed)
- `3` - Trading error (proposal rejected, execution failed)

**Example error handling in scripts:**

```bash
sigmax analyze BTC/USDT || {
    echo "Analysis failed with exit code $?"
    exit 1
}
```

## Troubleshooting

### "API key not configured"

```bash
sigmax config set api_key YOUR_API_KEY
```

### "Connection refused"

Ensure the SIGMAX API server is running:

```bash
# Check API URL
sigmax config get api_url

# Test API connectivity
curl http://localhost:8000/api/health
```

### "Command not found: sigmax"

Reinstall with CLI dependencies:

```bash
pip install -e ".[cli]"
```

### Clear shell history

```bash
rm ~/.sigmax/shell_history.txt
```

## Advanced Usage

### Custom API Endpoint

```bash
sigmax --api-url https://custom.sigmax.io status
```

### Multiple Environments

```bash
# Production
export SIGMAX_API_KEY=prod_key_123
export SIGMAX_API_URL=https://prod.sigmax.io
sigmax status

# Staging
export SIGMAX_API_KEY=staging_key_456
export SIGMAX_API_URL=https://staging.sigmax.io
sigmax status
```

### Combine with Other Tools

```bash
# Watch proposals in real-time
watch -n 5 "sigmax proposals --status pending"

# Log analysis to file
sigmax analyze BTC/USDT --stream 2>&1 | tee analysis_$(date +%Y%m%d_%H%M%S).log

# Alert on new proposals
sigmax proposals --format json | jq '.[] | select(.approved == false)' | \
    xargs -I {} echo "New proposal: {}"
```

## Getting Help

```bash
# General help
sigmax --help

# Command-specific help
sigmax analyze --help
sigmax config --help

# Interactive shell help
sigmax shell
sigmax> help
```

## See Also

- [Main README](../README.md) - Project overview
- [API Documentation](API.md) - REST API reference
- [Architecture](ARCHITECTURE.md) - System design
- [Configuration](CONFIGURATION.md) - Advanced configuration

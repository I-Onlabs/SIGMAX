# SIGMAX CLI Quick Start

Get up and running with the SIGMAX command-line interface in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- SIGMAX API server running (or access to hosted instance)
- API key for authentication

## Installation

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/I-Onlabs/SIGMAX.git
cd SIGMAX

# Install with CLI dependencies
pip install -e ".[cli]"
```

### 2. Verify Installation

```bash
sigmax --version
```

You should see: `SIGMAX CLI v1.0.0`

## Configuration

### Set Your API Key

```bash
sigmax config set api_key YOUR_API_KEY
```

### Configure API Endpoint (if not using localhost)

```bash
sigmax config set api_url https://api.sigmax.io
```

### Verify Configuration

```bash
sigmax config list
```

## First Commands

### 1. Check System Status

```bash
sigmax status
```

**Expected output:**
```
╭──────────── SIGMAX Status ────────────╮
│ Status: operational                   │
│ Mode: paper                           │
│ Active Trades: 0                      │
│ PnL: $0.00                            │
╰───────────────────────────────────────╯
```

### 2. Analyze a Trading Pair

```bash
sigmax analyze BTC/USDT
```

**Expected output:**
```
Analyzing BTC/USDT...
  ✓ Fetching market data
  ✓ Running technical analysis
  ✓ Multi-agent consensus
  ✓ Generating recommendation

╭────────── Analysis Result ──────────╮
│ Action: BUY                         │
│ Confidence: 78.5%                   │
│ Rationale: Strong bullish momentum │
│ with favorable indicators           │
╰─────────────────────────────────────╯
```

### 3. Create a Trade Proposal

```bash
sigmax propose ETH/USDT --risk balanced
```

**Expected output:**
```
Creating proposal for ETH/USDT...

╭────────── Trade Proposal ───────────╮
│ ID: PROP-abc123def456               │
│ Symbol: ETH/USDT                    │
│ Action: BUY                         │
│ Size: $500.00                       │
│ Status: ⏳ Pending                   │
│ Rationale: ...                      │
╰─────────────────────────────────────╯
```

### 4. List All Proposals

```bash
sigmax proposals
```

### 5. Approve and Execute

```bash
# Approve a proposal
sigmax approve PROP-abc123def456

# Execute the approved proposal
sigmax execute PROP-abc123def456
```

## Interactive Shell Mode

For an interactive experience:

```bash
sigmax shell
```

**In the shell:**
```
sigmax> analyze BTC/USDT
sigmax> status
sigmax> proposals
sigmax> help
sigmax> exit
```

## Common Workflows

### Daily Market Analysis

```bash
# Analyze multiple symbols
sigmax analyze BTC/USDT --risk conservative
sigmax analyze ETH/USDT --risk balanced
sigmax analyze SOL/USDT --risk aggressive
```

### Automated Proposal Creation

```bash
# Create proposals for specific symbols
sigmax propose BTC/USDT --size 1000
sigmax propose ETH/USDT --size 500

# Review pending proposals
sigmax proposals --status pending

# Approve high-confidence proposals
sigmax approve PROP-123
```

### Status Monitoring

```bash
# Check status with verbose output
sigmax status --verbose

# Watch status in real-time
watch -n 5 "sigmax status"
```

## Output Formats

### JSON (for scripting)

```bash
sigmax analyze BTC/USDT --format json > analysis.json
sigmax status --format json | jq '.active_trades'
```

### Table (for multiple items)

```bash
sigmax proposals --format table
```

### Text (human-readable, default)

```bash
sigmax analyze BTC/USDT  # Default text format
```

## Next Steps

### Learn More

- **[Full CLI Documentation](docs/CLI.md)** - All commands and options
- **[API Reference](docs/API_REFERENCE.md)** - Backend API details
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design

### Advanced Usage

- **Scripting**: Automate analysis with shell scripts
- **CI/CD Integration**: Add to deployment pipelines
- **Monitoring**: Set up automated alerts
- **Backtesting**: Analyze historical performance

### Get Help

```bash
# General help
sigmax --help

# Command-specific help
sigmax analyze --help
sigmax config --help
```

## Troubleshooting

### Command Not Found

```bash
# Reinstall CLI dependencies
pip install -e ".[cli]"

# Check installation
which sigmax
```

### API Connection Error

```bash
# Verify API URL
sigmax config get api_url

# Test connectivity
curl http://localhost:8000/api/health
```

### Permission Denied

```bash
# Ensure SIGMAX API server is running
# Check firewall settings
# Verify API key is correct
```

## Environment Variables

Alternative to config commands:

```bash
export SIGMAX_API_KEY=your_key_here
export SIGMAX_API_URL=http://localhost:8000

sigmax status  # Uses environment variables
```

## What's Next?

Now that you have the CLI running, you can:

1. **Explore all commands**: `sigmax --help`
2. **Read the full docs**: [docs/CLI.md](docs/CLI.md)
3. **Set up automation**: Create bash scripts for regular tasks
4. **Monitor your trades**: Use `watch` or cron jobs
5. **Integrate with other tools**: Export JSON for data analysis

Happy trading! 🚀

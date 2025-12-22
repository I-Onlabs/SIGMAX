# SIGMAX CLI

Command-line interface for SIGMAX - Autonomous Multi-Agent AI Crypto Trading OS.

## Features

- 🤖 **AI-Powered Analysis** - Get trading recommendations from multi-agent debate system
- 📊 **Real-time Status** - Monitor system health and trading activity
- 💼 **Proposal Management** - Create, approve, and execute trade proposals
- 🔒 **Paper & Live Trading** - Test strategies safely before going live
- 🎨 **Rich Terminal Output** - Beautiful tables, progress bars, and formatting
- 🐚 **Interactive Shell** - REPL-style interface for advanced users
- ⚛️ **Quantum Optimization** - Enable/disable quantum portfolio optimization

## Installation

### From PyPI (Recommended)

```bash
pip install sigmax-cli
```

### From Source

```bash
git clone https://github.com/yourusername/sigmax.git
cd sigmax/core/cli
pip install -e .
```

### Using pipx (Isolated Installation)

```bash
pipx install sigmax-cli
```

## Quick Start

### Basic Usage

```bash
# Analyze a trading pair
sigmax analyze BTC/USDT

# Check system status
sigmax status

# Start interactive shell
sigmax shell
```

### Configuration

Set your API credentials:

```bash
sigmax config set api_url http://localhost:8000
sigmax config set api_key sk-your-api-key-here
```

View current configuration:

```bash
sigmax config list
```

## Commands

### `analyze` - Get AI Trading Recommendations

Analyze a trading pair using multi-agent debate system:

```bash
sigmax analyze BTC/USDT
sigmax analyze ETH/USDT --risk balanced
sigmax analyze SOL/USDT --risk aggressive --stream
sigmax analyze BTC/USDT --no-quantum  # Disable quantum optimization
```

**Options:**
- `--risk` - Risk profile: `conservative` (default), `balanced`, `aggressive`
- `--mode` - Trading mode: `paper` (default), `live`
- `--format` - Output format: `text` (default), `json`, `table`
- `--stream` - Stream real-time analysis progress
- `--quantum/--no-quantum` - Enable/disable quantum optimization (default: enabled)

**Example Output:**

```
╭─────────────────────────────── BTC/USDT Analysis ───────────────────────────────╮
│ Decision: BUY                                                                    │
│ Confidence: 85%                                                                  │
│                                                                                  │
│ Rationale:                                                                       │
│ • Strong bullish momentum detected                                              │
│ • RSI showing oversold conditions                                               │
│ • Volume increasing significantly                                               │
│                                                                                  │
│ Entry: $42,150  Target: $45,000  Stop Loss: $40,500                            │
╰──────────────────────────────────────────────────────────────────────────────────╯
```

---

### `status` - System Status

Get current SIGMAX status:

```bash
sigmax status
sigmax status --format json
sigmax status --verbose
```

**Options:**
- `--format` - Output format: `text` (default), `json`, `table`
- `--verbose` - Show detailed status including agent activity

**Example Output:**

```
╭─────────────────── SIGMAX Status ───────────────────╮
│ System:    Running ✓                                 │
│ Mode:      Paper Trading                             │
│ Agents:    5 active                                  │
│ Uptime:    2h 34m                                    │
│                                                      │
│ Recent Activity:                                     │
│ • BTC/USDT analysis completed (2m ago)               │
│ • ETH/USDT proposal created (5m ago)                 │
╰──────────────────────────────────────────────────────╯
```

---

### `propose` - Create Trade Proposal

Create a trade proposal:

```bash
sigmax propose BTC/USDT
sigmax propose ETH/USDT --size 100
sigmax propose SOL/USDT --risk balanced --mode live
sigmax propose BTC/USDT --no-quantum  # Disable quantum optimization
```

**Options:**
- `--size` - Position size in USD (optional, system calculates based on risk)
- `--risk` - Risk profile: `conservative` (default), `balanced`, `aggressive`
- `--mode` - Trading mode: `paper` (default), `live`
- `--format` - Output format: `text` (default), `json`, `table`
- `--quantum/--no-quantum` - Enable/disable quantum optimization (default: enabled)

---

### `proposals` - List Trade Proposals

List all trade proposals:

```bash
sigmax proposals
sigmax proposals --status pending
sigmax proposals --format json
```

**Options:**
- `--status` - Filter by status: `pending`, `approved`, `executed`
- `--format` - Output format: `table` (default), `json`, `text`

**Example Output:**

```
┌──────────┬────────────┬────────┬─────────┬────────────┬────────────┐
│ ID       │ Symbol     │ Action │ Size    │ Status     │ Created    │
├──────────┼────────────┼────────┼─────────┼────────────┼────────────┤
│ PROP-123 │ BTC/USDT   │ BUY    │ $1000   │ Pending    │ 2m ago     │
│ PROP-122 │ ETH/USDT   │ SELL   │ $500    │ Approved   │ 15m ago    │
│ PROP-121 │ SOL/USDT   │ BUY    │ $250    │ Executed   │ 1h ago     │
└──────────┴────────────┴────────┴─────────┴────────────┴────────────┘
```

---

### `approve` - Approve Trade Proposal

Approve a pending proposal:

```bash
sigmax approve PROP-123
sigmax approve PROP-456 --format json
```

**Options:**
- `--format` - Output format: `text` (default), `json`, `table`

---

### `execute` - Execute Trade Proposal

Execute an approved proposal:

```bash
sigmax execute PROP-123
sigmax execute PROP-456 --force  # Skip confirmation
```

**Options:**
- `--format` - Output format: `text` (default), `json`, `table`
- `--force` - Skip confirmation prompt

**⚠️ Warning:** This executes real trades in live mode!

---

### `config` - Manage Configuration

Manage CLI configuration:

```bash
# List all configuration
sigmax config list

# Get specific value
sigmax config get api_key

# Set value
sigmax config set api_key sk-xxx
sigmax config set api_url http://localhost:8000
```

**Available Keys:**
- `api_url` - SIGMAX API endpoint URL
- `api_key` - API authentication key
- `default_risk` - Default risk profile
- `default_mode` - Default trading mode
- `output_format` - Default output format

---

### `shell` - Interactive Shell

Start interactive REPL-style shell:

```bash
sigmax shell
sigmax shell --api-url http://localhost:8000
```

**Options:**
- `--api-url` - Override API endpoint URL
- `--api-key` - Override API key

**Shell Commands:**
- `analyze <symbol>` - Analyze a symbol
- `status` - Show system status
- `propose <symbol>` - Create proposal
- `proposals` - List proposals
- `approve <id>` - Approve proposal
- `execute <id>` - Execute proposal
- `help` - Show available commands
- `exit` - Exit shell

**Example Session:**

```
╭───────────────── SIGMAX Interactive Shell ─────────────────╮
│ Type 'help' for commands, 'exit' to quit                   │
╰─────────────────────────────────────────────────────────────╯

sigmax> analyze BTC/USDT
[Analysis output...]

sigmax> propose BTC/USDT --size 1000
[Proposal created: PROP-789]

sigmax> approve PROP-789
[Proposal approved]

sigmax> exit
```

---

### `version` - Show Version

Display CLI version:

```bash
sigmax version
```

## Advanced Usage

### Streaming Analysis

Watch real-time analysis progress:

```bash
sigmax analyze BTC/USDT --stream
```

Output:
```
Analyzing BTC/USDT...
[1/5] Fetching market data... ✓
[2/5] Running technical analysis... ✓
[3/5] Agent debate in progress...
  Bull Agent: Strong momentum, RSI oversold
  Bear Agent: Resistance at $43k, volume declining
[4/5] Reaching consensus... ✓
[5/5] Generating recommendation... ✓

Decision: BUY (Confidence: 82%)
```

### Quantum Optimization

Enable or disable quantum portfolio optimization:

```bash
# Use quantum optimization (default)
sigmax analyze BTC/USDT

# Disable quantum optimization (use classical algorithms)
sigmax analyze BTC/USDT --no-quantum
sigmax propose ETH/USDT --no-quantum
```

Quantum optimization uses quantum-inspired algorithms for portfolio allocation and risk management, potentially improving performance but requiring more computational resources.

### JSON Output for Automation

Use JSON output for scripting and automation:

```bash
# Get status as JSON
sigmax status --format json

# Parse with jq
sigmax status --format json | jq '.agents.active'

# Use in scripts
if [ $(sigmax status --format json | jq -r '.system.status') == "running" ]; then
    echo "System is healthy"
fi
```

### Paper Trading Workflow

Safe testing workflow before live trading:

```bash
# 1. Configure for paper trading
sigmax config set default_mode paper

# 2. Analyze and create proposal
sigmax analyze BTC/USDT --risk balanced
sigmax propose BTC/USDT --size 1000

# 3. Review proposals
sigmax proposals --status pending

# 4. Approve and execute (no real money)
sigmax approve PROP-123
sigmax execute PROP-123 --force
```

### Live Trading Workflow

Production trading workflow:

```bash
# 1. Ensure system is ready
sigmax status --verbose

# 2. Analyze with conservative risk
sigmax analyze BTC/USDT --risk conservative

# 3. Create proposal for live trading
sigmax propose BTC/USDT --mode live --size 500

# 4. Review carefully
sigmax proposals --status pending

# 5. Approve (requires manual confirmation)
sigmax approve PROP-456

# 6. Execute (requires double confirmation)
sigmax execute PROP-456
> Execute proposal PROP-456? [y/N]: y
```

## Configuration File

Configuration is stored in `~/.sigmax/config.json`:

```json
{
  "api_url": "http://localhost:8000",
  "api_key": "sk-your-api-key",
  "default_risk": "conservative",
  "default_mode": "paper",
  "output_format": "text",
  "quantum_enabled": true
}
```

## Environment Variables

Override config with environment variables:

```bash
export SIGMAX_API_URL=http://localhost:8000
export SIGMAX_API_KEY=sk-your-api-key
export SIGMAX_DEFAULT_RISK=balanced
export SIGMAX_DEFAULT_MODE=paper
export SIGMAX_QUANTUM_ENABLED=true

sigmax analyze BTC/USDT
```

## Troubleshooting

### Connection Errors

If you get connection errors:

```bash
# Check API URL
sigmax config get api_url

# Test connectivity
curl $(sigmax config get api_url)/health

# Update URL if needed
sigmax config set api_url http://localhost:8000
```

### Authentication Errors

If you get 401/403 errors:

```bash
# Check API key
sigmax config get api_key

# Set new key
sigmax config set api_key sk-your-new-key
```

### Debug Mode

Enable verbose logging:

```bash
export SIGMAX_DEBUG=1
sigmax analyze BTC/USDT
```

## Development

### Running from Source

```bash
# Clone repository
git clone https://github.com/yourusername/sigmax.git
cd sigmax/core/cli

# Install in development mode
pip install -e ".[dev]"

# Run CLI
sigmax --help
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=cli --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy cli/
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](../../LICENSE) for details.

## Support

- **Documentation**: https://sigmax.readthedocs.io
- **Issues**: https://github.com/yourusername/sigmax/issues
- **Discussions**: https://github.com/yourusername/sigmax/discussions

## Related Projects

- **SIGMAX Python SDK**: https://github.com/yourusername/sigmax/tree/main/sdk/python
- **SIGMAX TypeScript SDK**: https://github.com/yourusername/sigmax/tree/main/sdk/typescript
- **SIGMAX API**: https://github.com/yourusername/sigmax

## Version

Current version: 0.1.0

See [CHANGELOG.md](CHANGELOG.md) for release history.

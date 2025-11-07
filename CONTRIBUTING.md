# Contributing to SIGMAX

First off, thank you for considering contributing to SIGMAX! It's people like you that make SIGMAX such a great tool for the community.

## Code of Conduct

This project and everyone participating in it is governed by respect, professionalism, and collaboration. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include as many details as possible:

**Bug Report Template:**

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. macOS 13, Ubuntu 22.04]
 - Python Version: [e.g. 3.11.5]
 - Node Version: [e.g. 20.10.0]
 - SIGMAX Version: [e.g. 1.0.0]

**Logs**
```
Paste relevant logs here
```

**Additional context**
Add any other context about the problem here.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear use case**: Why would this be useful?
- **Describe the solution**: What would you like to happen?
- **Describe alternatives**: What alternatives have you considered?
- **Impact**: Who would benefit from this?

### Pull Requests

1. **Fork the repo** and create your branch from `main`
2. **Follow the code style** (see below)
3. **Add tests** if you've added code
4. **Update documentation** if needed
5. **Ensure tests pass** before submitting
6. **Write clear commit messages**

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/your-username/SIGMAX.git
cd SIGMAX
```

### 2. Create Virtual Environment

```bash
cd core
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### 3. Install Pre-commit Hooks

```bash
pre-commit install
```

### 4. Run Tests

```bash
pytest tests/ -v
```

### 5. Start Development Servers

```bash
# Terminal 1: Backend
cd ui/api
uvicorn main:app --reload

# Terminal 2: Frontend
cd ui/web
npm run dev

# Terminal 3: Core (optional)
cd core
python main.py --mode paper
```

## Code Style

### Python

We use:
- **Black** for formatting
- **Ruff** for linting
- **mypy** for type checking
- **isort** for import sorting

```bash
# Format code
black core/ ui/api/

# Lint
ruff check .

# Type check
mypy core/
```

**Style Guidelines:**

- Use type hints for all function signatures
- Write docstrings for all public functions (Google style)
- Keep functions under 50 lines when possible
- Use descriptive variable names
- Add comments for complex logic

**Example:**

```python
async def analyze_symbol(
    self,
    symbol: str,
    market_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze a trading symbol using multi-agent debate.

    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        market_data: Optional market data override

    Returns:
        Decision dict with action, confidence, and reasoning

    Raises:
        ValueError: If symbol format is invalid
        RuntimeError: If orchestrator not initialized
    """
    # Implementation here
```

### TypeScript/React

We use:
- **ESLint** for linting
- **Prettier** for formatting
- **TypeScript strict mode**

```bash
# Lint
npm run lint

# Format
npm run format
```

**Style Guidelines:**

- Use functional components with hooks
- Prefer TypeScript interfaces over types
- Use descriptive component names
- Extract reusable logic into custom hooks
- Keep components under 200 lines

**Example:**

```typescript
interface TradingPanelProps {
  symbol: string;
  onAnalyze: (decision: Decision) => void;
}

export const TradingPanel: React.FC<TradingPanelProps> = ({
  symbol,
  onAnalyze
}) => {
  const [analyzing, setAnalyzing] = useState(false);

  // Implementation here
};
```

## Project Structure

```
SIGMAX/
├── core/                    # Python backend
│   ├── agents/             # LangGraph agents
│   ├── modules/            # Core functionality
│   ├── utils/              # Helper utilities
│   └── tests/              # Python tests
├── ui/
│   ├── api/                # FastAPI server
│   └── web/                # React frontend
├── trading/                # Freqtrade integration
├── infra/                  # Infrastructure configs
└── docs/                   # Documentation
```

## Testing

### Python Tests

We use **pytest** for testing:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_orchestrator.py

# Run with coverage
pytest --cov=core tests/

# Run specific test
pytest tests/test_orchestrator.py::test_analyze_symbol
```

**Writing Tests:**

```python
import pytest
from core.agents.orchestrator import SIGMAXOrchestrator

@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test that orchestrator initializes correctly."""
    orchestrator = SIGMAXOrchestrator(
        data_module=None,
        execution_module=None,
        # ... other deps
    )

    await orchestrator.initialize()

    assert orchestrator.app is not None
    assert orchestrator.running is False
```

### Frontend Tests

We use **Vitest** for unit tests and **Playwright** for E2E:

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e
```

## Commit Messages

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(agents): add sentiment analysis to researcher agent

- Integrate Twitter API for social sentiment
- Add weighted sentiment scoring
- Update researcher agent to use sentiment in decisions

Closes #123
```

```
fix(ui): resolve 3D swarm rendering performance issue

The agent swarm was dropping to 30 FPS on low-end devices.
Optimized by reducing polygon count and implementing LOD.

Fixes #456
```

## Areas We Need Help

### High Priority

- [ ] **Mobile App**: React Native version of Neural Cockpit
- [ ] **Strategy Marketplace**: Share and discover trading strategies
- [ ] **Advanced Backtesting**: Multi-asset portfolio backtesting
- [ ] **Real Quantum Hardware**: IBM Quantum integration
- [ ] **Multi-User Support**: Isolated accounts and permissions

### Medium Priority

- [ ] **More Exchanges**: Expand beyond Binance
- [ ] **Additional Agents**: ESG analyzer, news trader
- [ ] **Voice Control**: Full implementation of voice commands
- [ ] **Desktop App**: Tauri desktop application
- [ ] **Narrative Trading**: Event-driven strategies

### Good First Issues

- [ ] **Add unit tests**: Increase coverage to 90%+
- [ ] **Documentation**: Add more examples and tutorials
- [ ] **UI Improvements**: Better mobile responsiveness
- [ ] **Bug Fixes**: Check GitHub issues labeled "good first issue"
- [ ] **Performance**: Optimize agent response times

## Agent Development

To add a new agent:

1. **Create agent file** in `core/agents/`:

```python
# core/agents/news_trader.py
class NewsTraderAgent:
    """Trades based on breaking news events."""

    def __init__(self, llm):
        self.llm = llm

    async def analyze_news(
        self,
        symbol: str,
        news: List[str]
    ) -> Dict[str, Any]:
        # Implementation
        pass
```

2. **Add to orchestrator** in `core/agents/orchestrator.py`:

```python
from .news_trader import NewsTraderAgent

# In __init__:
self.news_trader = NewsTraderAgent(self.llm)

# Add node to workflow:
workflow.add_node("news_trader", self._news_trader_node)
workflow.add_edge("researcher", "news_trader")
```

3. **Write tests**:

```python
# tests/agents/test_news_trader.py
@pytest.mark.asyncio
async def test_news_trader_analysis():
    agent = NewsTraderAgent(llm=None)
    result = await agent.analyze_news("BTC/USDT", ["Fed raises rates"])
    assert "sentiment" in result
```

4. **Update documentation** in `docs/AGENTS.md`

## UI Component Development

To add a new UI component:

1. **Create component** in `ui/web/src/components/`:

```typescript
// ui/web/src/components/NewsPanel.tsx
import { Newspaper } from 'lucide-react'

export default function NewsPanel() {
  return (
    <div className="rounded-2xl border border-white/10 backdrop-blur-lg bg-white/5 p-6">
      <h3 className="flex items-center space-x-2">
        <Newspaper className="w-5 h-5" />
        <span>Breaking News</span>
      </h3>
      {/* Implementation */}
    </div>
  )
}
```

2. **Add to App.tsx**:

```typescript
import NewsPanel from './components/NewsPanel'

// In render:
<NewsPanel />
```

3. **Add API endpoint** if needed in `ui/api/main.py`

4. **Write tests** (optional but recommended)

## Documentation

All documentation lives in the `/docs` folder:

- **ARCHITECTURE.md**: System design and data flow
- **SAFETY.md**: Risk management and security
- **API.md**: API reference (add this!)
- **AGENTS.md**: Agent documentation (add this!)

When adding features:
1. Update relevant documentation
2. Add JSDoc/docstring comments
3. Update README.md if user-facing
4. Add examples to QUICKSTART.md

## Release Process

1. Update version in `package.json` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release branch: `git checkout -b release/v1.1.0`
4. Tag release: `git tag -a v1.1.0 -m "Release v1.1.0"`
5. Push: `git push origin v1.1.0`
6. Create GitHub release with changelog

## Questions?

- **Discord**: [Join our server](https://discord.gg/sigmax)
- **GitHub Discussions**: [Start a discussion](https://github.com/yourusername/SIGMAX/discussions)
- **Email**: dev@sigmax.dev

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to SIGMAX! 🚀

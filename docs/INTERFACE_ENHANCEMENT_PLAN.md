# SIGMAX Interface Enhancement Plan

## 📋 Executive Summary

**Current State:** SIGMAX supports Telegram bot + Web UI/API
**Goal:** Transform SIGMAX into a multi-interface platform accessible via CLI, SDKs, and WebSockets

**Why This Matters:**
- **Developers:** Need programmatic access via SDK
- **DevOps:** Need CLI for automation/scripting
- **Real-time Apps:** Need WebSocket for live updates
- **Integration:** Need clean SDK for building on SIGMAX

## 🔍 Current Architecture Audit

### ✅ Existing Interfaces

| Interface | Status | Purpose | Strengths | Limitations |
|-----------|--------|---------|-----------|-------------|
| **Telegram Bot** | ✅ Production | Natural language control | Easy for users | Not programmable |
| **Web API** | ✅ Production | REST + SSE streaming | Full featured | HTTP overhead |
| **Web UI** | ✅ Production | 3D visualization | Beautiful | Not headless |
| **Python API** | ✅ Code example | Programmatic access | Direct access | No packaging |

### 🏗️ Architecture Strengths

**Clean Multi-Channel Design:**
```python
# core/interfaces/contracts.py already has:
class Channel(str, Enum):
    telegram = "telegram"
    web = "web"
    api = "api"
    cli = "cli"  # <-- DEFINED BUT NOT IMPLEMENTED
```

**Structured Contracts:**
- `StructuredRequest` → Unified input for all channels
- `ChannelResponse` → Standardized output
- `ChannelService` → Routes requests to orchestrator

**This means:** Adding new interfaces is straightforward - the foundation is already built!

## 🎯 Enhancement Recommendations

### Priority 1: CLI Interface (High Impact, Medium Effort)

**Use Cases:**
```bash
# Non-interactive (scripting/automation)
sigmax analyze BTC/USDT
sigmax status
sigmax propose BTC/USDT --risk balanced
sigmax execute PROP-123

# Interactive (REPL)
sigmax shell
> analyze ETH/USDT
> status
> help
```

**Implementation:**
- Use `click` or `typer` for CLI framework
- Interactive mode with `prompt_toolkit`
- Output formats: JSON, table, or human-readable
- Channel: `Channel.cli` (already defined!)

**Benefits:**
- **DevOps:** Scriptable trading operations
- **CI/CD:** Automated testing/backtesting
- **Cron jobs:** Scheduled analysis
- **No browser needed:** Headless operation

### Priority 2: Chat SDK (High Impact, High Effort)

**Python SDK:**
```python
from sigmax_sdk import SigmaxClient

client = SigmaxClient(api_key="...")

# Streaming analysis
async for event in client.analyze("BTC/USDT", risk="balanced"):
    print(f"[{event.type}] {event.data}")

# Synchronous
result = client.analyze_sync("ETH/USDT")
print(result.decision)

# Trade proposals
proposal = client.propose_trade("BTC/USDT", size=100)
client.approve_proposal(proposal.id)
client.execute_proposal(proposal.id)
```

**TypeScript/JavaScript SDK:**
```typescript
import { SigmaxClient } from '@sigmax/sdk';

const client = new SigmaxClient({ apiKey: '...' });

// Streaming
for await (const event of client.analyze('BTC/USDT')) {
  console.log(event);
}

// Promise-based
const result = await client.analyzeSync('ETH/USDT');
```

**Benefits:**
- **Developers:** Easy integration in their apps
- **Type safety:** Full TypeScript support
- **npm/PyPI:** Standard package management
- **Documentation:** Auto-generated from types

### Priority 3: WebSocket Support (Medium Impact, Medium Effort)

**Why WebSocket > SSE:**
- **Bidirectional:** Client can send commands while streaming
- **Lower overhead:** More efficient than HTTP
- **Better mobile:** Works reliably on iOS/Android
- **Standard protocol:** Easy client libraries

**Implementation:**
```python
# FastAPI WebSocket endpoint
@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    while True:
        # Receive command
        data = await websocket.receive_json()

        # Process via ChannelService
        request = StructuredRequest(**data, channel=Channel.web)

        # Stream response
        async for event in service.stream_analyze(request):
            await websocket.send_json(event.model_dump())
```

**Client Usage:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.send(JSON.stringify({
  message: 'Analyze BTC/USDT',
  symbol: 'BTC/USDT',
  risk_profile: 'balanced'
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### Priority 4: GraphQL API (Optional, Advanced)

**Why GraphQL:**
- **Flexible queries:** Client controls data shape
- **Real-time subscriptions:** Built-in WebSocket
- **Type system:** Self-documenting API
- **Batching:** Multiple queries in one request

**Example:**
```graphql
query {
  analysis(symbol: "BTC/USDT", riskProfile: BALANCED) {
    decision {
      action
      confidence
      rationale
    }
    artifacts {
      type
      content
    }
  }
}

subscription {
  analysisStream(symbol: "BTC/USDT") {
    step
    progress
    data
  }
}
```

## 📊 Comparison Matrix

| Feature | Telegram | Web UI | CLI | SDK (Python) | SDK (TS) | WebSocket | GraphQL |
|---------|----------|--------|-----|--------------|----------|-----------|---------|
| **Natural Language** | ✅ | ✅ | ⚠️ | ❌ | ❌ | ⚠️ | ❌ |
| **Programmable** | ❌ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Real-time Streaming** | ❌ | ✅ (SSE) | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Automation** | ⚠️ | ❌ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| **Human-Friendly** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Developer-Friendly** | ❌ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Mobile** | ✅ | ✅ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| **Offline** | ❌ | ⚠️ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Learning Curve** | Low | Low | Low | Medium | Medium | Medium | High |

## 🗺️ Implementation Roadmap

### Phase 1: CLI (Week 1)
- [x] Audit current architecture
- [ ] Design CLI command structure
- [ ] Implement non-interactive mode
- [ ] Implement interactive shell
- [ ] Add output formatting (JSON/table/text)
- [ ] Write CLI documentation
- [ ] Add to README

### Phase 2: Python SDK (Week 2)
- [ ] Design SDK API surface
- [ ] Implement sync methods
- [ ] Implement async/streaming methods
- [ ] Add type hints (full typing coverage)
- [ ] Package for PyPI
- [ ] Write SDK documentation + examples
- [ ] Create Jupyter notebook examples

### Phase 3: TypeScript SDK (Week 2-3)
- [ ] Port Python SDK design to TS
- [ ] Implement Promise-based API
- [ ] Implement AsyncIterator streaming
- [ ] Add full TypeScript types
- [ ] Package for npm
- [ ] Write SDK documentation + examples
- [ ] Create React/Next.js examples

### Phase 4: WebSocket (Week 3)
- [ ] Add WebSocket endpoint to FastAPI
- [ ] Implement bidirectional messaging
- [ ] Add heartbeat/reconnection logic
- [ ] Update Python SDK to use WS
- [ ] Update TypeScript SDK to use WS
- [ ] Test reliability (reconnection, error handling)

### Phase 5: GraphQL (Optional, Week 4+)
- [ ] Design GraphQL schema
- [ ] Implement resolvers
- [ ] Add subscriptions (real-time)
- [ ] Set up Apollo Server or Strawberry
- [ ] GraphQL Playground UI
- [ ] Documentation

## 📝 Suggested Command Structure

### CLI Commands

```bash
# Analysis
sigmax analyze <symbol> [--risk <profile>] [--mode paper|live]
sigmax status [--format json|table|text]
sigmax explain <symbol> [--trade-id <id>]

# Trading
sigmax propose <symbol> [--size <amount>] [--risk <profile>]
sigmax approve <proposal-id>
sigmax execute <proposal-id>
sigmax list proposals [--status pending|approved|executed]

# Control
sigmax start [--profile <name>]
sigmax stop [--emergency]
sigmax pause [--duration <time>]
sigmax resume

# Monitoring
sigmax watch <symbol>  # Live updates
sigmax logs [--tail <n>]
sigmax agents  # Show agent activity

# Configuration
sigmax config set <key> <value>
sigmax config get <key>
sigmax config list

# Interactive
sigmax shell  # REPL mode
sigmax chat   # Natural language mode (like Telegram)
```

## 🛠️ Technical Stack Recommendations

### CLI
- **Framework:** `typer` (modern, type-safe, better than click)
- **Interactive:** `prompt_toolkit` (autocomplete, syntax highlighting)
- **Tables:** `rich` (beautiful terminal output)
- **Progress:** `rich.progress` (live updates)

### Python SDK
- **HTTP:** `httpx` (async HTTP client)
- **WebSocket:** `websockets` library
- **Types:** Full `mypy` coverage
- **Docs:** `mkdocs` + `mkdocstrings`

### TypeScript SDK
- **HTTP:** `axios` or `fetch`
- **WebSocket:** Native `WebSocket` API
- **Build:** `tsup` (fast bundler)
- **Docs:** `typedoc`

### WebSocket
- **FastAPI:** `fastapi.WebSocket` (built-in)
- **Broadcasting:** `redis` for multi-instance
- **Reconnection:** Exponential backoff

## 📦 Deliverables

### Week 1
- ✅ Enhancement plan (this document)
- [ ] CLI tool (`sigmax` command)
- [ ] CLI documentation
- [ ] Updated README

### Week 2
- [ ] Python SDK (`sigmax-sdk` on PyPI)
- [ ] SDK documentation + examples
- [ ] Jupyter notebook tutorial

### Week 3
- [ ] TypeScript SDK (`@sigmax/sdk` on npm)
- [ ] React integration example
- [ ] WebSocket support in both SDKs

### Week 4 (Optional)
- [ ] GraphQL API
- [ ] GraphQL Playground
- [ ] Advanced examples

## ✅ Success Criteria

1. **CLI:** Developers can automate SIGMAX without browser
2. **Python SDK:** Data scientists can use in Jupyter notebooks
3. **TypeScript SDK:** Web developers can integrate in React/Next.js
4. **WebSocket:** Mobile apps get real-time updates efficiently
5. **Documentation:** Every interface has examples and guides
6. **Testing:** All interfaces have integration tests

## 🎯 Recommendation: Start with CLI

**Why CLI First:**
1. **Immediate value:** DevOps can script operations
2. **Low complexity:** Reuses existing API
3. **Fast to build:** 1-2 days for MVP
4. **Foundation:** CLI tests the API design
5. **Feedback:** Users can test before SDK release

**Then SDK:** Once CLI proves the design works, SDKs follow naturally.

---

**Status:** Ready to implement
**Next Steps:** Approve plan → Build CLI → Enhance README → Release

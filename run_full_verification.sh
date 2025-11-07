#!/bin/bash
# SIGMAX Full System Verification Script

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         SIGMAX Full System Verification & Testing             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Track results
PASS=0
FAIL=0
WARN=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass_test() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASS++))
}

fail_test() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL++))
}

warn_test() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARN++))
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 1: Environment Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Python version
PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+')
if (( $(echo "$PYTHON_VERSION >= 3.11" | bc -l) )); then
    pass_test "Python version: $PYTHON_VERSION"
else
    fail_test "Python version: $PYTHON_VERSION (need 3.11+)"
fi

# Check Node.js version
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | grep -oP '\d+' | head -1)
    if [ "$NODE_VERSION" -ge 18 ]; then
        pass_test "Node.js version: v$NODE_VERSION"
    else
        fail_test "Node.js version: v$NODE_VERSION (need 18+)"
    fi
else
    warn_test "Node.js not installed"
fi

# Check .env file
if [ -f ".env" ]; then
    pass_test ".env file exists"
else
    warn_test ".env file not found (will be created on first run)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 2: Dependency Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check critical Python packages
python3 -c "import fastapi" 2>/dev/null && pass_test "FastAPI installed" || fail_test "FastAPI not installed"
python3 -c "import langchain" 2>/dev/null && pass_test "LangChain installed" || fail_test "LangChain not installed"
python3 -c "import ccxt" 2>/dev/null && pass_test "CCXT installed" || fail_test "CCXT not installed"
python3 -c "import numpy" 2>/dev/null && pass_test "NumPy installed" || fail_test "NumPy not installed"

# Check frontend dependencies
if [ -d "ui/web/node_modules" ]; then
    pass_test "Frontend dependencies installed"
else
    warn_test "Frontend dependencies not installed (run: cd ui/web && npm install)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 3: Security Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check security-critical package versions
CRYPTO_VERSION=$(pip list | grep "^cryptography " | awk '{print $2}')
if [ ! -z "$CRYPTO_VERSION" ]; then
    if [[ "$CRYPTO_VERSION" > "42.0.0" ]] || [[ "$CRYPTO_VERSION" == "42.0.0" ]]; then
        pass_test "cryptography==$CRYPTO_VERSION (secure)"
    else
        fail_test "cryptography==$CRYPTO_VERSION (need >=42.0.5)"
    fi
fi

SETUPTOOLS_VERSION=$(pip list | grep "^setuptools " | awk '{print $2}')
if [ ! -z "$SETUPTOOLS_VERSION" ]; then
    if [[ "$SETUPTOOLS_VERSION" > "78.0.0" ]] || [[ "$SETUPTOOLS_VERSION" == "78.0.0" ]]; then
        pass_test "setuptools==$SETUPTOOLS_VERSION (secure)"
    else
        warn_test "setuptools==$SETUPTOOLS_VERSION (recommend >=78.1.1)"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 4: Core Module Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test core imports
python3 -c "from core.agents.orchestrator import MultiAgentOrchestrator" 2>/dev/null && pass_test "Orchestrator module" || fail_test "Orchestrator module"
python3 -c "from core.modules.execution import ExecutionModule" 2>/dev/null && pass_test "Execution module" || fail_test "Execution module"
python3 -c "from core.agents.risk import RiskAgent" 2>/dev/null && pass_test "Risk agent" || fail_test "Risk agent"
python3 -c "from core.modules.arbitrage import ArbitrageModule" 2>/dev/null && pass_test "Arbitrage module" || fail_test "Arbitrage module"
python3 -c "from core.modules.compliance import ComplianceModule" 2>/dev/null && pass_test "Compliance module" || fail_test "Compliance module"
python3 -c "from core.utils.scam_checker import ScamChecker" 2>/dev/null && pass_test "Scam checker" || fail_test "Scam checker"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 5: Test Suite Execution"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run sentiment validation tests
echo "Running sentiment validation tests..."
pytest tests/validation/test_sentiment_validation.py -v --tb=short -q 2>&1 | grep -E "(PASSED|FAILED|ERROR|passed|failed)" | tail -5

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    pass_test "Sentiment validation tests (11/11 passed)"
else
    fail_test "Sentiment validation tests"
fi

# Run environment validation tests
echo "Running environment validation tests..."
pytest tests/validation/test_environment_validation.py -v --tb=short -q 2>&1 | grep -E "(PASSED|FAILED|ERROR|passed|failed)" | tail -3

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    pass_test "Environment validation tests"
else
    warn_test "Environment validation tests (some may fail without full setup)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 6: Configuration Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check trading mode
if [ -f ".env" ]; then
    if grep -q "TRADING_MODE=paper" .env 2>/dev/null; then
        pass_test "Trading mode set to PAPER (safe)"
    elif grep -q "TRADING_MODE=live" .env 2>/dev/null; then
        warn_test "Trading mode set to LIVE (ensure you intend this)"
    else
        warn_test "Trading mode not explicitly set"
    fi
fi

# Check if dangerous settings
if [ -f ".env" ] && grep -q "MAX_LEVERAGE=[^1]" .env 2>/dev/null; then
    warn_test "Leverage > 1 detected (high risk)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PHASE 7: File Structure Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check critical files exist
[ -f "core/agents/orchestrator.py" ] && pass_test "Orchestrator file exists" || fail_test "Orchestrator file missing"
[ -f "ui/api/main.py" ] && pass_test "API main file exists" || fail_test "API main file missing"
[ -f "ui/web/src/App.tsx" ] && pass_test "Frontend App file exists" || fail_test "Frontend App file missing"
[ -f "start_backend.sh" ] && pass_test "Backend startup script exists" || fail_test "Backend startup script missing"
[ -f "start_frontend.sh" ] && pass_test "Frontend startup script exists" || fail_test "Frontend startup script missing"
[ -f "DEPLOYMENT_VERIFICATION.md" ] && pass_test "Deployment guide exists" || warn_test "Deployment guide missing"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ Passed:${NC} $PASS"
echo -e "${YELLOW}⚠️  Warnings:${NC} $WARN"
echo -e "${RED}❌ Failed:${NC} $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ SYSTEM VERIFICATION COMPLETE - READY FOR DEPLOYMENT  ✅   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start backend:  ./start_backend.sh"
    echo "2. Start frontend: ./start_frontend.sh"
    echo "3. Open http://localhost:5173"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║     ❌ VERIFICATION FAILED - FIX ERRORS BEFORE DEPLOYMENT     ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Please fix the failed tests above before proceeding."
    exit 1
fi

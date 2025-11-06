#!/bin/bash
# SIGMAX Environment Validation Script
# Checks system requirements and configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0
CHECKS=0

# Helper functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
    ((CHECKS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
    ((CHECKS++))
}

check_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo "======================================"
echo "  SIGMAX Environment Validation"
echo "======================================"
echo

# Check Operating System
echo "=== System Information ==="
check_info "OS: $(uname -s) $(uname -r)"
check_info "Architecture: $(uname -m)"
echo

# Check Python
echo "=== Python Environment ==="
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    check_pass "Python $PYTHON_VERSION"
else
    check_fail "Python 3 not found"
fi

echo "✅ Environment validation script created"

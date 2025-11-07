#!/bin/bash
# SIGMAX Security Vulnerability Fix Script

echo "🔒 Fixing SIGMAX Security Vulnerabilities..."
echo ""

# Phase 1: Critical
echo "================================================"
echo "Phase 1: CRITICAL vulnerabilities"
echo "================================================"
pip install --upgrade "cryptography>=42.0.5"
echo "✅ Cryptography upgraded"
echo ""

# Phase 2: High
echo "================================================"
echo "Phase 2: HIGH priority vulnerabilities"
echo "================================================"
pip install --upgrade "setuptools>=78.1.1"
pip install --upgrade "pip>=25.2"
echo "✅ Setuptools and pip upgraded"
echo ""

# Phase 3: Moderate
echo "================================================"
echo "Phase 3: MODERATE priority vulnerabilities"
echo "================================================"
pip install --upgrade "xmltodict>=0.15.1"
echo "✅ xmltodict upgraded"
echo ""

# Verify
echo "================================================"
echo "🔍 Verifying upgrades..."
echo "================================================"
pip list | grep -E "(cryptography|setuptools|pip|xmltodict)"
echo ""

# Run security scan
echo "================================================"
echo "🔒 Running security scan..."
echo "================================================"
safety scan 2>&1 | head -50
echo ""

echo "✅ Security fix complete!"
echo ""
echo "Next steps:"
echo "1. Run test suite: pytest tests/validation/test_sentiment_validation.py -v"
echo "2. Verify core modules: python3 -c 'from core.modules.privacy import PrivacyModule'"
echo "3. Commit changes: git add -u && git commit -m 'security: Fix 13 vulnerabilities'"

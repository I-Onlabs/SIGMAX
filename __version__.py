"""
SIGMAX Version Information
Single source of truth for project version.
"""

__version__ = "0.2.0-alpha"
__version_info__ = (0, 2, 0, "alpha", 0)

# Version components
MAJOR = 0
MINOR = 2
PATCH = 0
PRERELEASE = "alpha"
BUILD = 0

# Human-readable status
STATUS = "Alpha - Research Software"
STABILITY = "Experimental"

# What's actually working in this version
FUNCTIONAL_FEATURES = [
    "Multi-agent orchestrator (core)",
    "Quantum optimization (VQE/QAOA)",
    "Safety enforcer (auto-pause)",
    "FastAPI backend",
    "CLI tools",
    "Paper trading only",
]

# What's NOT working (despite claims)
KNOWN_GAPS = [
    "SDKs not published to PyPI/npm (install from source)",
    "ZK-SNARK proofs are mocked (not real)",
    "Two-man rule not implemented",
    "MEV protection is only slippage checking",
    "Performance claims unverified",
]

# Legal status
LICENSE = "MIT (with GPL-3.0 dependency - see LICENSE)"
USE_CASE = "Educational and Research Only"
PRODUCTION_READY = False

def get_version():
    """Return version string."""
    return __version__

def get_version_info():
    """Return detailed version information."""
    return {
        "version": __version__,
        "status": STATUS,
        "stability": STABILITY,
        "production_ready": PRODUCTION_READY,
        "use_case": USE_CASE,
        "functional": FUNCTIONAL_FEATURES,
        "known_gaps": KNOWN_GAPS,
    }

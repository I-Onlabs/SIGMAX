from setuptools import setup, find_packages
import sys
from pathlib import Path

# Import version from single source of truth
sys.path.insert(0, str(Path(__file__).parent))
from __version__ import __version__, STATUS, USE_CASE

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="sigmax",
    version=__version__,
    author="SIGMAX Contributors",
    description=f"SIGMAX - {STATUS} - {USE_CASE}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/I-Onlabs/SIGMAX",
    packages=find_packages(where="."),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "performance": [
            "aeron-python>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "sigmax-ingest=apps.ingest_cex.main:main",
            "sigmax-book=apps.book_shard.main:main",
            "sigmax-features=apps.features.main:main",
            "sigmax-decision=apps.decision.main:main",
            "sigmax-risk=apps.risk.main:main",
            "sigmax-router=apps.router.main:main",
            "sigmax-exec=apps.exec_cex.main:main",
            "sigmax-obs=apps.obs.main:main",
            "sigmax-replay=apps.replay.main:main",
        ],
    },
)

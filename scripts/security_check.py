#!/usr/bin/env python3
"""
SIGMAX Security Check Script

Performs comprehensive security checks on SIGMAX codebase and dependencies.
Checks for known vulnerabilities, insecure configurations, and best practices.

Usage:
    python scripts/security_check.py --all
    python scripts/security_check.py --dependencies
    python scripts/security_check.py --secrets
    python scripts/security_check.py --code
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class SecurityChecker:
    """Performs security checks on SIGMAX"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.findings = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message"""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "CRITICAL": "\033[95m",
            "RESET": "\033[0m"
        }
        color = colors.get(level, "")
        reset = colors["RESET"]
        print(f"{color}[{level}] {message}{reset}")

    def add_finding(self, severity: str, title: str, description: str, recommendation: str = ""):
        """Add security finding"""
        self.findings[severity.lower()].append({
            "title": title,
            "description": description,
            "recommendation": recommendation
        })

    def check_dependencies(self) -> bool:
        """Check dependencies for known vulnerabilities"""
        self.log("Checking dependencies for vulnerabilities...", "INFO")

        # Check if pip-audit is installed
        try:
            result = subprocess.run(
                ['pip-audit', '--version'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self.log("pip-audit not installed, installing...", "WARNING")
                subprocess.run(['pip', 'install', 'pip-audit'], check=True)

        except FileNotFoundError:
            self.log("pip-audit not available, skipping dependency check", "WARNING")
            return False

        # Run pip-audit
        try:
            result = subprocess.run(
                ['pip-audit', '--desc', '--json'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                self.log("✓ No known vulnerabilities found in dependencies", "SUCCESS")
                return True

            # Parse findings
            try:
                data = json.loads(result.stdout)
                dependencies = data.get('dependencies', [])

                for dep in dependencies:
                    name = dep.get('name', 'unknown')
                    version = dep.get('version', 'unknown')
                    vulns = dep.get('vulns', [])

                    for vuln in vulns:
                        vuln_id = vuln.get('id', 'N/A')
                        description = vuln.get('description', 'No description')
                        fix_versions = vuln.get('fix_versions', [])

                        # Determine severity
                        # pip-audit doesn't provide severity, estimate from CVE
                        severity = "medium"
                        if "critical" in description.lower() or "severe" in description.lower():
                            severity = "critical"
                        elif "high" in description.lower():
                            severity = "high"

                        self.add_finding(
                            severity,
                            f"Vulnerable dependency: {name}",
                            f"Package {name}=={version} has known vulnerability {vuln_id}: {description}",
                            f"Upgrade to one of: {', '.join(fix_versions) if fix_versions else 'latest version'}"
                        )

                self.log(f"✗ Found {len(dependencies)} vulnerable dependencies", "ERROR")

            except json.JSONDecodeError:
                self.log("Could not parse pip-audit output", "WARNING")

            return False

        except subprocess.TimeoutExpired:
            self.log("Dependency check timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"Dependency check failed: {e}", "ERROR")
            return False

    def check_secrets(self) -> bool:
        """Check for accidentally committed secrets"""
        self.log("Checking for committed secrets...", "INFO")

        # Check for common secret patterns in code
        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\'][^"\']{20,}["\']', "API key in code"),
            (r'secret[_-]?key\s*=\s*["\'][^"\']{20,}["\']', "Secret key in code"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Password in code"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "Token in code"),
            (r'aws[_-]?access[_-]?key', "AWS access key"),
            (r'-----BEGIN (RSA|DSA|EC) PRIVATE KEY-----', "Private key"),
        ]

        issues_found = False

        # Check Python files
        python_files = list(self.project_root.glob("**/*.py"))

        for file in python_files:
            # Skip venv, node_modules, etc.
            if any(skip in str(file) for skip in ['venv', 'node_modules', '.git', '__pycache__']):
                continue

            try:
                content = file.read_text()

                for pattern, description in secret_patterns:
                    import re
                    if re.search(pattern, content, re.IGNORECASE):
                        # Check if it's actually a secret (not example/placeholder)
                        if "example" not in content.lower() and "placeholder" not in content.lower():
                            self.add_finding(
                                "high",
                                f"Potential secret in {file.name}",
                                f"Found pattern matching {description}",
                                "Remove secret from code and use environment variables"
                            )
                            issues_found = True

            except Exception as e:
                self.log(f"Could not read {file}: {e}", "WARNING")

        # Check for .env files in git
        env_files = list(self.project_root.glob("**/.env*"))
        for env_file in env_files:
            if env_file.name != ".env.example" and env_file.exists():
                # Check if tracked by git
                result = subprocess.run(
                    ['git', 'ls-files', '--error-unmatch', str(env_file)],
                    cwd=self.project_root,
                    capture_output=True
                )

                if result.returncode == 0:
                    self.add_finding(
                        "critical",
                        f"Environment file in git: {env_file.name}",
                        "Sensitive environment file is tracked by git",
                        "Remove from git: git rm --cached {env_file.name} and add to .gitignore"
                    )
                    issues_found = True

        if not issues_found:
            self.log("✓ No secrets found in code", "SUCCESS")
            return True
        else:
            self.log(f"✗ Found potential secrets in code", "ERROR")
            return False

    def check_code_security(self) -> bool:
        """Check code for security issues using bandit"""
        self.log("Checking code for security issues...", "INFO")

        # Check if bandit is installed
        try:
            result = subprocess.run(
                ['bandit', '--version'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self.log("bandit not installed, installing...", "WARNING")
                subprocess.run(['pip', 'install', 'bandit'], check=True)

        except FileNotFoundError:
            self.log("bandit not available, skipping code security check", "WARNING")
            return False

        # Run bandit
        try:
            result = subprocess.run(
                ['bandit', '-r', 'core/', 'apps/', '-f', 'json', '-ll'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Parse results
            try:
                data = json.loads(result.stdout)
                results = data.get('results', [])

                if not results:
                    self.log("✓ No code security issues found", "SUCCESS")
                    return True

                for issue in results:
                    severity = issue.get('issue_severity', 'MEDIUM').lower()
                    test_id = issue.get('test_id', 'N/A')
                    text = issue.get('issue_text', 'No description')
                    filename = issue.get('filename', 'unknown')
                    line = issue.get('line_number', 0)

                    self.add_finding(
                        severity,
                        f"Code security issue ({test_id})",
                        f"{filename}:{line} - {text}",
                        "Review code and apply security best practices"
                    )

                self.log(f"✗ Found {len(results)} code security issues", "ERROR")
                return False

            except json.JSONDecodeError:
                self.log("Could not parse bandit output", "WARNING")
                return False

        except subprocess.TimeoutExpired:
            self.log("Code security check timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"Code security check failed: {e}", "ERROR")
            return False

    def check_configurations(self) -> bool:
        """Check for insecure configurations"""
        self.log("Checking configurations...", "INFO")

        issues_found = False

        # Check .env.example for secure defaults
        env_example = self.project_root / ".env.example"
        if env_example.exists():
            content = env_example.read_text()

            # Check for insecure defaults
            if "password=password" in content.lower() or "secret=secret" in content.lower():
                self.add_finding(
                    "low",
                    "Weak default credentials in .env.example",
                    "Example file contains weak default passwords",
                    "Use strong placeholder values in examples"
                )
                issues_found = True

            if "debug=true" in content.lower():
                self.add_finding(
                    "medium",
                    "Debug mode enabled in example",
                    ".env.example has DEBUG=true",
                    "Set DEBUG=false in production examples"
                )
                issues_found = True

        # Check Docker configurations
        dockerfiles = list(self.project_root.glob("**/Dockerfile*"))
        for dockerfile in dockerfiles:
            content = dockerfile.read_text()

            if "FROM" in content and ":latest" in content:
                self.add_finding(
                    "low",
                    f"Using ':latest' tag in {dockerfile.name}",
                    "Docker image uses ':latest' tag which is not reproducible",
                    "Pin specific version tags for reproducibility"
                )
                issues_found = True

            if "USER root" in content or (("USER" not in content) and ("RUN" in content)):
                self.add_finding(
                    "medium",
                    f"Running as root in {dockerfile.name}",
                    "Container runs as root user",
                    "Create and use non-root user in Dockerfile"
                )
                issues_found = True

        if not issues_found:
            self.log("✓ No configuration issues found", "SUCCESS")
            return True
        else:
            self.log(f"✗ Found configuration issues", "ERROR")
            return False

    def check_file_permissions(self) -> bool:
        """Check for overly permissive file permissions"""
        self.log("Checking file permissions...", "INFO")

        issues_found = False

        # Check scripts directory
        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists():
            for script in scripts_dir.glob("*.py"):
                stat = script.stat()
                mode = oct(stat.st_mode)[-3:]

                # Check if world-writable
                if int(mode[2]) >= 2:
                    self.add_finding(
                        "medium",
                        f"Script {script.name} is world-writable",
                        f"File has permissions {mode}, allowing anyone to modify",
                        f"Fix: chmod 750 {script}"
                    )
                    issues_found = True

        # Check for sensitive files
        sensitive_patterns = [".env", "*.pem", "*.key", "*.p12"]
        for pattern in sensitive_patterns:
            for file in self.project_root.glob(f"**/{pattern}"):
                if file.is_file():
                    stat = file.stat()
                    mode = oct(stat.st_mode)[-3:]

                    # Should be 600 or 400
                    if int(mode[1]) > 0 or int(mode[2]) > 0:
                        self.add_finding(
                            "high",
                            f"Sensitive file {file.name} has loose permissions",
                            f"File has permissions {mode}, readable by group/others",
                            f"Fix: chmod 600 {file}"
                        )
                        issues_found = True

        if not issues_found:
            self.log("✓ File permissions look good", "SUCCESS")
            return True
        else:
            self.log(f"✗ Found permission issues", "ERROR")
            return False

    def print_summary(self):
        """Print security check summary"""
        print("\n" + "="*70)
        print("SECURITY CHECK SUMMARY")
        print("="*70 + "\n")

        total = sum(len(findings) for findings in self.findings.values())

        if total == 0:
            print("✓ No security issues found!\n")
            return

        # Print counts
        print(f"Total Findings: {total}\n")

        for severity in ["critical", "high", "medium", "low", "info"]:
            count = len(self.findings[severity])
            if count > 0:
                severity_upper = severity.upper()
                print(f"  {severity_upper}: {count}")

        print()

        # Print findings by severity
        for severity in ["critical", "high", "medium", "low", "info"]:
            findings = self.findings[severity]

            if findings:
                print(f"\n{severity.upper()} Severity Issues:")
                print("-" * 70)

                for i, finding in enumerate(findings, 1):
                    print(f"\n{i}. {finding['title']}")
                    print(f"   Description: {finding['description']}")
                    if finding['recommendation']:
                        print(f"   Recommendation: {finding['recommendation']}")

        print("\n" + "="*70)
        print("For detailed remediation steps, see: docs/SECURITY_ASSESSMENT.md")
        print("="*70 + "\n")

    def run_all_checks(self):
        """Run all security checks"""
        self.log("\n" + "="*70, "INFO")
        self.log("Starting SIGMAX Security Check", "INFO")
        self.log("="*70 + "\n", "INFO")

        results = {
            "dependencies": self.check_dependencies(),
            "secrets": self.check_secrets(),
            "code": self.check_code_security(),
            "configurations": self.check_configurations(),
            "permissions": self.check_file_permissions()
        }

        self.print_summary()

        # Return exit code
        critical_or_high = len(self.findings["critical"]) + len(self.findings["high"])
        if critical_or_high > 0:
            return 2  # Critical issues found
        elif len(self.findings["medium"]) > 0:
            return 1  # Medium issues found
        else:
            return 0  # All clear


def main():
    parser = argparse.ArgumentParser(
        description="SIGMAX Security Check Script"
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all security checks (default)'
    )
    parser.add_argument(
        '--dependencies',
        action='store_true',
        help='Check dependencies for vulnerabilities'
    )
    parser.add_argument(
        '--secrets',
        action='store_true',
        help='Check for committed secrets'
    )
    parser.add_argument(
        '--code',
        action='store_true',
        help='Check code for security issues'
    )
    parser.add_argument(
        '--config',
        action='store_true',
        help='Check configurations'
    )
    parser.add_argument(
        '--permissions',
        action='store_true',
        help='Check file permissions'
    )

    args = parser.parse_args()

    checker = SecurityChecker()

    # If no specific check requested, run all
    if not any([args.dependencies, args.secrets, args.code, args.config, args.permissions]):
        args.all = True

    if args.all:
        exit_code = checker.run_all_checks()
    else:
        if args.dependencies:
            checker.check_dependencies()
        if args.secrets:
            checker.check_secrets()
        if args.code:
            checker.check_code_security()
        if args.config:
            checker.check_configurations()
        if args.permissions:
            checker.check_file_permissions()

        checker.print_summary()

        critical_or_high = len(checker.findings["critical"]) + len(checker.findings["high"])
        exit_code = 2 if critical_or_high > 0 else (1 if len(checker.findings["medium"]) > 0 else 0)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

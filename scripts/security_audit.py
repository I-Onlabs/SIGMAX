#!/usr/bin/env python3
"""
SIGMAX Security Audit Script

Performs comprehensive security audits including:
- Static code analysis with Bandit
- Dependency vulnerability scanning
- Secret detection
- Configuration security checks
- Permissions audit

Usage:
    python scripts/security_audit.py --full
    python scripts/security_audit.py --quick
    python scripts/security_audit.py --report output.json
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class SecurityAuditor:
    """Comprehensive security auditing tool"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.findings = []
        self.timestamp = datetime.utcnow().isoformat()

    def log(self, message: str, level: str = "INFO"):
        """Log audit message"""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[93m",
            "CRITICAL": "\033[91m",
            "RESET": "\033[0m"
        }
        color = colors.get(level, "")
        reset = colors["RESET"]
        print(f"{color}[{level}] {message}{reset}")

    def run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run shell command and return results"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_root
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)

    def check_bandit(self) -> Dict:
        """Run Bandit static code analysis"""
        self.log("Running Bandit static code analysis...")

        returncode, stdout, stderr = self.run_command([
            'bandit',
            '-r', 'pkg/', 'apps/', 'core/',
            '-f', 'json',
            '-ll',  # Only show medium/high severity
            '--exclude', '*/tests/*,*/test_*.py'
        ])

        findings = {
            "tool": "bandit",
            "status": "completed" if returncode in [0, 1] else "failed",
            "issues": []
        }

        if returncode in [0, 1] and stdout:
            try:
                bandit_data = json.loads(stdout)
                findings["issues"] = bandit_data.get("results", [])
                findings["metrics"] = bandit_data.get("metrics", {})

                issue_count = len(findings["issues"])
                if issue_count > 0:
                    self.log(f"Found {issue_count} security issues", "WARNING")
                else:
                    self.log("No security issues found", "SUCCESS")

            except json.JSONDecodeError:
                findings["status"] = "error"
                findings["error"] = "Failed to parse Bandit output"

        return findings

    def check_secrets(self) -> Dict:
        """Check for hardcoded secrets"""
        self.log("Scanning for hardcoded secrets...")

        findings = {
            "tool": "secret_scanner",
            "status": "completed",
            "issues": []
        }

        # Patterns to search for
        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', 'Potential API key'),
            (r'secret[_-]?key\s*=\s*["\'][^"\']+["\']', 'Potential secret key'),
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
            (r'aws[_-]?access[_-]?key\s*=\s*["\'][^"\']+["\']', 'AWS access key'),
            (r'private[_-]?key\s*=\s*["\'][^"\']+["\']', 'Private key'),
        ]

        import re

        python_files = list(self.project_root.rglob("*.py"))
        for file_path in python_files:
            if "test" in str(file_path) or ".venv" in str(file_path):
                continue

            try:
                content = file_path.read_text()
                for pattern, description in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Skip if it's in a comment or looks like a template
                        line = content[max(0, match.start()-50):match.end()+50]
                        if '# TODO' in line or 'example' in line.lower() or 'your_' in line.lower():
                            continue

                        findings["issues"].append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "description": description,
                            "line": content[:match.start()].count('\n') + 1,
                            "severity": "HIGH"
                        })
            except Exception:
                continue

        issue_count = len(findings["issues"])
        if issue_count > 0:
            self.log(f"Found {issue_count} potential secrets", "CRITICAL")
        else:
            self.log("No hardcoded secrets detected", "SUCCESS")

        return findings

    def check_permissions(self) -> Dict:
        """Check file permissions"""
        self.log("Checking file permissions...")

        findings = {
            "tool": "permission_checker",
            "status": "completed",
            "issues": []
        }

        sensitive_files = [
            ".env",
            ".env.production",
            ".env.testnet",
            "config/secrets.yaml",
            "*.key",
            "*.pem"
        ]

        for pattern in sensitive_files:
            for file_path in self.project_root.glob(f"**/{pattern}"):
                if file_path.is_file():
                    mode = file_path.stat().st_mode
                    perms = oct(mode)[-3:]

                    # Check if file is world-readable or group-readable
                    if perms[1] != '0' or perms[2] != '0':
                        findings["issues"].append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "permissions": perms,
                            "description": f"Sensitive file has overly permissive permissions: {perms}",
                            "severity": "MEDIUM",
                            "recommendation": "chmod 600"
                        })

        issue_count = len(findings["issues"])
        if issue_count > 0:
            self.log(f"Found {issue_count} permission issues", "WARNING")
        else:
            self.log("File permissions look good", "SUCCESS")

        return findings

    def check_dependencies(self) -> Dict:
        """Check for vulnerable dependencies"""
        self.log("Checking dependencies for known vulnerabilities...")

        findings = {
            "tool": "pip_audit",
            "status": "completed",
            "issues": []
        }

        # Check API requirements
        returncode, stdout, stderr = self.run_command([
            'pip-audit',
            '-r', 'ui/api/requirements.txt',
            '--format', 'json'
        ])

        if returncode == 0 and stdout:
            try:
                audit_data = json.loads(stdout)
                for dep in audit_data.get("dependencies", []):
                    if dep.get("vulns"):
                        for vuln in dep["vulns"]:
                            findings["issues"].append({
                                "package": dep["name"],
                                "version": dep["version"],
                                "vulnerability": vuln["id"],
                                "description": vuln.get("description", "")[:200],
                                "severity": "HIGH",
                                "fix_versions": vuln.get("fix_versions", [])
                            })
            except json.JSONDecodeError:
                pass

        issue_count = len(findings["issues"])
        if issue_count > 0:
            self.log(f"Found {issue_count} vulnerable dependencies", "CRITICAL")
        else:
            self.log("Dependencies are secure", "SUCCESS")

        return findings

    def check_config_security(self) -> Dict:
        """Check configuration security"""
        self.log("Checking configuration security...")

        findings = {
            "tool": "config_checker",
            "status": "completed",
            "issues": []
        }

        # Check for debug mode in production config
        config_files = list(self.project_root.glob("config/**/*.yaml")) + \
                      list(self.project_root.glob("config/**/*.yml"))

        import yaml

        for config_file in config_files:
            try:
                with open(config_file) as f:
                    config = yaml.safe_load(f)

                # Check for insecure settings
                if isinstance(config, dict):
                    # Check debug mode
                    if config.get("debug", False) and "production" in str(config_file):
                        findings["issues"].append({
                            "file": str(config_file.relative_to(self.project_root)),
                            "description": "Debug mode enabled in production config",
                            "severity": "HIGH",
                            "recommendation": "Set debug: false"
                        })

                    # Check for weak encryption
                    if "encryption" in config:
                        enc = config["encryption"]
                        if enc.get("algorithm") in ["DES", "RC4", "MD5"]:
                            findings["issues"].append({
                                "file": str(config_file.relative_to(self.project_root)),
                                "description": f"Weak encryption algorithm: {enc.get('algorithm')}",
                                "severity": "CRITICAL",
                                "recommendation": "Use AES-256 or ChaCha20"
                            })

            except Exception:
                continue

        issue_count = len(findings["issues"])
        if issue_count > 0:
            self.log(f"Found {issue_count} configuration issues", "WARNING")
        else:
            self.log("Configuration security looks good", "SUCCESS")

        return findings

    def generate_report(self, output_file: str = None) -> Dict:
        """Generate comprehensive security report"""
        self.log("\n" + "="*70)
        self.log("SIGMAX Security Audit Report")
        self.log("="*70 + "\n")

        report = {
            "timestamp": self.timestamp,
            "project": "SIGMAX",
            "audits": []
        }

        # Run all security checks
        report["audits"].append(self.check_bandit())
        report["audits"].append(self.check_secrets())
        report["audits"].append(self.check_permissions())
        report["audits"].append(self.check_dependencies())
        report["audits"].append(self.check_config_security())

        # Calculate statistics
        total_issues = sum(len(audit.get("issues", [])) for audit in report["audits"])
        critical_issues = sum(
            len([i for i in audit.get("issues", []) if i.get("severity") == "CRITICAL"])
            for audit in report["audits"]
        )
        high_issues = sum(
            len([i for i in audit.get("issues", []) if i.get("severity") == "HIGH"])
            for audit in report["audits"]
        )

        report["summary"] = {
            "total_issues": total_issues,
            "critical": critical_issues,
            "high": high_issues,
            "medium": total_issues - critical_issues - high_issues
        }

        # Print summary
        self.log("\n" + "="*70)
        self.log("AUDIT SUMMARY")
        self.log("="*70)
        self.log(f"Total Issues: {total_issues}")
        self.log(f"Critical: {critical_issues}", "CRITICAL" if critical_issues > 0 else "SUCCESS")
        self.log(f"High: {high_issues}", "WARNING" if high_issues > 0 else "SUCCESS")
        self.log(f"Medium: {report['summary']['medium']}", "INFO")
        self.log("="*70 + "\n")

        # Save report
        if output_file:
            output_path = self.project_root / output_file
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            self.log(f"Report saved to: {output_path}", "SUCCESS")

        return report


def main():
    parser = argparse.ArgumentParser(
        description="SIGMAX Comprehensive Security Audit"
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full security audit (all checks)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick security audit (critical checks only)'
    )
    parser.add_argument(
        '--report',
        type=str,
        help='Output report file (JSON format)'
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent

    auditor = SecurityAuditor(project_root)
    report = auditor.generate_report(args.report)

    # Exit with error code if critical issues found
    if report["summary"]["critical"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

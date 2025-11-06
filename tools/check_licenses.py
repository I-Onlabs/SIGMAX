#!/usr/bin/env python3
"""
License Compliance Checker

Verifies that all dependencies use permissive licenses only.
SIGMAX requires zero legal risk - only MIT, Apache 2.0, BSD-like licenses.
"""

import sys
import subprocess
from typing import Dict, List, Set, Tuple


# Allowed licenses (permissive only)
ALLOWED_LICENSES = {
    "MIT",
    "MIT License",
    "Apache 2.0",
    "Apache Software License",
    "Apache License 2.0",
    "BSD",
    "BSD License",
    "BSD-3-Clause",
    "BSD-2-Clause",
    "ISC",
    "ISC License (ISCL)",
    "Python Software Foundation License",
    "PSF",
    "Public Domain",
    "Unlicense",
    "CC0",
}

# Known forbidden licenses (copyleft)
FORBIDDEN_LICENSES = {
    "GPL",
    "GPLv2",
    "GPLv3",
    "AGPL",
    "AGPLv3",
    "LGPL",
    "LGPLv2",
    "LGPLv3",
    "Affero GPL",
    "Creative Commons",  # Depends on variant
    "CC BY-SA",  # ShareAlike is copyleft
}


class LicenseChecker:
    """Check license compliance for all dependencies"""

    def __init__(self):
        self.violations: List[Tuple[str, str]] = []
        self.warnings: List[Tuple[str, str]] = []
        self.compliant: List[Tuple[str, str]] = []

    def get_installed_packages(self) -> Dict[str, str]:
        """Get all installed packages and their licenses"""
        try:
            # Use pip-licenses if available (more reliable)
            result = subprocess.run(
                ["pip-licenses", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                import json
                packages = json.loads(result.stdout)
                return {pkg["Name"]: pkg.get("License", "UNKNOWN") for pkg in packages}

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        # Fallback: parse pip list and pip show
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print("Error: Failed to get package list")
                return {}

            import json
            packages_list = json.loads(result.stdout)

            licenses = {}
            for pkg in packages_list:
                pkg_name = pkg["name"]
                # Get license from pip show
                show_result = subprocess.run(
                    ["pip", "show", pkg_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if show_result.returncode == 0:
                    for line in show_result.stdout.split("\n"):
                        if line.startswith("License:"):
                            license_name = line.split(":", 1)[1].strip()
                            licenses[pkg_name] = license_name if license_name else "UNKNOWN"
                            break
                else:
                    licenses[pkg_name] = "UNKNOWN"

            return licenses

        except Exception as e:
            print(f"Error getting packages: {e}")
            return {}

    def check_license(self, package: str, license_name: str) -> str:
        """
        Check if a license is compliant.

        Returns:
            "compliant", "violation", or "warning"
        """
        if license_name == "UNKNOWN":
            return "warning"

        # Check for forbidden licenses
        for forbidden in FORBIDDEN_LICENSES:
            if forbidden.lower() in license_name.lower():
                return "violation"

        # Check for allowed licenses
        for allowed in ALLOWED_LICENSES:
            if allowed.lower() in license_name.lower():
                return "compliant"

        # Unknown license - warn
        return "warning"

    def run_check(self):
        """Run license compliance check"""
        print("\n🔍 SIGMAX License Compliance Check")
        print("=" * 80)
        print("\n✅ Allowed: MIT, Apache 2.0, BSD-like (permissive licenses)")
        print("❌ Forbidden: GPL, AGPL, LGPL (copyleft licenses)")
        print("\n" + "=" * 80)

        packages = self.get_installed_packages()

        if not packages:
            print("\n❌ Error: Could not retrieve package information")
            print("   Install pip-licenses for better results: pip install pip-licenses")
            return False

        print(f"\n📦 Checking {len(packages)} packages...\n")

        for package, license_name in sorted(packages.items()):
            status = self.check_license(package, license_name)

            if status == "violation":
                self.violations.append((package, license_name))
            elif status == "warning":
                self.warnings.append((package, license_name))
            else:
                self.compliant.append((package, license_name))

        # Print results
        self._print_results()

        # Return success/failure
        return len(self.violations) == 0

    def _print_results(self):
        """Print check results"""
        # Violations
        if self.violations:
            print("\n❌ LICENSE VIOLATIONS (COPYLEFT)")
            print("-" * 80)
            for package, license_name in self.violations:
                print(f"  {package:<30} {license_name}")

        # Warnings
        if self.warnings:
            print("\n⚠️  UNKNOWN LICENSES (MANUAL REVIEW REQUIRED)")
            print("-" * 80)
            for package, license_name in self.warnings:
                print(f"  {package:<30} {license_name}")

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"✅ Compliant:  {len(self.compliant)} packages")
        print(f"⚠️  Warnings:   {len(self.warnings)} packages")
        print(f"❌ Violations: {len(self.violations)} packages")

        if self.violations:
            print("\n🚨 ACTION REQUIRED:")
            print("   Remove or replace packages with copyleft licenses")
            print("   SIGMAX requires zero legal risk - only permissive licenses allowed")
        elif self.warnings:
            print("\n⚠️  ACTION RECOMMENDED:")
            print("   Manually verify licenses for packages with UNKNOWN license")
            print("   Check package documentation or PyPI page")
        else:
            print("\n✅ ALL PACKAGES COMPLIANT!")
            print("   No license violations detected")


def main():
    """Main entry point"""
    checker = LicenseChecker()

    # Check if pip-licenses is installed
    try:
        subprocess.run(
            ["pip-licenses", "--version"],
            capture_output=True,
            timeout=5
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("\n💡 TIP: Install pip-licenses for better results:")
        print("   pip install pip-licenses\n")

    success = checker.run_check()

    print("\n" + "=" * 80 + "\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

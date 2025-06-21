#!/usr/bin/env python3
"""
Anvyl Test Runner

Comprehensive test runner for Anvyl project that can run:
- Unit tests
- Integration tests  
- Manual test procedures
- Code coverage reports
- Performance tests
"""

import os
import sys
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any


class TestRunner:
    """Main test runner class."""
    
    def __init__(self, project_root: str = None):
        """Initialize test runner."""
        if project_root is not None:
            self.project_root = Path(project_root)
        else:
            self.project_root = Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "htmlcov"
        
    def run_unit_tests(self, verbose: bool = False, coverage: bool = True) -> bool:
        """Run unit tests with optional coverage."""
        print("🧪 Running unit tests...")
        
        cmd = ["python", "-m", "pytest", str(self.tests_dir / "unit")]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=anvyl",
                "--cov-report=term-missing",
                "--cov-report=html"
            ])
        
        # Add markers for unit tests only
        cmd.extend(["-m", "unit or not integration and not manual"])
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=False)
            success = result.returncode == 0
            
            if success:
                print("✅ Unit tests passed!")
                if coverage and self.coverage_dir.exists():
                    print(f"📊 Coverage report available at: {self.coverage_dir}/index.html")
            else:
                print("❌ Unit tests failed!")
                
            return success
            
        except Exception as e:
            print(f"💥 Error running unit tests: {e}")
            return False
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        cmd = ["python", "-m", "pytest", str(self.tests_dir / "integration")]
        
        if verbose:
            cmd.append("-v")
        
        # Add markers for integration tests
        cmd.extend(["-m", "integration"])
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=False)
            success = result.returncode == 0
            
            if success:
                print("✅ Integration tests passed!")
            else:
                print("❌ Integration tests failed!")
                
            return success
            
        except Exception as e:
            print(f"💥 Error running integration tests: {e}")
            return False
    
    def run_all_tests(self, verbose: bool = False, coverage: bool = True) -> bool:
        """Run all automated tests."""
        print("🚀 Running all automated tests...")
        
        unit_success = self.run_unit_tests(verbose, coverage)
        integration_success = self.run_integration_tests(verbose)
        
        overall_success = unit_success and integration_success
        
        if overall_success:
            print("🎉 All tests passed!")
        else:
            print("💔 Some tests failed!")
            
        return overall_success
    
    def run_linting(self) -> bool:
        """Run code linting and formatting checks."""
        print("🔍 Running code quality checks...")
        
        success = True
        
        # Run Black formatting check
        try:
            result = subprocess.run(
                ["python", "-m", "black", "--check", "anvyl/", "tests/"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ Black formatting check passed")
            else:
                print("❌ Black formatting check failed")
                print("💡 Run 'black anvyl/ tests/' to fix formatting")
                success = False
        except Exception as e:
            print(f"⚠️  Could not run Black: {e}")
        
        # Run isort import sorting check
        try:
            result = subprocess.run(
                ["python", "-m", "isort", "--check-only", "anvyl/", "tests/"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ isort import check passed")
            else:
                print("❌ isort import check failed")
                print("💡 Run 'isort anvyl/ tests/' to fix imports")
                success = False
        except Exception as e:
            print(f"⚠️  Could not run isort: {e}")
        
        # Run mypy type checking
        try:
            result = subprocess.run(
                ["python", "-m", "mypy", "anvyl/"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ MyPy type checking passed")
            else:
                print("❌ MyPy type checking failed")
                print(result.stdout)
                success = False
        except Exception as e:
            print(f"⚠️  Could not run MyPy: {e}")
        
        return success
    
    def show_manual_tests(self) -> None:
        """Display manual test procedures."""
        print("📋 Manual Test Procedures")
        print("=" * 50)
        
        manual_test_file = self.tests_dir / "manual" / "test_installation.md"
        
        if manual_test_file.exists():
            print(f"📖 Manual test procedures are available at:")
            print(f"   {manual_test_file}")
            print()
            print("📝 Manual test categories:")
            print("   1. Installation Tests")
            print("   2. Core Functionality Tests")
            print("   3. AI Agent Tests")
            print("   4. Web UI Tests")
            print("   5. Error Handling Tests")
            print("   6. Data Persistence Tests")
            print("   7. Performance Tests")
            print("   8. Documentation Tests")
            print()
            print("💡 Follow the procedures in the manual test file to verify")
            print("   end-to-end functionality that requires human interaction.")
        else:
            print("❌ Manual test procedures not found!")
    
    def clean_test_artifacts(self) -> None:
        """Clean up test artifacts and temporary files."""
        print("🧹 Cleaning test artifacts...")
        
        artifacts_to_clean = [
            self.coverage_dir,
            self.project_root / ".coverage",
            self.project_root / ".pytest_cache",
            self.project_root / ".mypy_cache",
        ]
        
        for artifact in artifacts_to_clean:
            if artifact.exists():
                if artifact.is_dir():
                    shutil.rmtree(artifact)
                else:
                    artifact.unlink()
                print(f"🗑️  Removed {artifact}")
        
        print("✅ Test artifacts cleaned")
    
    def setup_test_environment(self) -> bool:
        """Set up test environment."""
        print("⚙️  Setting up test environment...")
        
        # Check if we're in a virtual environment
        if not hasattr(sys, 'real_prefix') and sys.base_prefix == sys.prefix:
            print("⚠️  Warning: Not running in a virtual environment")
            print("💡 Consider using: python -m venv anvyl-test-env")
        
        # Install development dependencies
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
                cwd=self.project_root,
                check=True
            )
            print("✅ Development dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
        except Exception as e:
            print(f"💥 Error setting up environment: {e}")
            return False
    
    def run_smoke_tests(self) -> bool:
        """Run quick smoke tests to verify basic functionality."""
        print("💨 Running smoke tests...")
        
        smoke_tests = [
            # Test basic import
            ([sys.executable, "-c", "import anvyl; print('✅ Import successful')"], "Import test"),
            
            # Test CLI availability
            ([sys.executable, "-m", "anvyl.cli", "--help"], "CLI help test"),
            
            # Test version command
            ([sys.executable, "-m", "anvyl.cli", "version"], "Version command test"),
        ]
        
        success = True
        
        for cmd, description in smoke_tests:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print(f"✅ {description} passed")
                else:
                    print(f"❌ {description} failed")
                    print(f"   Error: {result.stderr}")
                    success = False
            except subprocess.TimeoutExpired:
                print(f"⏱️  {description} timed out")
                success = False
            except Exception as e:
                print(f"💥 {description} error: {e}")
                success = False
        
        return success
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        print("📊 Generating test report...")
        
        report = {
            "timestamp": subprocess.run(
                ["date"], capture_output=True, text=True
            ).stdout.strip(),
            "python_version": sys.version,
            "project_root": str(self.project_root),
            "tests": {}
        }
        
        # Run different test suites and collect results
        test_suites = [
            ("smoke", self.run_smoke_tests),
            ("linting", self.run_linting),
            ("unit", lambda: self.run_unit_tests(coverage=False)),
            ("integration", self.run_integration_tests),
        ]
        
        for suite_name, test_func in test_suites:
            try:
                result = test_func()
                report["tests"][suite_name] = {
                    "passed": result,
                    "status": "PASS" if result else "FAIL"
                }
            except Exception as e:
                report["tests"][suite_name] = {
                    "passed": False,
                    "status": "ERROR",
                    "error": str(e)
                }
        
        # Save report
        report_file = self.project_root / "test_report.json"
        import json
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"📋 Test report saved to: {report_file}")
        
        # Print summary
        print("\n📈 Test Summary:")
        for suite_name, results in report["tests"].items():
            status = results["status"]
            emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "💥"
            print(f"   {emoji} {suite_name.capitalize()}: {status}")
        
        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Anvyl Test Runner")
    parser.add_argument(
        "command",
        choices=["unit", "integration", "all", "lint", "manual", "clean", "setup", "smoke", "report"],
        help="Test command to run"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--project-root", help="Project root directory")
    
    args = parser.parse_args()
    
    runner = TestRunner(args.project_root)
    
    coverage = not args.no_coverage
    
    if args.command == "unit":
        success = runner.run_unit_tests(args.verbose, coverage)
    elif args.command == "integration":
        success = runner.run_integration_tests(args.verbose)
    elif args.command == "all":
        success = runner.run_all_tests(args.verbose, coverage)
    elif args.command == "lint":
        success = runner.run_linting()
    elif args.command == "manual":
        runner.show_manual_tests()
        success = True
    elif args.command == "clean":
        runner.clean_test_artifacts()
        success = True
    elif args.command == "setup":
        success = runner.setup_test_environment()
    elif args.command == "smoke":
        success = runner.run_smoke_tests()
    elif args.command == "report":
        report = runner.generate_test_report()
        success = all(r["passed"] for r in report["tests"].values() if "passed" in r)
    else:
        print(f"❌ Unknown command: {args.command}")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
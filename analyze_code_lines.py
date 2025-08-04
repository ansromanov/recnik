#!/usr/bin/env python3
"""
Lines of Code Analyzer
Analyzes and reports lines of code by technology, excluding temporary files.
"""

import os
from pathlib import Path
import subprocess
import sys


class CodeAnalyzer:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.excluded_paths = [
            ".venv/*",
            "venv/*",
            "env/*",
            "node_modules/*",
            "*/node_modules/*",
            "htmlcov/*",
            "*/htmlcov/*",
            "build/*",
            "*/build/*",
            "dist/*",
            "*/dist/*",
            "__pycache__/*",
            "*/__pycache__/*",
            ".git/*",
            "logs/*",
            "*/logs/*",
            "coverage/*",
            "*/coverage/*",
        ]

        self.file_types = {
            "Python": ["*.py"],
            "JavaScript": ["*.js", "*.jsx"],
            "TypeScript": ["*.ts", "*.tsx"],
            "CSS": ["*.css", "*.scss", "*.sass", "*.less"],
            "HTML": ["*.html", "*.htm"],
            "SQL": ["*.sql"],
            "YAML": ["*.yml", "*.yaml"],
            "JSON": ["*.json"],
            "Shell Scripts": ["*.sh", "*.bash", "*.zsh"],
            "Dockerfiles": ["Dockerfile*"],
            "Markdown": ["*.md"],
            "Go": ["*.go"],
            "Rust": ["*.rs"],
            "Java": ["*.java"],
            "C++": ["*.cpp", "*.cc", "*.cxx", "*.hpp", "*.h"],
            "C": ["*.c", "*.h"],
            "C#": ["*.cs"],
            "PHP": ["*.php"],
            "Ruby": ["*.rb"],
            "Swift": ["*.swift"],
            "Kotlin": ["*.kt"],
            "Config Files": [
                "Makefile",
                "*.conf",
                "requirements*.txt",
                "*.ini",
                "*.toml",
                "*.cfg",
            ],
        }

    def _build_find_command(self, patterns: list[str]) -> list[str]:
        """Build find command with exclusions"""
        cmd = ["find", str(self.root_path)]

        # Add exclusions
        for excluded in self.excluded_paths:
            cmd.extend(["-not", "-path", f"./{excluded}"])

        # Add patterns
        if len(patterns) == 1:
            cmd.extend(["-name", patterns[0]])
        else:
            # Multiple patterns with -o (OR)
            pattern_args = []
            for i, pattern in enumerate(patterns):
                if i > 0:
                    pattern_args.append("-o")
                pattern_args.extend(["-name", pattern])
            cmd.extend(["("] + pattern_args + [")"])

        return cmd

    def count_lines_for_type(
        self, technology: str, patterns: list[str]
    ) -> tuple[int, int]:
        """Count lines for a specific file type, returning (production_lines, test_lines)"""
        try:
            find_cmd = self._build_find_command(patterns)

            # Execute find command
            find_result = subprocess.run(
                find_cmd, capture_output=True, text=True, check=True
            )

            if not find_result.stdout.strip():
                return (0, 0)

            files = find_result.stdout.strip().split("\n")

            # Filter out special files for certain types
            if technology == "JSON":
                files = [f for f in files if not f.endswith("package-lock.json")]

            if not files or files == [""]:
                return (0, 0)

            # Separate test files from production files
            test_files = []
            prod_files = []

            for file in files:
                # Common test file patterns
                if any(
                    pattern in file.lower()
                    for pattern in [
                        "/test_",
                        "/tests/",
                        "_test.",
                        ".test.",
                        "/spec/",
                        "_spec.",
                        "test/",
                        "tests/",
                        "/conftest.py",
                        "/pytest.ini",
                    ]
                ):
                    test_files.append(file)
                else:
                    prod_files.append(file)

            def count_files(file_list):
                if not file_list:
                    return 0
                wc_cmd = ["wc", "-l"] + file_list
                wc_result = subprocess.run(wc_cmd, capture_output=True, text=True)
                if wc_result.returncode != 0 or not wc_result.stdout.strip():
                    return 0

                lines = wc_result.stdout.strip().split("\n")
                if len(lines) == 1:
                    return int(lines[0].split()[0])
                else:
                    total_line = lines[-1]
                    if "total" in total_line:
                        return int(total_line.split()[0])
                    else:
                        return sum(
                            int(line.split()[0]) for line in lines if line.strip()
                        )

            prod_lines = count_files(prod_files)
            test_lines = count_files(test_files)

            return (prod_lines, test_lines)

        except (subprocess.CalledProcessError, ValueError, IndexError) as e:
            print(f"Error counting lines for {technology}: {e}", file=sys.stderr)
            return (0, 0)

    def analyze(self) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
        """Analyze all file types and return (total_results, prod_results, test_results)"""
        total_results = {}
        prod_results = {}
        test_results = {}

        print("🔍 Analyzing repository...")
        print(f"📁 Root path: {self.root_path.absolute()}")
        print()

        for technology, patterns in self.file_types.items():
            prod_count, test_count = self.count_lines_for_type(technology, patterns)
            total_count = prod_count + test_count

            if total_count >= 500:
                print(
                    f"Counting {technology}... ✅ {total_count:,} lines ({prod_count:,} code, {test_count:,} tests)"
                )
                total_results[technology] = total_count
                prod_results[technology] = prod_count
                test_results[technology] = test_count

        return total_results, prod_results, test_results

    def generate_report(
        self,
        total_results: dict[str, int],
        prod_results: dict[str, int],
        test_results: dict[str, int],
    ) -> None:
        """Generate and print comprehensive report"""
        if not total_results:
            print("❌ No technologies with 500+ lines of code found!")
            return

        total = sum(total_results.values())
        total_prod = sum(prod_results.values())
        total_test = sum(test_results.values())

        print("\n" + "=" * 65)
        print("📊 Lines of Code Analysis Report")
        print("=" * 65)
        print(f"📍 Repository: {self.root_path.absolute()}")
        print(f"📝 Total Lines of Code: {total:,}")
        print(
            f"💻 Production Code: {total_prod:,} lines ({(total_prod / total) * 100:.1f}%)"
        )
        print(f"🧪 Test Code: {total_test:,} lines ({(total_test / total) * 100:.1f}%)")

        # Test coverage ratio insight
        if total_prod > 0:
            test_ratio = total_test / total_prod
            print(f"🎯 Test-to-Code Ratio: {test_ratio:.2f}:1")
        print()

        # Sort by line count (descending)
        sorted_data = sorted(total_results.items(), key=lambda x: x[1], reverse=True)

        for tech, lines in sorted_data:
            percentage = (lines / total) * 100
            bar_length = int(percentage / 2)  # Scale bar to fit
            bar = "█" * bar_length
            print(f"{tech:<25} {lines:>6,} lines ({percentage:5.1f}%) {bar}")

        print()
        print("📈 Key Insights:")
        self._generate_insights(
            sorted_data, total, total_results, prod_results, test_results
        )

        print()
        print("🏗️  Architecture Breakdown:")
        self._generate_architecture_breakdown(total_results, total)

    def _generate_architecture_breakdown(
        self, results: dict[str, int], total: int
    ) -> None:
        """Generate architecture-specific breakdown"""
        # Define architecture categories
        backend_techs = [
            "Python",
            "Java",
            "Go",
            "Rust",
            "C++",
            "C",
            "C#",
            "PHP",
            "Ruby",
            "SQL",
        ]
        frontend_techs = ["JavaScript", "TypeScript", "CSS", "HTML"]
        devops_techs = ["YAML", "Dockerfiles", "Shell Scripts", "Config Files"]
        docs_techs = ["Markdown", "JSON"]

        backend_total = sum(results.get(tech, 0) for tech in backend_techs)
        frontend_total = sum(results.get(tech, 0) for tech in frontend_techs)
        devops_total = sum(results.get(tech, 0) for tech in devops_techs)
        docs_total = sum(results.get(tech, 0) for tech in docs_techs)

        categories = [
            ("Backend", backend_total),
            ("Frontend", frontend_total),
            ("DevOps/Infrastructure", devops_total),
            ("Documentation/Config", docs_total),
        ]

        for category, count in categories:
            if count > 0:
                percentage = (count / total) * 100
                print(f"{category:<25} {count:>8,} lines ({percentage:5.1f}%)")

    def _generate_insights(
        self,
        sorted_results: list[tuple[str, int]],
        total: int,
        total_results: dict[str, int],
        prod_results: dict[str, int],
        test_results: dict[str, int],
    ) -> None:
        """Generate insights based on the analysis"""
        if not sorted_results:
            return

        dominant_tech, dominant_count = sorted_results[0]
        dominant_percentage = (dominant_count / total) * 100
        tech_dict = dict(sorted_results)

        # Dominant technology insight
        print(
            f"• {dominant_tech} dominates with {dominant_percentage:.1f}% of the codebase"
        )

        # Test coverage analysis
        total_prod = sum(prod_results.values())
        total_test = sum(test_results.values())
        if total_prod > 0:
            test_ratio = total_test / total_prod
            if test_ratio >= 0.5:
                print(
                    f"• Excellent test coverage with {test_ratio:.2f}:1 test-to-code ratio"
                )
            elif test_ratio >= 0.3:
                print(
                    f"• Good test coverage with {test_ratio:.2f}:1 test-to-code ratio"
                )
            elif test_ratio >= 0.1:
                print(
                    f"• Moderate test coverage with {test_ratio:.2f}:1 test-to-code ratio"
                )
            elif test_ratio > 0:
                print(
                    f"• Limited test coverage with {test_ratio:.2f}:1 test-to-code ratio"
                )
            else:
                print("• No test files detected")

        # Multi-technology analysis
        significant_techs = [
            tech for tech, count in sorted_results if count > total * 0.1
        ]  # >10% of total
        if len(significant_techs) > 1:
            print(
                f"• Multi-technology stack with {len(significant_techs)} major components"
            )

        # Documentation presence
        docs_techs = ["Markdown", "JSON"]
        docs_total = sum(tech_dict.get(tech, 0) for tech in docs_techs)
        if docs_total > total * 0.05:  # >5% of total
            docs_pct = (docs_total / total) * 100
            print(f"• Well-documented project ({docs_pct:.1f}% documentation)")

        # Infrastructure/DevOps presence
        infra_techs = ["YAML", "Dockerfiles", "Shell Scripts", "Config Files"]
        infra_total = sum(tech_dict.get(tech, 0) for tech in infra_techs)
        if infra_total > total * 0.05:  # >5% of total
            infra_pct = (infra_total / total) * 100
            print(
                f"• Comprehensive DevOps setup ({infra_pct:.1f}% infrastructure code)"
            )

        # Frontend presence
        frontend_techs = ["JavaScript", "TypeScript", "CSS", "HTML"]
        frontend_total = sum(tech_dict.get(tech, 0) for tech in frontend_techs)
        if frontend_total > total * 0.1:  # >10% of total
            frontend_pct = (frontend_total / total) * 100
            print(f"• Substantial frontend codebase ({frontend_pct:.1f}% frontend)")

        # Containerization
        if tech_dict.get("Dockerfiles", 0) > 0:
            print("• Containerized application with Docker support")


def save_results_to_json(
    total_results, prod_results, test_results, filepath="code_analysis_results.json"
):
    """Save analysis results to JSON file"""
    import json

    output = {
        "total": total_results,
        "production": prod_results,
        "tests": test_results,
        "summary": {
            "total_lines": sum(total_results.values()),
            "production_lines": sum(prod_results.values()),
            "test_lines": sum(test_results.values()),
        },
    }

    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Results saved to {filepath}")
    return output


def load_previous_results(filepath="code_analysis_results.json"):
    """Load previous analysis results from JSON file"""
    import json

    try:
        with open(filepath) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ No previous results found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in {filepath}")
        return None


def show_diff(current_results, previous_results):
    """Show differences between current and previous results"""
    if not previous_results:
        print("❌ Cannot show diff: no previous results available")
        return

    print("\n" + "=" * 65)
    print("📊 Diff: Current vs Previous Analysis")
    print("=" * 65)
    print()

    # Compare totals
    current_total = current_results["total"]
    previous_total = previous_results["total"]

    current_summary = current_results["summary"]
    previous_summary = previous_results["summary"]

    # Overall changes
    total_diff = current_summary["total_lines"] - previous_summary["total_lines"]
    prod_diff = (
        current_summary["production_lines"] - previous_summary["production_lines"]
    )
    test_diff = current_summary["test_lines"] - previous_summary["test_lines"]

    print("📈 Overall Changes:")
    print(
        f"Total Lines:      {previous_summary['total_lines']:,} → {current_summary['total_lines']:,} ({total_diff:+,})"
    )
    print(
        f"Production Lines: {previous_summary['production_lines']:,} → {current_summary['production_lines']:,} ({prod_diff:+,})"
    )
    print(
        f"Test Lines:       {previous_summary['test_lines']:,} → {current_summary['test_lines']:,} ({test_diff:+,})"
    )
    print()

    # Technology-specific changes
    all_techs = set(current_total.keys()) | set(previous_total.keys())
    changes = []

    for tech in all_techs:
        current_count = current_total.get(tech, 0)
        previous_count = previous_total.get(tech, 0)
        diff = current_count - previous_count

        if diff != 0:
            changes.append((tech, previous_count, current_count, diff))

    if changes:
        print("🔍 Technology Changes:")
        changes.sort(
            key=lambda x: abs(x[3]), reverse=True
        )  # Sort by absolute difference

        for tech, prev_count, curr_count, diff in changes:
            if prev_count == 0:
                status = "NEW"
                print(f"{tech:<25} {status:<8} → {curr_count:>6,} lines ({diff:+,})")
            elif curr_count == 0:
                status = "REMOVED"
                print(f"{tech:<25} {prev_count:>6,} → {status:<8} ({diff:+,})")
            else:
                percentage_change = (diff / prev_count) * 100 if prev_count > 0 else 0
                print(
                    f"{tech:<25} {prev_count:>6,} → {curr_count:>6,} ({diff:+,}, {percentage_change:+.1f}%)"
                )
    else:
        print("✅ No changes detected between analyses")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze lines of code by technology")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to analyze (default: current directory)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--csv", action="store_true", help="Output results as CSV")
    parser.add_argument(
        "--write", action="store_true", help="Save results to JSON file"
    )
    parser.add_argument(
        "--diff", action="store_true", help="Show diff with previous results"
    )
    parser.add_argument(
        "--output",
        default="code_analysis_results.json",
        help="Output file for --write (default: code_analysis_results.json)",
    )

    args = parser.parse_args()

    # Verify path exists
    if not os.path.exists(args.path):
        print(f"❌ Error: Path '{args.path}' does not exist")
        sys.exit(1)

    analyzer = CodeAnalyzer(args.path)
    total_results, prod_results, test_results = analyzer.analyze()

    # Handle diff option first if requested
    if args.diff:
        previous_results = load_previous_results(args.output)
        current_results = {
            "total": total_results,
            "production": prod_results,
            "tests": test_results,
            "summary": {
                "total_lines": sum(total_results.values()),
                "production_lines": sum(prod_results.values()),
                "test_lines": sum(test_results.values()),
            },
        }
        show_diff(current_results, previous_results)

    # Handle write option
    if args.write:
        save_results_to_json(total_results, prod_results, test_results, args.output)

    # Handle output format options
    if args.json:
        import json

        output = {
            "total": total_results,
            "production": prod_results,
            "tests": test_results,
        }
        print(json.dumps(output, indent=2))
    elif args.csv:
        print("Technology,Total Lines,Production Lines,Test Lines,Percentage")
        total = sum(total_results.values())
        for tech, lines in sorted(
            total_results.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (lines / total) * 100
            prod_lines = prod_results.get(tech, 0)
            test_lines = test_results.get(tech, 0)
            print(f'"{tech}",{lines},{prod_lines},{test_lines},{percentage:.1f}')
    elif not args.write and not args.diff:
        # Only show the full report if not using write or diff options
        analyzer.generate_report(total_results, prod_results, test_results)


if __name__ == "__main__":
    main()

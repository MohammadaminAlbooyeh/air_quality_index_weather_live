#!/bin/bash
# Local CI Check Script
# This script runs all CI checks locally before pushing to GitHub

set -e  # Exit on any error

echo "🚀 Running Local CI Checks..."
echo ""

# Activate virtual environment
source .venv/bin/activate

echo "📋 Step 1: Running Flake8 Linter..."
flake8 backend/ tests/ --count --statistics
echo "✅ Flake8 passed!"
echo ""

echo "🎨 Step 2: Checking Code Formatting (Black)..."
black --check backend/ tests/
echo "✅ Black formatting check passed!"
echo ""

echo "📦 Step 3: Checking Import Sorting (isort)..."
isort --check-only backend/ tests/
echo "✅ isort check passed!"
echo ""

echo "🧪 Step 4: Running Unit Tests..."
pytest tests/ -v
echo "✅ All tests passed!"
echo ""

echo "📊 Step 5: Generating Coverage Report..."
pytest tests/ --cov=backend --cov-report=term --cov-report=html
echo "✅ Coverage report generated!"
echo "   View HTML report: open htmlcov/index.html"
echo ""

echo "✨ All CI checks passed successfully! ✨"
echo "You're ready to push to GitHub! 🚀"

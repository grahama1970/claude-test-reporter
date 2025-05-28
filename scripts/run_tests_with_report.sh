#!/bin/bash
# Run tests and generate Markdown report

cd /home/graham/workspace/experiments/sparta
source .venv/bin/activate

echo "🧪 Running SPARTA tests with report generation..."

# Run the reporter
python -m src.sparta.utils.test_reporter

# Show report location
echo "📄 Reports available in docs/reports/"
ls -la docs/reports/test_report_*.md | tail -5
# Cost Analysis Dashboard (HTML)

Interactive HTML dashboards for analyzing modernization costs, combining Konveyor analysis with LLM evaluation results.

## Overview

The cost dashboard provides a comprehensive view of your application modernization project costs by combining:
- **Konveyor analysis reports** - Rule violations detected in your codebase
- **LLM evaluation results** - Model performance data from your evaluations
- **Cost modeling** - API costs + manual development estimates
- **Optimization recommendations** - Best model selection per rule category

**Output**: Single HTML file with interactive charts that works offline and can be shared via email.

## Quick Start

### Step 1: Run Konveyor Analysis

```bash
# Analyze your Java application
konveyor-analyzer analyze \
  --input /path/to/your/app \
  --output konveyor_analysis.json \
  --target quarkus
```

### Step 2: Run LLM Evaluation

```bash
# Evaluate LLM fixes for detected violations
python evaluate.py \
  --benchmark benchmarks/test_cases/java-ee-quarkus-migration.yaml \
  --output results/
```

### Step 3: Generate Cost Dashboard

```bash
# Generate interactive HTML dashboard
python scripts/generate_cost_dashboard.py \
  --konveyor-analysis konveyor_analysis.json \
  --evaluation-results results/results_latest.json \
  --output reports/cost_dashboard.html

# Open in browser
open reports/cost_dashboard.html
```

## Dashboard Panels

### Executive Summary (Top Row)

**Total Estimated Cost**
- Aggregate project cost: LLM API costs + manual development hours
- Color-coded: Green (<$10K), Yellow ($10K-$50K), Orange ($50K-$100K), Red (>$100K)

**Automation Rate**
- Percentage of violations that can be auto-fixed with LLM
- Goal: >85% automation for cost-effective modernization

**LLM Automation Savings**
- Total savings: Manual cost - LLM cost
- Typical: 99%+ cost reduction

**ROI (Return on Investment)**
- Formula: (Manual Cost - Total Cost) / Total Cost × 100
- Shows business value of LLM-assisted migration

### Cost Analysis Charts

**Cost Breakdown by Model**
- Per-fix cost × success rate for each model
- Shows effective cost per successful fix
- Example: GPT-4o @ $0.176/fix × 85% = $0.207 effective cost

**LLM vs Manual Development**
- Bar chart comparing costs:
  - **LLM Automation** - Pure API costs
  - **Manual Development** - Developer time @ configurable hourly rate
  - **Hybrid** - LLM + manual review (recommended)

**Violation Distribution**
- Pie chart showing breakdown by category
- Helps prioritize which areas to tackle first

### Optimization Tables

**Optimal Model Selection by Rule Category**
- Recommends best model for each violation category
- Based on: success rate, cost/fix, and total violations
- Example output:

| Rule Category | Best Model | Success Rate | Cost/Fix | # Violations | Estimated Cost |
|--------------|-----------|--------------|----------|--------------|----------------|
| EJB to CDI | claude-3-5-sonnet | 92% | $0.27 | 45 | $12.15 |
| JMS to Reactive | gpt-4o | 85% | $0.18 | 23 | $4.14 |
| Persistence | gpt-4o | 88% | $0.18 | 67 | $12.06 |

**Detailed Rule-by-Rule Analysis**
- Every rule with:
  - Violation count
  - Recommended model
  - Success rate
  - Cost per fix
  - Total estimated cost
  - Auto-fixable flag

**Recommended Action Plan**
- Phased migration strategy
- Example:

| Phase | Recommended Action | Use Model | Violations | Est. Cost | Priority |
|-------|-------------------|-----------|------------|-----------|----------|
| 1 | Auto-fix EJB migrations | claude-3-5-sonnet | 45 | $12.15 | P0 |
| 2 | Auto-fix persistence | gpt-4o | 67 | $12.06 | P0 |
| 3 | Manual review complex cases | human | 12 | $900 | P1 |

### Performance Visualizations

**Model Performance by Rule Category**
- Bar chart showing each model's success rate per category
- Identifies which models excel at specific migration types

**Success Rate Trends**
- Line chart showing model performance over time
- Tracks improvements as models are updated

## Configuration Options

### Command-Line Arguments

```bash
python scripts/generate_cost_dashboard.py \
  --konveyor-analysis <path>     # Konveyor analysis JSON (required)
  --evaluation-results <path>    # Evaluation results JSON (required)
  --output <path>                # Output HTML file (default: cost_dashboard.html)
  --hourly-rate <amount>         # Developer hourly rate (default: 75)
  --min-success-rate <percent>   # Threshold for auto-fixable (default: 70)
  --project-name <name>          # Project name for title
```

### Example with Custom Settings

```bash
python scripts/generate_cost_dashboard.py \
  --konveyor-analysis analysis/cool-store.json \
  --evaluation-results results/results_20241011.json \
  --output reports/cool-store-cost-analysis.html \
  --hourly-rate 100 \
  --min-success-rate 80 \
  --project-name "Cool Store Migration"
```

## Input Data Formats

### Konveyor Analysis Format

Expected JSON structure from Konveyor analyzer:

```json
{
  "violations": [
    {
      "rule_id": "ee-to-quarkus-00000",
      "category": "ejb-migration",
      "severity": "medium",
      "description": "Replace @Stateless with @ApplicationScoped",
      "file": "src/main/java/UserService.java",
      "line": 15,
      "effort": 3,
      "incidents": 1
    }
  ],
  "summary": {
    "total_incidents": 156,
    "categories": {
      "ejb-migration": 45,
      "persistence": 67,
      "jms-reactive": 23
    }
  }
}
```

### Evaluation Results Format

Expected JSON from `evaluate.py`:

```json
[
  {
    "test_case_id": "tc001",
    "rule_id": "ee-to-quarkus-00000",
    "model_name": "gpt-4o",
    "timestamp": "2024-10-11T14:30:25",
    "passed": true,
    "metrics": {
      "functional_correctness": true,
      "compiles": true
    },
    "estimated_cost": 0.00176
  }
]
```

## Use Cases

### 1. Project Budget Planning

```bash
# Generate cost estimate for stakeholder approval
python scripts/generate_cost_dashboard.py \
  --konveyor-analysis analysis.json \
  --evaluation-results results.json \
  --output proposal/migration-cost-estimate.html

# Email to stakeholders or include in project proposal
```

### 2. Model Selection

```bash
# Compare different models to find optimal mix
# Run evaluations with different models, then generate dashboard
# Dashboard shows which model is best for each rule category
```

### 3. Progress Tracking

```bash
# Generate weekly dashboards to track progress
python scripts/generate_cost_dashboard.py \
  --konveyor-analysis current_state.json \
  --evaluation-results results/week_12.json \
  --output reports/week_12_progress.html

# Compare against previous weeks
```

### 4. Executive Reporting

```bash
# Generate quarterly report for executives
python scripts/generate_cost_dashboard.py \
  --konveyor-analysis analysis.json \
  --evaluation-results results.json \
  --output quarterly/Q4_migration_report.html

# Print to PDF or email as HTML
```

## Sharing and Exporting

### Email to Stakeholders

The dashboard is a single HTML file with all assets embedded. Simply:

1. Generate the dashboard
2. Attach to email
3. Recipients can open directly in browser (no server needed)

### Print to PDF

```bash
# Option 1: Use browser print function
open cost_dashboard.html
# File → Print → Save as PDF

# Option 2: Command-line with wkhtmltopdf
wkhtmltopdf cost_dashboard.html cost_dashboard.pdf
```

### Archive for Project Records

```bash
# Create timestamped archive
DATE=$(date +%Y%m%d)
cp cost_dashboard.html archives/migration_cost_${DATE}.html
```

## Customization

### Adjust Cost Thresholds

Edit `scripts/generate_cost_dashboard.py`:

```python
# Change color-coded cost thresholds
thresholds = {
    'green': 5000,    # <$5K
    'yellow': 25000,  # $5K-$25K
    'orange': 75000,  # $25K-$75K
    'red': 75000      # >$75K
}
```

### Add Custom Charts

The dashboard uses Chart.js. Add new charts in the template:

```javascript
// Add custom chart
const myChart = new Chart(ctx, {
    type: 'line',
    data: { /* your data */ },
    options: { /* your options */ }
});
```

### Branding

Customize colors and styling in the HTML template:

```css
/* Change primary color scheme */
:root {
    --primary-color: #your-brand-color;
    --background-color: #your-bg-color;
}
```

## Troubleshooting

### Dashboard Shows "No Data"

1. Check input files exist:
   ```bash
   ls -lh konveyor_analysis.json results/results_latest.json
   ```

2. Validate JSON format:
   ```bash
   python -m json.tool konveyor_analysis.json
   ```

3. Check evaluation results not empty:
   ```bash
   cat results/results_latest.json | jq 'length'
   ```

### Charts Not Rendering

1. Open browser console (F12) for JavaScript errors
2. Ensure Chart.js CDN is accessible (or use offline version)
3. Check data arrays are properly formatted

### Cost Calculations Seem Wrong

1. Verify hourly rate is correct:
   ```bash
   --hourly-rate 75  # Default is $75/hr
   ```

2. Check model costs in script match current pricing
3. Ensure evaluation results have `estimated_cost` field

## Best Practices

### 1. Generate Regularly

```bash
# Weekly dashboard generation
cron: 0 9 * * 1  # Every Monday at 9am
python scripts/generate_cost_dashboard.py \
  --konveyor-analysis analysis.json \
  --evaluation-results results/latest.json \
  --output reports/weekly/$(date +%Y%m%d)_dashboard.html
```

### 2. Version Control

```bash
# Keep dashboards in git for historical comparison
git add reports/cost_dashboard_*.html
git commit -m "Weekly cost dashboard: $(date +%Y-%m-%d)"
```

### 3. Combine with Evaluation Reports

```bash
# Generate both HTML report and cost dashboard
python evaluate.py --format html --output results/
python scripts/generate_cost_dashboard.py \
  --evaluation-results results/results_latest.json \
  --output results/cost_dashboard.html
```

### 4. Share Appropriately

- **Technical team**: Share full dashboard with all details
- **Management**: Focus on Executive Summary panels
- **Finance**: Highlight ROI and cost breakdown sections

## Advanced: Automated Report Generation

Create a script to automate the entire workflow:

```bash
#!/bin/bash
# scripts/generate_weekly_report.sh

DATE=$(date +%Y%m%d)
OUTPUT_DIR="reports/weekly/${DATE}"

# Create output directory
mkdir -p ${OUTPUT_DIR}

# Run Konveyor analysis
konveyor-analyzer analyze \
  --input /path/to/app \
  --output ${OUTPUT_DIR}/analysis.json

# Run evaluation
python evaluate.py \
  --benchmark benchmarks/test_cases/ \
  --output ${OUTPUT_DIR}/

# Generate cost dashboard
python scripts/generate_cost_dashboard.py \
  --konveyor-analysis ${OUTPUT_DIR}/analysis.json \
  --evaluation-results ${OUTPUT_DIR}/results_latest.json \
  --output ${OUTPUT_DIR}/cost_dashboard.html

# Email to stakeholders
echo "Weekly Migration Report" | mail \
  -s "Migration Cost Dashboard - Week ${DATE}" \
  -a ${OUTPUT_DIR}/cost_dashboard.html \
  team@example.com

echo "Report generated: ${OUTPUT_DIR}/cost_dashboard.html"
```

## Comparison: HTML vs Grafana

| Feature | HTML Dashboard | Grafana |
|---------|---------------|---------|
| Setup complexity | Low - single script | High - requires servers |
| Live data | No - static snapshot | Yes - auto-refresh |
| Sharing | Email as file | Share URL |
| Offline access | ✅ Yes | ❌ No |
| Alerting | ❌ No | ✅ Yes |
| Time-series analysis | Limited | ✅ Excellent |
| Infrastructure needed | None | Prometheus + Grafana |
| Best for | One-time reports, archives | Ongoing monitoring |

**Recommendation**: Use HTML dashboards for project-based cost analysis and stakeholder reporting. Only move to Grafana if you need continuous monitoring across multiple projects.

## Contributing

Improvements to the dashboard generator:

1. Add new chart types
2. Enhance cost modeling (e.g., include infrastructure costs)
3. Add more customization options
4. Improve PDF export formatting

Submit PRs to enhance the dashboard!

## License

Apache 2.0

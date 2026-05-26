# aws-cost-cli

A command-line tool for analyzing AWS spend across services, regions, accounts, and tags — with forecasting, anomaly detection, budget tracking, and Slack notifications.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-28%20passed-brightgreen)
![Docker](https://img.shields.io/badge/docker-tektribe%2Faws--cost--cli-blue?logo=docker)

---

## Commands

| Command | What it does |
|---|---|
| `summary` | Monthly totals for the last N months |
| `daily` | Day-by-day breakdown for any period |
| `services` | Cost by AWS service |
| `regions` | Cost by AWS region |
| `accounts` | Cost by linked account (AWS Organizations) |
| `tags` | Cost by resource tag key |
| `compare` | Side-by-side with the previous equivalent period |
| `forecast` | Projected spend for the rest of this month or year |
| `anomalies` | Unusual spend spikes detected by AWS |
| `budget set/list/status` | Set monthly budgets and track usage |
| `notify slack` | Send a cost summary to a Slack channel |
| `watch` | Live-refresh cost view in the terminal |

---

## Install

**From source (recommended while in early development)**

```bash
git clone https://github.com/Mide69/aws-cost-cli.git
cd aws-cost-cli
pip install -e .
```

**With Docker (no Python required)**

```bash
docker pull tektribe/aws-cost-cli:latest

docker run --rm \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e AWS_DEFAULT_REGION \
  tektribe/aws-cost-cli services
```

---

## Prerequisites

- AWS credentials configured (see [Authentication](#authentication))
- Cost Explorer enabled in your AWS account:
  `AWS Console → Billing → Cost Explorer → Enable`
  *(takes up to 24 hours to activate on a new account)*

---

## Usage

### Time periods

All commands accept `--period` with the following values:

| Flag | Range |
|---|---|
| `yesterday` | Previous calendar day |
| `7d` | Last 7 days |
| `30d` | Last 30 days |
| `mtd` | Month to date *(default)* |
| `last-month` | Previous full calendar month |
| `3m` | Last 3 months |
| `6m` | Last 6 months |
| `ytd` | Year to date |
| `2026-03` | Specific month (YYYY-MM) |
| `--start` / `--end` | Fully custom date range |

### Examples

```bash
# Monthly overview
aws-cost summary
aws-cost summary --months 12

# Daily spend last week
aws-cost daily --period 7d

# Services this month, top 10 only
aws-cost services --top 10

# Services last month vs the month before
aws-cost services --period last-month --compare

# Which regions are costing the most?
aws-cost regions --period ytd

# Break down cost by your Environment tag
aws-cost tags --tag-key Environment

# Full comparison report (services, ranked by change)
aws-cost compare --period last-month --by SERVICE

# Forecast: how much will this month cost?
aws-cost forecast

# Anomalies in the last 14 days above $5 impact
aws-cost anomalies --days 14 --threshold 5

# Set a monthly budget and check it
aws-cost budget set total 500
aws-cost budget set "Amazon EC2" 200
aws-cost budget status

# Send a Slack report
export AWS_COST_SLACK_WEBHOOK=https://hooks.slack.com/services/...
aws-cost notify slack --period last-month

# Export to CSV
aws-cost --format json services > services.json
aws-cost --format csv services > services.csv

# Live view, refreshes every 30 seconds
aws-cost watch --interval 30

# Use a named AWS profile
aws-cost --profile production services
```

---

## Authentication

The tool uses the standard AWS credential chain — no custom credential flags needed:

1. Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
2. AWS credentials file: `~/.aws/credentials`
3. AWS config file: `~/.aws/config`
4. IAM role (EC2, ECS, Lambda, etc.)

To configure credentials:

```bash
aws configure
```

---

## IAM Permissions

Minimum permissions required:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast",
        "ce:GetAnomalies"
      ],
      "Resource": "*"
    }
  ]
}
```

> Cost Explorer charges ~$0.01 per API request.

---

## Docker

Pull from Docker Hub:

```bash
docker pull tektribe/aws-cost-cli:latest
```

Run with environment variable credentials:

```bash
docker run --rm \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e AWS_DEFAULT_REGION=us-east-1 \
  tektribe/aws-cost-cli services --period last-month --compare
```

Run with a mounted credentials file:

```bash
docker run --rm \
  -v ~/.aws:/root/.aws:ro \
  tektribe/aws-cost-cli summary
```

Build locally from source:

```bash
docker build -t tektribe/aws-cost-cli .
```

---

## Development

```bash
git clone https://github.com/Mide69/aws-cost-cli.git
cd aws-cost-cli

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"

pytest tests/ -v
pytest tests/ -v --cov=aws_cost_cli
```

### Project structure

```
aws_cost_cli/
├── cli.py            Click commands and routing
├── cost_explorer.py  AWS Cost Explorer API calls
├── formatter.py      Rich terminal output and CSV export
├── periods.py        Time period resolution (7d, mtd, last-month…)
├── budget.py         Local budget storage (~/.aws-cost-cli/)
└── notify.py         Slack webhook notifications
```

---

## License

MIT

# aws-cost-cli

A Python CLI for analyzing and monitoring your AWS spending via the [Cost Explorer API](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html).

## Features

| Command | Description |
|---------|-------------|
| `aws-cost summary` | Monthly cost totals for the last N months |
| `aws-cost services` | Cost breakdown by AWS service |
| `aws-cost accounts` | Cost breakdown by linked account (AWS Organizations) |
| `aws-cost forecast` | Spend forecast for the rest of this month or year |
| `aws-cost anomalies` | Anomaly detection — flag unexpected spend spikes |

All commands support `--format json` for scripting/piping.

## Requirements

- Python 3.9+
- AWS credentials configured (env vars, `~/.aws/credentials`, or IAM role)
- IAM permissions: `ce:GetCostAndUsage`, `ce:GetCostForecast`, `ce:GetAnomalies`

## Installation

```bash
pip install aws-cost-cli
```

Or install from source:

```bash
git clone https://github.com/Mide69/aws-cost-cli.git
cd aws-cost-cli
pip install -e .
```

## Usage

```bash
# Last 6 months of total spend
aws-cost summary

# Last 3 months
aws-cost summary --months 3

# Cost by service for the current month
aws-cost services

# Cost by service for a specific month
aws-cost services --month 2026-03

# Cost by linked account
aws-cost accounts --month 2026-05

# Forecast remaining spend this month
aws-cost forecast

# Forecast remaining spend this year
aws-cost forecast --period YEARLY

# Anomalies in the last 30 days with >$10 impact
aws-cost anomalies

# Anomalies in the last 7 days with >$50 impact
aws-cost anomalies --days 7 --threshold 50

# JSON output (pipe-friendly)
aws-cost --format json services
aws-cost --format json anomalies | jq '.[].service'

# Use a specific AWS profile
aws-cost --profile prod summary
```

## Required IAM Permissions

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

> **Note:** Cost Explorer must be enabled in your AWS account (AWS Console → Billing → Cost Explorer). There is a small per-request charge (~$0.01 per API call).

## Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=aws_cost_cli
```

## License

MIT

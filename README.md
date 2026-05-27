
# aws-cost-cli

A command-line tool for analyzing AWS spend across services, regions, accounts, and tags — with forecasting, anomaly detection, budget tracking, Slack notifications, and a live watch mode.

![CI](https://github.com/Mide69/aws-cost-cli/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-tektribe%2Faws--cost--cli-blue?logo=docker)
![PyPI](https://img.shields.io/badge/pypi-aws--cost--cli-orange?logo=pypi)

---

## Table of Contents

1. [What This Tool Does](#what-this-tool-does)
2. [Before You Start](#before-you-start)
3. [Step 1 — Create an AWS Account](#step-1--create-an-aws-account)
4. [Step 2 — Enable Cost Explorer](#step-2--enable-cost-explorer)
5. [Step 3 — Create an IAM User and Access Keys](#step-3--create-an-iam-user-and-access-keys)
6. [Step 4 — Install the Tool](#step-4--install-the-tool)
   - [Option A — Install from PyPI](#option-a--install-from-pypi-recommended)
   - [Option B — Install from GitHub](#option-b--install-from-github)
   - [Option C — Run with Docker](#option-c--run-with-docker-no-python-required)
7. [Step 5 — Configure AWS Credentials](#step-5--configure-aws-credentials)
8. [Step 6 — Verify the Installation](#step-6--verify-the-installation)
9. [Using the Commands](#using-the-commands)
   - [summary](#summary)
   - [daily](#daily)
   - [services](#services)
   - [regions](#regions)
   - [accounts](#accounts)
   - [tags](#tags)
   - [compare](#compare)
   - [forecast](#forecast)
   - [anomalies](#anomalies)
   - [budget](#budget)
   - [notify slack](#notify-slack)
   - [watch](#watch)
10. [Time Period Reference](#time-period-reference)
11. [Output Formats](#output-formats)
12. [Docker Reference](#docker-reference)
13. [IAM Permissions](#iam-permissions)
14. [Development Setup](#development-setup)

---

## What This Tool Does

`aws-cost-cli` connects to your AWS account and pulls cost data from the AWS Cost Explorer API, then displays it in clean, readable tables directly in your terminal. No browser needed.

You can break down your spend by service, region, account, or tag; compare periods side by side; set budgets; get forecasts; detect anomalies; and send cost reports to Slack — all from a single command.

---

## Before You Start

You will need:

- An AWS account (free to create)
- A computer running Windows, macOS, or Linux
- A terminal — Command Prompt, PowerShell, Git Bash, or Terminal

If you are going the Python route (Options A or B), you also need:

- Python 3.9 or higher installed on your machine
  - Check by running: `python --version`
  - Download from [python.org](https://python.org) if needed

If you are going the Docker route (Option C), you need:

- Docker Desktop installed and running
  - Download from [docker.com](https://docker.com)

---

## Step 1 — Create an AWS Account

> Skip this step if you already have an AWS account.

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click **Create a Free Account**
3. Enter your email address and choose an account name
4. Enter your credit card details (you will not be charged for free-tier usage)
5. Verify your phone number when prompted
6. Select the **Basic (Free)** support plan
7. Sign in to the **AWS Management Console**

---

## Step 2 — Enable Cost Explorer

Cost Explorer is the AWS service that this tool reads from. It is not enabled by default and needs to be turned on once.

1. Log in to the [AWS Console](https://console.aws.amazon.com)
2. In the search bar at the top, type **Cost Explorer** and click it
3. Click the **Enable Cost Explorer** button on the page
4. AWS will begin processing your historical cost data

> **Important:** After enabling, it can take up to **24 hours** for data to appear. If you run the tool before that window and get empty results, wait and try again the next day.

---

## Step 3 — Create an IAM User and Access Keys

Access keys allow the tool on your computer to authenticate with your AWS account without using your root password.

1. In the AWS Console, click on your **account name** in the top-right corner
2. Select **Security credentials** from the dropdown
3. Scroll down to the **Access keys** section
4. Click **Create access key**
5. On the use case screen, select **Command Line Interface (CLI)**
6. Check the confirmation checkbox and click **Next**
7. Click **Create access key**
8. You will now see two values. **Copy both immediately** — the secret will not be shown again:
   - **Access key ID** — example: `AKIAIOSFODNN7EXAMPLE`
   - **Secret access key** — example: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
9. Store these somewhere safe (a password manager is recommended)

> **Security note:** Never commit your access keys to GitHub or share them publicly. If you accidentally expose them, delete them immediately from the AWS console and create new ones.

---

## Step 4 — Install the Tool

There are three ways to install `aws-cost-cli`. Choose the one that works best for you.

---

### Option A — Install from PyPI (Recommended)

This is the simplest option. It installs the tool from the Python Package Index with a single command.

**Requirement:** Python 3.9+ installed

```bash
pip install aws-cost-cli
```

Verify the installation:

```bash
aws-cost --version
```

You should see the version number printed. You are ready to use the tool.

---

### Option B — Install from GitHub

Use this option if you want the latest development version or if you plan to modify the code.

**Step 1 — Clone the repository**

```bash
git clone https://github.com/Mide69/aws-cost-cli.git
```

This downloads the full project to a folder called `aws-cost-cli` in your current directory.

**Step 2 — Navigate into the folder**

```bash
cd aws-cost-cli
```

**Step 3 — Create a virtual environment**

A virtual environment keeps the project's dependencies isolated from the rest of your system.

```bash
python -m venv .venv
```

**Step 4 — Activate the virtual environment**

On macOS / Linux:
```bash
source .venv/bin/activate
```

On Windows (PowerShell):
```powershell
.venv\Scripts\activate
```

On Windows (Git Bash):
```bash
source .venv/Scripts/activate
```

When the virtual environment is active, you will see `(.venv)` at the beginning of your terminal prompt.

**Step 5 — Install the package**

```bash
pip install -e .
```

The `-e` flag installs the package in editable mode, meaning any changes you make to the source code take effect immediately without reinstalling.

**Step 6 — Verify the installation**

```bash
aws-cost --version
```

---

### Option C — Run with Docker (No Python Required)

Use this option if you do not want to install Python or manage dependencies. Docker Desktop must be installed and running.

**Step 1 — Pull the image from Docker Hub**

```bash
docker pull tektribe/aws-cost-cli:latest
```

This downloads the pre-built image. It is approximately 180MB.

**Step 2 — Run a test command**

```bash
docker run --rm tektribe/aws-cost-cli --help
```

You should see the help output listing all available commands. The tool is ready to use.

> Docker requires credentials to be passed in at runtime. See [Docker Reference](#docker-reference) for full usage instructions.

---

## Step 5 — Configure AWS Credentials

> Skip this step if you are using Docker — credentials are handled differently there. See [Docker Reference](#docker-reference).

**Install the AWS CLI** (if you do not already have it):

Download from the [official AWS CLI page](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and run the installer for your operating system.

Verify it installed:

```bash
aws --version
```

**Run the configuration command:**

```bash
aws configure
```

You will be asked four questions. Enter the values from Step 3:

```
AWS Access Key ID:      AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key:  wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name:    us-east-1
Default output format:  json
```

Press **Enter** after each one. This saves your credentials to `~/.aws/credentials` on your machine.

---

## Step 6 — Verify the Installation

Run the following command to confirm everything is connected:
aws 
```bash
aws-cost summary
```

If Cost Explorer is enabled and credentials are correct, you will see a table of your monthly cost totals. If you see an error, check the [Troubleshooting](#troubleshooting) section below.

---

## Using the Commands

All commands follow this structure:

```
aws-cost [global options] COMMAND [command options]
```

Global options (apply to every command):

| Option | Description | Default |
|---|---|---|
| `--profile TEXT` | Use a named AWS profile | default profile |
| `--region TEXT` | AWS region | `us-east-1` |
| `--format [table\|json\|csv]` | Output format | `table` |
| `--version` | Show version and exit | — |
| `--help` | Show help | — |

---

### summary

Shows your total monthly AWS spend for the last N months.

```bash
aws-cost summary
```

Example output:

```
╭─────────────────────────────────╮
│       Monthly Cost Summary      │
├───────────┬──────────┬──────────┤
│ Month     │ Total    │          │
├───────────┼──────────┼──────────┤
│ 2025-12   │ $12.34   │          │
│ 2026-01   │ $18.00   │          │
│ 2026-02   │ $9.50    │          │
│ 2026-03   │ $22.10   │ estimated│
╰───────────┴──────────┴──────────╯
```

**Options:**

```bash
# Show the last 12 months instead of 6
aws-cost summary --months 12

# Output as JSON
aws-cost --format json summary

# Output as CSV
aws-cost --format csv summary
```

---

### daily

Shows a day-by-day cost breakdown for a given period. Useful for spotting the exact day a cost spike happened.

```bash
aws-cost daily
```

**Options:**

```bash
# Last 7 days
aws-cost daily --period 7d

# A specific month
aws-cost daily --period 2026-03

# Custom date range
aws-cost daily --start 2026-05-01 --end 2026-05-15
```

---

### services

Shows how much each AWS service is costing you for a given period.

```bash
aws-cost services
```

Example output:

```
╭────────────────────────────────────────────────────╮
│         Cost by Service — May 2026                 │
├──────────────────────┬──────────┬───────────────── ┤
│ Service              │ Cost     │ % of Total       │
├──────────────────────┼──────────┼──────────────────┤
│ Amazon EC2           │ $45.20   │ 62.1%            │
│ Amazon RDS           │ $18.30   │ 25.1%            │
│ Amazon S3            │ $8.00    │ 11.0%            │
│ AWS Lambda           │ $0.90    │ 1.2%             │
├──────────────────────┼──────────┼──────────────────┤
│ Total                │ $72.80   │ 100%             │
╰──────────────────────┴──────────┴──────────────────╯
```

**Options:**

```bash
# Show only the top 5 most expensive services
aws-cost services --top 5

# Show last month's costs
aws-cost services --period last-month

# Compare this month vs last month (shows % change)
aws-cost services --compare

# Combined: last month, top 5, with comparison
aws-cost services --period last-month --top 5 --compare

# Custom date range
aws-cost services --start 2026-01-01 --end 2026-03-31
```

When using `--compare`, the output adds a column showing whether each service went up or down:

```
│ Amazon EC2    │ $45.20  │ 62.1%  │ ▲ +12.3%  │
│ Amazon S3     │ $8.00   │ 11.0%  │ ▼ -5.1%   │
│ AWS Lambda    │ $0.90   │ 1.2%   │ new       │
```

---

### regions

Shows which AWS regions your spend is coming from.

```bash
aws-cost regions
```

**Options:**

```bash
# Year to date, with comparison vs same period last year
aws-cost regions --period ytd --compare

# Top 3 most expensive regions this month
aws-cost regions --top 3
```

---

### accounts

Shows cost broken down by linked AWS account. This is useful if you manage multiple accounts under AWS Organizations.

```bash
aws-cost accounts
```

**Options:**

```bash
aws-cost accounts --period last-month --compare
aws-cost accounts --top 5
```

> If you have a single AWS account, this will show just one row — that is expected behaviour.

---

### tags

Shows cost broken down by a resource tag key. This requires your AWS resources to be tagged.

For example, if your team tags resources with `Environment = production` or `Environment = staging`, you can see the cost of each environment:

```bash
aws-cost tags --tag-key Environment
```

Output:

```
│ production  │ $210.00  │ 84.0%  │
│ staging     │ $35.00   │ 14.0%  │
│ (untagged)  │ $5.00    │ 2.0%   │
```

**Options:**

```bash
# Cost by team
aws-cost tags --tag-key Team

# Cost by project for last month
aws-cost tags --tag-key Project --period last-month

# Top 5 tag values
aws-cost tags --tag-key Environment --top 5
```

---

### compare

A standalone comparison command that shows the current period side by side with the previous equivalent period.

```bash
aws-cost compare
```

**Options:**

```bash
# Compare by service for last month vs the month before
aws-cost compare --period last-month --by SERVICE

# Compare by region for last 30 days vs the 30 days before that
aws-cost compare --period 30d --by REGION

# Compare by account
aws-cost compare --by LINKED_ACCOUNT
```

---

### forecast

Shows a projected cost for the remainder of the current month or year, based on your spending trend.

```bash
aws-cost forecast
```

Example output:

```
╭──────────────────────────────────────────╮
│              Cost Forecast               │
│                                          │
│  Period:    2026-05-27 → 2026-05-31      │
│  Forecast:  $24.50                       │
│  Range:     $20.10 – $28.90              │
╰──────────────────────────────────────────╯
```

The range shows the lower and upper confidence bounds from the AWS forecast model.

**Options:**

```bash
# Forecast the rest of this month (default)
aws-cost forecast

# Forecast the rest of this year
aws-cost forecast --period YEARLY
```

---

### anomalies

Detects unusual cost spikes using AWS Cost Anomaly Detection. This is useful for catching unexpected charges early.

```bash
aws-cost anomalies
```

**Options:**

```bash
# Look back 14 days, show anomalies above $5 impact
aws-cost anomalies --days 14 --threshold 5

# Look back 60 days, show everything above $1
aws-cost anomalies --days 60 --threshold 1
```

If no anomalies are found, the output will say: `No cost anomalies detected.`

---

### budget

The `budget` command has three sub-commands: `set`, `list`, and `status`.

Budgets are stored locally on your machine in `~/.aws-cost-cli/budgets.json`. The budget name is either `total` (for your overall monthly spend) or any AWS service name exactly as it appears in Cost Explorer.

**Set a budget:**

```bash
# Set a total monthly budget of $500
aws-cost budget set total 500

# Set a budget for a specific service
aws-cost budget set "Amazon EC2" 200
aws-cost budget set "Amazon S3" 50
aws-cost budget set "Amazon RDS" 100
```

**List all budgets:**

```bash
aws-cost budget list
```

Output:

```
╭──────────────────┬──────────────────╮
│ Name             │ Monthly Budget   │
├──────────────────┼──────────────────┤
│ total            │ $500.00          │
│ Amazon EC2       │ $200.00          │
│ Amazon S3        │ $50.00           │
╰──────────────────┴──────────────────╯
```

**Check status with progress bars:**

```bash
aws-cost budget status
```

Output:

```
total
  ████████████░░░░░░░░░░░░░░░░░░  42.3%
  Spent: $211.50  /  Budget: $500.00  /  Remaining: $288.50

Amazon EC2
  ████████████████████░░░░░░░░░░  67.8%
  Spent: $135.60  /  Budget: $200.00  /  Remaining: $64.40

Amazon S3
  ██████░░░░░░░░░░░░░░░░░░░░░░░░  22.0%
  Spent: $11.00   /  Budget: $50.00   /  Remaining: $39.00
```

The bar turns yellow at 75% usage and red at 90%.

**Delete a budget:**

```bash
aws-cost budget delete "Amazon S3"
```

---

### notify slack

Sends a cost summary to a Slack channel using an Incoming Webhook.

**Step 1 — Create a Slack Incoming Webhook:**

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. Name your app (e.g. `AWS Cost Bot`) and select your workspace
4. Click **Incoming Webhooks** in the left menu
5. Toggle **Activate Incoming Webhooks** to On
6. Click **Add New Webhook to Workspace**
7. Select the channel you want to post to and click **Allow**
8. Copy the **Webhook URL** — it looks like `https://hooks.slack.com/services/T.../B.../...`

**Step 2 — Send a report:**

```bash
# Pass the webhook URL directly
aws-cost notify slack --webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Or set it as an environment variable (recommended — keeps it out of your terminal history)
export AWS_COST_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
aws-cost notify slack

# Send last month's top 10 services
aws-cost notify slack --period last-month --top 10
```

---

### watch

Live-refreshes the cost by service view in your terminal, similar to how `htop` works for system resources.

```bash
aws-cost watch
```

**Options:**

```bash
# Refresh every 30 seconds instead of the default 60
aws-cost watch --interval 30

# Show only the top 5 services, refresh every 2 minutes
aws-cost watch --top 5 --interval 120
```

Press **Ctrl + C** to exit the watch mode.

---

## Time Period Reference

All commands that accept `--period` support the following values:

| Value | What it covers |
|---|---|
| `yesterday` | Previous calendar day only |
| `7d` | Last 7 days |
| `30d` | Last 30 days |
| `mtd` | Month to date — from the 1st of this month until today *(default)* |
| `last-month` | The full previous calendar month |
| `3m` | Last 3 months |
| `6m` | Last 6 months |
| `ytd` | Year to date — from January 1st until today |
| `2026-03` | A specific month in YYYY-MM format |
| `--start` / `--end` | Fully custom range in YYYY-MM-DD format |

**Examples:**

```bash
aws-cost services --period 7d
aws-cost services --period last-month
aws-cost services --period 2026-03
aws-cost services --start 2026-01-01 --end 2026-03-31
```

---

## Output Formats

Every command supports three output formats controlled by the global `--format` flag.

**Table (default)** — coloured, human-readable output in the terminal:

```bash
aws-cost services
```

**JSON** — machine-readable output, useful for scripting:

```bash
aws-cost --format json services
```

**CSV** — comma-separated values, useful for spreadsheets:

```bash
aws-cost --format csv services

# Save to a file
aws-cost --format csv services > services.csv
aws-cost --format csv services --period last-month > last-month.csv
```

---

## Docker Reference

Docker lets you run `aws-cost-cli` without installing Python or any dependencies.

**Pull the latest image:**

```bash
docker pull tektribe/aws-cost-cli:latest
```

**Run using environment variables (recommended for CI/CD):**

Set your credentials as environment variables in your shell first:

```bash
export AWS_ACCESS_KEY_ID=your-access-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-access-key
export AWS_DEFAULT_REGION=us-east-1
```

Then run any command by passing those variables into the container:

```bash
docker run --rm \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e AWS_DEFAULT_REGION \
  tektribe/aws-cost-cli services
```

**Run using your existing AWS credentials file:**

If you have already run `aws configure`, your credentials are saved at `~/.aws/`. You can mount that folder into the container:

```bash
docker run --rm \
  -v ~/.aws:/root/.aws:ro \
  tektribe/aws-cost-cli summary
```

**Run any command with Docker:**

```bash
# Services last month with comparison
docker run --rm -v ~/.aws:/root/.aws:ro \
  tektribe/aws-cost-cli services --period last-month --compare

# Forecast
docker run --rm -v ~/.aws:/root/.aws:ro \
  tektribe/aws-cost-cli forecast

# Export to CSV (pipe the output to a file on your machine)
docker run --rm -v ~/.aws:/root/.aws:ro \
  tektribe/aws-cost-cli --format csv services > services.csv
```

**Build the image yourself from source:**

```bash
git clone https://github.com/Mide69/aws-cost-cli.git
cd aws-cost-cli
docker build -t aws-cost-cli .
docker run --rm -v ~/.aws:/root/.aws:ro aws-cost-cli summary
```

---

## IAM Permissions

The tool requires the following IAM permissions. Attach this policy to the IAM user whose access keys you are using:

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

**How to attach this policy:**

1. Go to the [IAM console](https://console.aws.amazon.com/iam)
2. Click **Policies** → **Create policy**
3. Click **JSON** and paste the policy above
4. Click **Next**, give the policy a name (e.g. `CostExplorerReadOnly`), and click **Create policy**
5. Go to **Users**, click your user, click **Add permissions**
6. Choose **Attach policies directly**, search for `CostExplorerReadOnly`, and attach it

> AWS Cost Explorer charges approximately **$0.01 per API request**. Normal usage of this tool costs a few cents per month.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `NoCredentialsError` | AWS credentials not configured | Run `aws configure` |
| `AccessDeniedException` | IAM user missing permissions | Attach the policy from the [IAM Permissions](#iam-permissions) section |
| Empty results / no data | Cost Explorer not yet enabled | Wait 24 hours after enabling Cost Explorer |
| `aws-cost: command not found` | Virtual environment not active | Run `source .venv/Scripts/activate` (or `source .venv/bin/activate` on Mac/Linux) |
| `No remaining days in forecast` | Running forecast on the last day of the month | Expected — there are no more days left to forecast |

---

## Development Setup

To set up a local development environment:

```bash
# Clone the repo
git clone https://github.com/Mide69/aws-cost-cli.git
cd aws-cost-cli

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
source .venv/Scripts/activate    # Windows Git Bash
.venv\Scripts\activate           # Windows PowerShell

# Install with development dependencies
pip install -e ".[dev]"

# Run the test suite
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=aws_cost_cli --cov-report=term-missing
```

**Project structure:**

```
aws_cost_cli/
├── cli.py            Click commands and option routing
├── cost_explorer.py  AWS Cost Explorer API calls (boto3)
├── formatter.py      Rich terminal tables and CSV export
├── periods.py        Time period resolution (7d, mtd, last-month…)
├── budget.py         Local budget storage (~/.aws-cost-cli/)
└── notify.py         Slack webhook notifications

tests/
├── test_cost_explorer.py   API layer tests (mocked)
├── test_periods.py         Period resolver tests
└── test_budget.py          Budget CRUD tests
```

---

## License

MIT

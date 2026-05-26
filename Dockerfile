FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY aws_cost_cli/ aws_cost_cli/

RUN pip install --no-cache-dir .

ENTRYPOINT ["aws-cost"]
CMD ["--help"]

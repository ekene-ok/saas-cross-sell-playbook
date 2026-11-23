#!/usr/bin/env bash
# Download the IBM Telco Customer Churn sample dataset (Apache 2.0) into data/raw/.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw
curl -sSL -o data/raw/telco_customer_churn.csv \
  https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv
echo "Data ready in data/raw/"

#!/bin/bash
#
# Import Grafana dashboards
#
# Usage: ./tools/import_dashboards.sh [grafana_url] [username] [password]
#

set -e

GRAFANA_URL="${1:-http://localhost:3000}"
GRAFANA_USER="${2:-admin}"
GRAFANA_PASS="${3:-admin}"

DASHBOARD_DIR="$(dirname "$0")/../infra/prometheus/grafana-dashboards"

echo "Importing Grafana dashboards to ${GRAFANA_URL}..."

# Check if Grafana is accessible
if ! curl -s -f "${GRAFANA_URL}/api/health" > /dev/null; then
    echo "Error: Grafana not accessible at ${GRAFANA_URL}"
    exit 1
fi

# Import each dashboard
for dashboard in "${DASHBOARD_DIR}"/*.json; do
    if [ -f "$dashboard" ]; then
        filename=$(basename "$dashboard")
        echo "Importing ${filename}..."

        # Wrap dashboard JSON in required format
        payload=$(cat "$dashboard" | jq '{dashboard: .dashboard, overwrite: true, inputs: [], folderId: 0}')

        response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
            -d "$payload" \
            "${GRAFANA_URL}/api/dashboards/db")

        # Check if import was successful
        if echo "$response" | jq -e '.status == "success"' > /dev/null 2>&1; then
            echo "  ✓ Successfully imported ${filename}"
            dashboard_url=$(echo "$response" | jq -r '.url')
            echo "    URL: ${GRAFANA_URL}${dashboard_url}"
        else
            echo "  ✗ Failed to import ${filename}"
            echo "    Response: $response"
        fi
    fi
done

echo ""
echo "Dashboard import complete!"
echo "Access Grafana at: ${GRAFANA_URL}"

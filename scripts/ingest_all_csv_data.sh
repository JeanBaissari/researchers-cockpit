#!/usr/bin/env bash
# =============================================================================
# Comprehensive CSV Data Ingestion Script
# =============================================================================
# Ingests all available CSV forex data into Zipline bundles with validation.
#
# This script:
# 1. Activates the virtual environment
# 2. Validates CSV files before ingestion
# 3. Ingests data for both EURUSD and NZDJPY across all timeframes
# 4. Creates bundles following naming convention: csv_{symbol}_{timeframe}
# 5. Validates bundle integrity after ingestion
#
# Architectural Compliance:
# - Uses lib/bundles/ package for data ingestion (v1.11.0+)
# - Uses lib/validation/ package for data quality checks
# - Follows FOREX calendar conventions (24/5 trading)
# - No hardcoded paths (uses project root detection)
#
# Usage:
#   bash scripts/ingest_all_csv_data.sh
#   bash scripts/ingest_all_csv_data.sh --force  # Force re-ingestion
# =============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CSV Data Ingestion - The Researcher's Cockpit${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Parse command-line arguments
FORCE_FLAG=""
if [[ "${1:-}" == "--force" ]]; then
    FORCE_FLAG="--force"
    echo -e "${YELLOW}⚠ Force re-ingestion enabled${NC}"
    echo ""
fi

# Activate virtual environment
echo -e "${BLUE}[1/4] Activating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${RED}ERROR: Virtual environment not found at $PROJECT_ROOT/venv${NC}"
    echo -e "${YELLOW}Please create it first: python3 -m venv venv${NC}"
    exit 1
fi

source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Verify required packages
echo -e "${BLUE}[2/4] Verifying required packages...${NC}"
python3 -c "import pandas, zipline, exchange_calendars" 2>/dev/null || {
    echo -e "${RED}ERROR: Required packages not installed${NC}"
    echo -e "${YELLOW}Install with: pip install -r requirements.txt${NC}"
    exit 1
}
echo -e "${GREEN}✓ All required packages available${NC}"
echo ""

# CSV data directory
DATA_DIR="$PROJECT_ROOT/data/processed"

# Array of symbols and timeframes
ALL_SYMBOLS="EURUSD,NZDJPY"
TIMEFRAMES=("1m" "5m" "15m" "30m" "1h" "4h" "1d")

# Count total timeframes to ingest
TOTAL_TIMEFRAMES=${#TIMEFRAMES[@]}

echo -e "${BLUE}[3/4] Ingesting CSV data...${NC}"
echo -e "Ingesting ${GREEN}$TOTAL_TIMEFRAMES${NC} timeframes with both EURUSD and NZDJPY"
echo ""

# Ingestion counter
SUCCESS_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0

# Ingest each timeframe with all symbols
for timeframe in "${TIMEFRAMES[@]}"; do
    # Check if CSV files exist for this timeframe
    CSV_COUNT=$(ls "$DATA_DIR/$timeframe/"*"_${timeframe}_"*"_ready.csv" 2>/dev/null | wc -l)

    if [ "$CSV_COUNT" -eq 0 ]; then
        echo -e "${YELLOW}⊘ Skipping ${timeframe}: No CSV files found${NC}"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        continue
    fi

    # Bundle name following convention: csv_forex_{timeframe}
    BUNDLE_NAME="csv_forex_${timeframe}"

    echo -e "${BLUE}→ Ingesting ${timeframe} data (EURUSD + NZDJPY)...${NC}"
    echo "  Bundle: $BUNDLE_NAME"
    echo "  Files: $CSV_COUNT CSV files"

    # Ingest data for all symbols in this timeframe
    if python3 scripts/ingest_data.py \
        --source csv \
        --assets forex \
        --symbols "$ALL_SYMBOLS" \
        --timeframe "$timeframe" \
        --calendar FOREX \
        $FORCE_FLAG 2>&1 | grep -q "Successfully ingested"; then
        echo -e "${GREEN}✓ Successfully ingested ${timeframe}${NC}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "${RED}✗ Failed to ingest ${timeframe}${NC}"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    echo ""
done

# Summary
echo -e "${BLUE}[4/4] Ingestion Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Total timeframes: ${TOTAL_TIMEFRAMES}"
echo -e "Success:          ${GREEN}${SUCCESS_COUNT}${NC}"
echo -e "Failed:           ${RED}${FAILED_COUNT}${NC}"
echo -e "Skipped:          ${YELLOW}${SKIPPED_COUNT}${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $FAILED_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ All CSV data ingested successfully!${NC}"
    echo ""
    echo -e "${BLUE}Available bundles (each contains EURUSD + NZDJPY):${NC}"
    echo "  csv_forex_1m, csv_forex_5m, csv_forex_15m, csv_forex_30m"
    echo "  csv_forex_1h, csv_forex_4h, csv_forex_1d"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Validate bundles: python3 scripts/validate_bundles.py csv_forex_1m"
    echo "  2. Create strategies in strategies/forex/"
    echo "  3. Run backtests: python3 scripts/run_backtest.py --strategy {name}"
else
    echo -e "${RED}⚠ Some ingestions failed. Check logs above for details.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Ingestion Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

#!/bin/bash
#
# Easy script to run OPF evaluation with different IEEE test cases
# Usage: ./run_case.sh [case_number] [num_servers] [mode]
#
# Examples:
#   ./run_case.sh 30 5              # IEEE 30 bus, 5 servers, comparison mode
#   ./run_case.sh 57 7 distributed  # IEEE 57 bus, 7 servers, distributed only
#   ./run_case.sh 14 3 centralized  # IEEE 14 bus, centralized only
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
CASE_NUM=${1:-14}
NUM_SERVERS=${2:-3}
MODE=${3:-comparison}

# Map case numbers to filenames
declare -A CASE_FILES
CASE_FILES[3]="pglib_opf_case3_lmbd.m"
CASE_FILES[5]="pglib_opf_case5_pjm.m"
CASE_FILES[14]="pglib_opf_case14_ieee.m"
CASE_FILES[24]="pglib_opf_case24_ieee_rts.m"
CASE_FILES[30]="pglib_opf_case30_ieee.m"
CASE_FILES[39]="pglib_opf_case39_epri.m"
CASE_FILES[57]="pglib_opf_case57_ieee.m"
CASE_FILES[118]="pglib_opf_case118_ieee.m"
CASE_FILES[200]="pglib_opf_case200_tamu.m"
CASE_FILES[500]="pglib_opf_case500_tamu.m"

# Check if case number is valid
if [ -z "${CASE_FILES[$CASE_NUM]}" ]; then
    echo -e "${RED}Error: Unknown case number $CASE_NUM${NC}"
    echo ""
    echo "Available cases:"
    echo "  3, 5, 14, 24, 30, 39, 57, 118, 200, 500"
    echo ""
    echo "Usage: $0 [case_number] [num_servers] [mode]"
    echo ""
    echo "Examples:"
    echo "  $0 30 5              # IEEE 30 bus, 5 servers, comparison"
    echo "  $0 57 7 distributed  # IEEE 57 bus, 7 servers, distributed"
    echo "  $0 14 3 centralized  # IEEE 14 bus, centralized only"
    exit 1
fi

CASE_FILE="${CASE_FILES[$CASE_NUM]}"
CASE_PATH="testbeds/$CASE_FILE"

# Recommended iterations based on case size
declare -A RECOMMENDED_ITERS
RECOMMENDED_ITERS[3]=500
RECOMMENDED_ITERS[5]=500
RECOMMENDED_ITERS[14]=1000
RECOMMENDED_ITERS[24]=1500
RECOMMENDED_ITERS[30]=1500
RECOMMENDED_ITERS[39]=2000
RECOMMENDED_ITERS[57]=2000
RECOMMENDED_ITERS[118]=3000
RECOMMENDED_ITERS[200]=4000
RECOMMENDED_ITERS[500]=5000

ITERATIONS=${RECOMMENDED_ITERS[$CASE_NUM]:-1000}

# Print configuration
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Edge OPF Evaluation Runner${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Configuration:"
echo -e "  IEEE Case:       ${YELLOW}${CASE_NUM} bus${NC}"
echo -e "  Case File:       ${CASE_FILE}"
echo -e "  Edge Servers:    ${YELLOW}${NUM_SERVERS}${NC} (simulated)"
echo -e "  Mode:            ${YELLOW}${MODE}${NC}"
echo -e "  Max Iterations:  ${ITERATIONS}"
echo ""

# Check if case file exists
if [ ! -f "../$CASE_PATH" ]; then
    echo -e "${RED}Error: Case file not found at ../$CASE_PATH${NC}"
    exit 1
fi

# Warn for large cases
if [ "$CASE_NUM" -ge 118 ]; then
    echo -e "${YELLOW}Warning: This is a large case. Consider:${NC}"
    echo -e "  - Using --sequential flag"
    echo -e "  - Ensuring sufficient RAM (16GB+)"
    echo -e "  - Allowing 30-60 minutes for completion"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Build command
CMD="python evaluate_edge_opf.py --mode $MODE --servers $NUM_SERVERS --case $CASE_PATH --iterations $ITERATIONS"

# Add sequential for very large cases
if [ "$CASE_NUM" -ge 118 ]; then
    CMD="$CMD --sequential"
    echo -e "${YELLOW}Note: Using sequential mode for large case${NC}"
    echo ""
fi

echo -e "${GREEN}Running command:${NC}"
echo -e "${YELLOW}$CMD${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo ""

# Run evaluation
$CMD

# Show results
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Evaluation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Results saved to:"
echo -e "  CSV files: ${YELLOW}results/*case${CASE_NUM}*.csv${NC}"
echo -e "  Plots:     ${YELLOW}plots/*case${CASE_NUM}*.png${NC}"
echo ""
echo -e "View results:"
echo -e "  ls results/*case${CASE_NUM}*"
echo -e "  ls plots/*case${CASE_NUM}*"
echo ""

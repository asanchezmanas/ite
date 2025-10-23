

#!/bin/bash

# Script para ejecutar tests con diferentes configuraciones

echo "🧪 Territory Conquest - Test Suite"
echo "=================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para ejecutar tests
run_tests() {
    local test_type=$1
    local args=$2
    
    echo -e "${BLUE}Running ${test_type} tests...${NC}"
    pytest $args
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${test_type} tests passed${NC}"
    else
        echo -e "${YELLOW}✗ ${test_type} tests failed${NC}"
        exit 1
    fi
    echo ""
}

# Parse argumentos
case "$1" in
    "unit")
        echo "Running UNIT tests only..."
        run_tests "Unit" "-m unit"
        ;;
    
    "integration")
        echo "Running INTEGRATION tests only..."
        run_tests "Integration" "-m integration"
        ;;
    
    "risk")
        echo "Running RISK system tests only..."
        run_tests "RISK" "-m risk"
        ;;
    
    "auth")
        echo "Running AUTH tests only..."
        run_tests "Auth" "tests/test_auth.py"
        ;;
    
    "activities")
        echo "Running ACTIVITIES tests only..."
        run_tests "Activities" "tests/test_activities.py"
        ;;
    
    "teams")
        echo "Running TEAMS tests only..."
        run_tests "Teams" "tests/test_teams.py"
        ;;
    
    "fast")
        echo "Running FAST tests (excluding slow)..."
        run_tests "Fast" "-m 'not slow'"
        ;;
    
    "coverage")
        echo "Running tests with COVERAGE report..."
        pytest --cov=app --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    
    "verbose")
        echo "Running ALL tests with VERBOSE output..."
        run_tests "All (Verbose)" "-vv"
        ;;
    
    "")
        echo "Running ALL tests..."
        run_tests "All" ""
        ;;
    
    *)
        echo "Usage: ./run_tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  (none)        Run all tests"
        echo "  unit          Run only unit tests"
        echo "  integration   Run only integration tests"
        echo "  risk          Run only RISK system tests"
        echo "  auth          Run only authentication tests"
        echo "  activities    Run only activities tests"
        echo "  teams         Run only teams tests"
        echo "  fast          Run fast tests (exclude slow)"
        echo "  coverage      Run with coverage report"
        echo "  verbose       Run with verbose output"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}=================================="
echo "✓ Test suite completed successfully"
echo -e "==================================${NC}"

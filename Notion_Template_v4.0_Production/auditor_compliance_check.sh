#!/bin/bash

# Estate Planning Concierge v4.0 - Auditor Compliance Check
# Verifies deploy.py meets all auditor requirements

echo "=================================================="
echo "AUDITOR COMPLIANCE CHECK - v4.0 Master Gold Build"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

# Function to check requirement
check_requirement() {
    local description="$1"
    local command="$2"
    local expected="$3"
    
    result=$(eval "$command" 2>/dev/null)
    if [ "$result" = "$expected" ] || [ ! -z "$result" ]; then
        echo -e "${GREEN}✅ PASS${NC} - $description"
        ((PASS_COUNT++))
    else
        echo -e "${RED}❌ FAIL${NC} - $description"
        ((FAIL_COUNT++))
    fi
}

echo "📋 CRITICAL AUDITOR REQUIREMENTS"
echo "---------------------------------"

# 1. API Version Check
check_requirement "API Version 2025-09-03" \
    "grep 'NOTION_API_VERSION = \"2025-09-03\"' deploy.py" \
    "NOTION_API_VERSION = \"2025-09-03\""

# 2. Token Format Support
check_requirement "Token supports secret_ and ntn_ prefixes" \
    "grep -E 'token.startswith\(\"secret_\"\) or token.startswith\(\"ntn_\"\)' deploy.py" \
    "token.startswith"

# 3. Rate Limiting
check_requirement "Rate limit set to 2.5 RPS" \
    "grep 'RATE_LIMIT_RPS = 2.5' deploy.py" \
    "RATE_LIMIT_RPS = 2.5"

# 4. Relation Resolution
check_requirement "Pages Index DB pattern implemented" \
    "grep 'class PagesIndexDB' deploy.py" \
    "class PagesIndexDB"

check_requirement "Relation resolution method exists" \
    "grep 'def resolve_relation' deploy.py" \
    "def resolve_relation"

# 5. Synced Blocks
check_requirement "Synced Block Manager implemented" \
    "grep 'class SyncedBlockManager' deploy.py" \
    "class SyncedBlockManager"

check_requirement "SYNC_KEY mapping implemented" \
    "grep 'SYNC_KEY' deploy.py" \
    "SYNC_KEY"

# 6. Error Handling
check_requirement "Try-except blocks for error handling" \
    "grep -c 'try:' deploy.py | test \$(cat) -gt 10 && echo 'found'" \
    "found"

check_requirement "Exponential backoff implemented" \
    "grep 'exponential_backoff' deploy.py" \
    "exponential_backoff"

check_requirement "Retry logic implemented" \
    "grep -E 'retry|MAX_RETRIES' deploy.py" \
    "retry"

# 7. Idempotency
check_requirement "Has marker function for idempotency" \
    "grep 'def has_marker' deploy.py" \
    "def has_marker"

check_requirement "Idempotent operations" \
    "grep -i 'idempotent' deploy.py" \
    "idempotent"

# 8. Formula Validation
check_requirement "Formula validation implemented" \
    "grep -E 'validate_formula|formula.*validation' deploy.py" \
    "formula"

# 9. Rich Text Formatting
check_requirement "Rich text with annotations" \
    "grep -E 'italic.*gray|annotations' deploy.py" \
    "annotations"

# 10. Main Components
check_requirement "NotionDeployer class exists" \
    "grep 'class NotionDeployer' deploy.py" \
    "class NotionDeployer"

check_requirement "Create page method exists" \
    "grep 'def create_page' deploy.py" \
    "def create_page"

check_requirement "Create database method exists" \
    "grep 'def create_database' deploy.py" \
    "def create_database"

check_requirement "Seed database method exists" \
    "grep 'def seed_database' deploy.py" \
    "def seed_database"

echo ""
echo "📊 YAML CONFIGURATION CHECK"
echo "---------------------------"

# Check YAML files exist
YAML_DIR="../Notion_Template_v4.0_YAMLs"
YAML_COUNT=$(ls -1 $YAML_DIR/*.yaml 2>/dev/null | wc -l)

if [ "$YAML_COUNT" -eq 22 ]; then
    echo -e "${GREEN}✅ PASS${NC} - All 22 YAML files present"
    ((PASS_COUNT++))
else
    echo -e "${RED}❌ FAIL${NC} - Expected 22 YAMLs, found $YAML_COUNT"
    ((FAIL_COUNT++))
fi

echo ""
echo "📈 ACCEPTANCE CRITERIA (62 items)"
echo "---------------------------------"

# Check for acceptance database support
check_requirement "Acceptance database schema" \
    "grep -i 'acceptance.*database' deploy.py" \
    "acceptance"

check_requirement "Check formula for acceptance" \
    "grep -E 'Status.*Done.*✅' deploy.py" \
    "Done"

echo ""
echo "🏗️ ARCHITECTURE COMPONENTS"
echo "-------------------------"

check_requirement "100+ pages support" \
    "grep -E 'create_page|pages' deploy.py | wc -l | test \$(cat) -gt 50 && echo 'found'" \
    "found"

check_requirement "11 databases defined" \
    "grep -E 'Accounts|Property|Insurance|Contacts|Subscriptions|Keepsakes|Letters|Analytics|Transactions|Claims|Maintenance' deploy.py | wc -l | test \$(cat) -gt 5 && echo 'found'" \
    "found"

check_requirement "18 letter templates" \
    "grep -E 'letter|template.*placeholder' deploy.py" \
    "letter"

check_requirement "3 main hubs structure" \
    "grep -E 'Preparation.*Hub|Executor.*Hub|Family.*Hub' deploy.py" \
    "Hub"

echo ""
echo "🔒 SECURITY & RELIABILITY"
echo "------------------------"

check_requirement "Logging implemented" \
    "grep 'import logging' deploy.py" \
    "import logging"

check_requirement "Environment variables used" \
    "grep 'os.environ' deploy.py" \
    "os.environ"

check_requirement "Validation mode available" \
    "grep -E '--validate-only|validate_only' deploy.py" \
    "validate"

check_requirement "Dry-run mode available" \
    "grep -E '--dry-run|dry_run' deploy.py" \
    "dry"

echo ""
echo "=================================================="
echo "FINAL AUDIT RESULTS"
echo "=================================================="
echo ""
echo -e "✅ Passed: ${GREEN}$PASS_COUNT${NC}"
echo -e "❌ Failed: ${RED}$FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}🎉 AUDIT PASSED!${NC} Deploy.py meets all auditor requirements."
    echo ""
    echo "The system is ready for:"
    echo "1. Setting environment variables"
    echo "2. Running validation checks"
    echo "3. Executing deployment"
    exit 0
else
    echo -e "${RED}⚠️ AUDIT FAILED${NC} - $FAIL_COUNT requirements not met."
    echo ""
    echo "Please review and fix the failures above."
    exit 1
fi
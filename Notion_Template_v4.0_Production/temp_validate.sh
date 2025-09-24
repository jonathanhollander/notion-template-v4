#!/bin/bash
# File: validate_complete_implementation.sh
# Source: COMPLETE_TECHNICAL_IMPLEMENTATION_PLAN.md lines 2178-2230
# Purpose: Validate all 29 enhanced systems implementation

echo "=== COMPREHENSIVE VALIDATION SCRIPT ==="
echo "Validating all 29 enhanced systems"

# Phase 1: YAML Syntax Validation
echo ""
echo "Phase 1: YAML Syntax Validation"
echo "--------------------------------"
for file in split_yaml/*.yaml; do
    echo -n "Validating $(basename $file)... "
    python3 -c "import yaml; yaml.safe_load(open('$file', 'r'))" 2>/dev/null && echo "✅ OK" || echo "❌ SYNTAX ERROR"
done

# Phase 2: Deployment Test
echo ""
echo "Phase 2: Deployment Test (Dry Run)"
echo "-----------------------------------"
if [ -f "deploy.py" ]; then
    echo "Running deployment dry run..."
    python3 deploy.py --dry-run --verbose 2>&1 | tail -5
else
    echo "❌ deploy.py not found"
fi

# Phase 3: Content Verification
echo ""
echo "Phase 3: Content Verification"
echo "-----------------------------"
echo -n "Checking for toggle systems... "
grep -r "toggle" split_yaml/ >/dev/null 2>&1 && echo "✅ Found" || echo "❌ Missing"

echo -n "Checking for accordion content... "
grep -r "accordion" split_yaml/ >/dev/null 2>&1 && echo "✅ Found" || echo "❌ Missing"

echo -n "Checking for database formulas... "
grep -r "formula" split_yaml/ >/dev/null 2>&1 && echo "✅ Found" || echo "❌ Missing"

echo -n "Checking for progress tracking... "
grep -r "progress" split_yaml/ >/dev/null 2>&1 && echo "✅ Found" || echo "❌ Missing"

# Phase 4: System Count Verification
echo ""
echo "Phase 4: System Count Verification"
echo "----------------------------------"
interactive_systems=$(grep -r -c "type.*toggle\|accordion" split_yaml/ 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
echo "Interactive systems found: $interactive_systems (target: 15)"

guidance_systems=$(grep -r -c "contextual_help\|help_text\|guidance" split_yaml/ 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
echo "Guidance systems found: $guidance_systems (target: 12)"

database_systems=$(grep -r -c "formula\|rollup" split_yaml/ 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
echo "Database systems found: $database_systems (target: 8)"

dashboard_files=0
[ -f "split_yaml/26_progress_visualizations.yaml" ] && ((dashboard_files++))
[ -f "split_yaml/28_analytics_dashboard.yaml" ] && ((dashboard_files++))
echo "Dashboard systems found: $dashboard_files (target: 2)"

# Phase 5: Legacy Recovery Check
echo ""
echo "Phase 5: Legacy Recovery Files"
echo "------------------------------"
echo -n "Checking legacy deploy.py... "
[ -f "../unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/deploy.py" ] && echo "✅ Available" || echo "❌ Missing"

echo -n "Checking synced_rollups.py... "
[ -f "../unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/synced_rollups.py" ] && echo "✅ Available" || echo "❌ Missing"

echo -n "Checking progress_dashboard.py... "
[ -f "../unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/progress_dashboard.py" ] && echo "✅ Available" || echo "❌ Missing"

# Final Summary
echo ""
echo "==================================="
total_enhanced=$((interactive_systems + guidance_systems + database_systems + dashboard_files))
echo "Total enhanced systems: $total_enhanced (target: 37+)"

if [ $total_enhanced -ge 37 ]; then
    echo "✅ COMPREHENSIVE VALIDATION PASSED"
else
    echo "❌ VALIDATION INCOMPLETE - Review implementation"
fi
echo "==================================="
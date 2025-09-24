#!/bin/bash

# Advanced Dashboard and Visualization Systems Analysis Script
# Comprehensive extraction of dashboard, visualization, and tracking systems

BASE_DIR="/Users/jonathanhollander/AI Code/Notion Template"
OUTPUT_FILE="DASHBOARD_SYSTEMS_ANALYSIS.md"

echo "# Advanced Dashboard and Visualization Systems Analysis" > "$OUTPUT_FILE"
echo "Date: $(date)" >> "$OUTPUT_FILE"
echo "Search Location: $BASE_DIR" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Function to add detailed analysis with full context
add_detailed_analysis() {
    local file="$1"
    local analysis_type="$2"
    local pattern="$3"

    echo "## $analysis_type SYSTEM FOUND" >> "$OUTPUT_FILE"
    echo "**FILE:** $file" >> "$OUTPUT_FILE"
    echo "**ANALYSIS TYPE:** $analysis_type" >> "$OUTPUT_FILE"
    echo "**PATTERN:** \"$pattern\"" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    # Get file info
    echo "**FILE SIZE:** $(wc -c < "$file" 2>/dev/null || echo 'N/A') bytes" >> "$OUTPUT_FILE"
    echo "**LINE COUNT:** $(wc -l < "$file" 2>/dev/null || echo 'N/A') lines" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    # Extract relevant sections with more context
    echo "**RELEVANT CODE SECTIONS:**" >> "$OUTPUT_FILE"
    echo "\`\`\`" >> "$OUTPUT_FILE"

    if [[ "$pattern" != "FULL_FILE" ]]; then
        grep -n -i -B3 -A10 "$pattern" "$file" 2>/dev/null | head -50 >> "$OUTPUT_FILE"
    else
        # For critical files, show first 100 lines
        head -100 "$file" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "[... FILE CONTINUES ...]" >> "$OUTPUT_FILE"
    fi

    echo "\`\`\`" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    # Extract class and function definitions
    echo "**KEY FUNCTIONS/CLASSES:**" >> "$OUTPUT_FILE"
    echo "\`\`\`" >> "$OUTPUT_FILE"
    grep -n "^class\|^def\|^async def" "$file" 2>/dev/null >> "$OUTPUT_FILE"
    echo "\`\`\`" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
}

echo "=== PHASE 1: Critical Dashboard Files Analysis ==="

# Critical dashboard files found in discovery
CRITICAL_DASHBOARD_FILES=(
    "unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/progress_dashboard.py"
    "unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/synced_rollups.py"
    "Notion_Template_v4.0_Production/asset_generation/review_dashboard.py"
    "Notion_Template_v4.0_Production/asset_generation/websocket_broadcaster.py"
)

for file in "${CRITICAL_DASHBOARD_FILES[@]}"; do
    full_path="$BASE_DIR/$file"
    if [[ -f "$full_path" ]]; then
        echo "Analyzing critical dashboard file: $file"
        add_detailed_analysis "$full_path" "CRITICAL_DASHBOARD" "FULL_FILE"
    fi
done

echo "=== PHASE 2: Dashboard Pattern Search ==="

# Dashboard and visualization patterns
DASHBOARD_PATTERNS=(
    "dashboard" "progress.*bar" "visualization" "gauge" "chart" "metric"
    "burndown" "analytics" "grid.*view" "status.*indicator" "timeline"
    "milestone" "tracker" "monitor" "widget" "panel" "component"
    "progress.*visual" "ascii.*chart" "bar.*chart" "pie.*chart"
    "data.*viz" "graph" "plot" "diagram" "report" "summary.*view"
)

for pattern in "${DASHBOARD_PATTERNS[@]}"; do
    echo "Searching for dashboard pattern: $pattern"

    find "$BASE_DIR" \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.js" -o -name "*.html" \) -type f | while read file; do
        if grep -l -i "$pattern" "$file" 2>/dev/null; then
            add_detailed_analysis "$file" "DASHBOARD_PATTERN" "$pattern"
        fi
    done
done

echo "=== PHASE 3: Tracking and Status Systems ==="

# Database and tracking patterns
DATABASE_PATTERNS=(
    "rollup" "formula" "relation" "database.*property" "select.*option"
    "checkbox.*status" "number.*property" "date.*range" "multi.*select"
    "status.*tracking" "completion.*rate" "progress.*calculation"
    "aggregate" "count" "sum" "average" "filter.*view" "sort.*property"
    "dependency.*tracking" "workflow.*status" "task.*completion"
)

for pattern in "${DATABASE_PATTERNS[@]}"; do
    echo "Searching for database pattern: $pattern"

    find "$BASE_DIR" \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" \) -type f | while read file; do
        if grep -l -i "$pattern" "$file" 2>/dev/null; then
            add_detailed_analysis "$file" "DATABASE_TRACKING" "$pattern"
        fi
    done
done

echo "=== PHASE 4: Visualization Components ==="

# Visual component patterns
VISUAL_PATTERNS=(
    "emoji.*progress" "visual.*element" "icon.*indicator" "color.*coding"
    "block.*visual" "callout.*status" "toggle.*expand" "accordion"
    "collapsible" "expandable" "show.*hide" "reveal.*content"
    "progress.*emoji" "status.*emoji" "completion.*visual"
    "bar.*emoji" "chart.*emoji" "graph.*visual" "indicator.*visual"
)

for pattern in "${VISUAL_PATTERNS[@]}"; do
    echo "Searching for visual pattern: $pattern"

    find "$BASE_DIR" \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.js" -o -name "*.html" \) -type f | while read file; do
        if grep -l -i "$pattern" "$file" 2>/dev/null; then
            add_detailed_analysis "$file" "VISUAL_COMPONENT" "$pattern"
        fi
    done
done

echo "=== PHASE 5: Summary Generation ==="

echo "# Summary Analysis" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Count findings by type
dashboard_count=$(grep -c "CRITICAL_DASHBOARD" "$OUTPUT_FILE")
pattern_count=$(grep -c "DASHBOARD_PATTERN" "$OUTPUT_FILE")
tracking_count=$(grep -c "DATABASE_TRACKING" "$OUTPUT_FILE")
visual_count=$(grep -c "VISUAL_COMPONENT" "$OUTPUT_FILE")

echo "## Dashboard Systems Found" >> "$OUTPUT_FILE"
echo "- **Critical Dashboard Files:** $dashboard_count" >> "$OUTPUT_FILE"
echo "- **Dashboard Pattern Matches:** $pattern_count" >> "$OUTPUT_FILE"
echo "- **Database Tracking Systems:** $tracking_count" >> "$OUTPUT_FILE"
echo "- **Visual Components:** $visual_count" >> "$OUTPUT_FILE"
echo "- **Total Systems Found:** $((dashboard_count + pattern_count + tracking_count + visual_count))" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Generate file statistics
echo "## Files with Most Dashboard Content" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
grep "**FILE:**" "$OUTPUT_FILE" | sort | uniq -c | sort -nr | head -20 >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "## Critical Findings Summary" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "### Most Advanced Dashboard Systems:" >> "$OUTPUT_FILE"

# Extract key insights from critical files
if [[ -f "$BASE_DIR/unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/progress_dashboard.py" ]]; then
    echo "1. **Progress Dashboard Manager** - Comprehensive progress tracking with visual indicators" >> "$OUTPUT_FILE"
    grep -n "class\|def " "$BASE_DIR/unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/progress_dashboard.py" | head -10 >> "$OUTPUT_FILE"
fi

if [[ -f "$BASE_DIR/unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/synced_rollups.py" ]]; then
    echo "2. **Synced Rollup Manager** - Cross-database synchronization system" >> "$OUTPUT_FILE"
    grep -n "class\|def " "$BASE_DIR/unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/synced_rollups.py" | head -10 >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"
echo "- **Analysis Completed:** $(date)" >> "$OUTPUT_FILE"

echo "=== DASHBOARD SYSTEMS ANALYSIS COMPLETE ==="
echo "Results saved to: $OUTPUT_FILE"
echo "Found $(grep -c "SYSTEM FOUND" "$OUTPUT_FILE") total dashboard systems"
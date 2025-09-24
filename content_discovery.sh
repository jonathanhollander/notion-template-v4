#!/bin/bash

# Comprehensive Content Discovery Script
BASE_DIR="/Users/jonathanhollander/AI Code/Notion Template"
OUTPUT_FILE="COMPREHENSIVE_CONTENT_DISCOVERY_RESULTS.md"

echo "# Comprehensive Content Discovery Results" > "$OUTPUT_FILE"
echo "Date: $(date)" >> "$OUTPUT_FILE"
echo "Search Location: $BASE_DIR" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

echo "=== Starting Content Discovery ==="

# Phase 1: Search for all content patterns
echo "# Pattern Search Results" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Define search patterns
PATTERNS=(
    "database" "formulae" "formula" "tracking" "status" "completion" "station"
    "rollup" "relation" "select" "checkbox" "progress" "metrics" "properties"
    "emotional intelligence" "EQ" "empathy" "compassion" "grief" "bereavement"
    "emotional support" "sensitivity" "comfort" "care" "understanding" "loss"
    "gentle" "supportive" "kindness" "family dynamics"
    "letter" "template" "draft" "body" "disclaimer" "prompt" "audience"
    "notification" "correspondence" "bank" "utility" "insurance"
    "prompts" "instructions" "guidance" "user guidance" "template prompts"
    "help text" "tooltips" "explanations" "directions"
    "toggle" "expand" "collapse" "accordion" "show/hide" "details"
    "summary" "more info" "dropdown" "reveal"
    "general items" "miscellaneous" "support systems"
    "dashboard" "grid" "analytics" "visualization" "gauge" "chart"
    "burndown" "progress bar" "status indicator"
)

total_matches=0

for pattern in "${PATTERNS[@]}"; do
    echo "Searching for: $pattern"

    find "$BASE_DIR" \( -name "*.py" -o -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.txt" -o -name "*.md" \) -type f -exec grep -l -i "$pattern" {} \; | while read file; do
        echo "## MATCHES for \"$pattern\"" >> "$OUTPUT_FILE"
        echo "**FILE:** $file" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"

        grep -n -i -B2 -A2 "$pattern" "$file" | while IFS=: read line_num content; do
            if [[ "$line_num" =~ ^[0-9]+$ ]]; then
                echo "**LINE $line_num:**" >> "$OUTPUT_FILE"
                echo "\`\`\`" >> "$OUTPUT_FILE"
                echo "$content" >> "$OUTPUT_FILE"
                echo "\`\`\`" >> "$OUTPUT_FILE"
                echo "" >> "$OUTPUT_FILE"
                ((total_matches++))
            fi
        done
        echo "---" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    done
done

echo "# Summary" >> "$OUTPUT_FILE"
echo "- **Search Patterns:** ${#PATTERNS[@]}" >> "$OUTPUT_FILE"
echo "- **Completed:** $(date)" >> "$OUTPUT_FILE"

echo "=== Content Discovery Complete ==="
echo "Results saved to: $OUTPUT_FILE"
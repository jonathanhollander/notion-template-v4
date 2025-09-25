#!/usr/bin/env python3
"""
Comprehensive analysis of Notion Template deployment assets.
This script analyzes all YAML files and generates a detailed report
of exactly what will be deployed to each page.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

class DeploymentAnalyzer:
    def __init__(self, yaml_dir: str = 'split_yaml'):
        self.yaml_dir = Path(yaml_dir)
        self.all_pages = []
        self.page_hierarchy = {}
        self.database_schemas = {}
        self.letters = []
        self.skipped_elements = defaultdict(list)
        self.processed_elements = defaultdict(int)

    def load_all_yamls(self) -> Dict:
        """Load and merge all YAML files"""
        merged_data = {
            'pages': [],
            'databases': [],
            'letters': [],
            'database_schemas': {}
        }

        for yaml_file in sorted(self.yaml_dir.glob('*.yaml')):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}

                    # Track source file for each item
                    if 'pages' in data:
                        for page in data['pages']:
                            page['_source_file'] = yaml_file.name
                            # Process children recursively
                            self._process_page_hierarchy(page)
                            merged_data['pages'].append(page)

                    if 'databases' in data:
                        for db in data['databases']:
                            db['_source_file'] = yaml_file.name
                            merged_data['databases'].append(db)
                            title = db.get('title', 'Untitled')
                            self.database_schemas[title] = db

                    if 'letters' in data:
                        for letter in data['letters']:
                            letter['_source_file'] = yaml_file.name
                            merged_data['letters'].append(letter)
                            self.letters.append(letter)

            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")
                self.skipped_elements['file_errors'].append(f"{yaml_file.name}: {str(e)}")

        return merged_data

    def _process_page_hierarchy(self, page: Dict, parent: Optional[str] = None):
        """Recursively process page hierarchy"""
        if parent:
            page['_parent'] = parent

        if 'children' in page:
            for child in page['children']:
                child['_is_child'] = True
                self._process_page_hierarchy(child, page.get('title', 'Untitled'))

    def analyze_page_assets(self, page: Dict, level: int = 0) -> List[str]:
        """Analyze what assets will be deployed for a page"""
        assets = []
        title = page.get('title', 'Untitled')

        # Icon analysis
        if page.get('icon'):
            icon = page['icon']
            if icon.startswith('emoji:'):
                assets.append(f"Icon: {icon} (emoji)")
                self.processed_elements['emoji_icons'] += 1
            elif icon.startswith('http'):
                assets.append(f"Icon: External URL")
                self.processed_elements['url_icons'] += 1
            else:
                assets.append(f"Icon: {icon}")
                self.processed_elements['other_icons'] += 1
        elif page.get('icon_file'):
            assets.append(f"Icon File: {page['icon_file']} (requires asset generation)")
            self.processed_elements['icon_files'] += 1

        # Cover analysis
        if page.get('cover'):
            if page['cover'].startswith('http'):
                assets.append(f"Cover: External URL (Unsplash)")
                self.processed_elements['url_covers'] += 1
        elif page.get('cover_file'):
            assets.append(f"Cover File: {page['cover_file']} (requires asset generation)")
            self.processed_elements['cover_files'] += 1

        # Content blocks analysis
        if 'blocks' in page:
            block_types = defaultdict(int)
            for block in page['blocks']:
                block_type = block.get('type', 'unknown')
                block_types[block_type] += 1
                self.processed_elements[f'block_{block_type}'] += 1

            assets.append("Content Blocks:")
            for btype, count in sorted(block_types.items()):
                assets.append(f"  - {count} {btype}")
        else:
            # YAML metadata content (NOT auto-generated - this is real content from YAML)
            yaml_content = []
            if page.get('description'):
                yaml_content.append("description")
                self.processed_elements['yaml_description'] += 1
            if page.get('disclaimer'):
                yaml_content.append("disclaimer")
                self.processed_elements['yaml_disclaimer'] += 1
            if page.get('role'):
                yaml_content.append("role")
                self.processed_elements['yaml_role'] += 1

            if yaml_content:
                assets.append(f"⚠️ MISSING CONTENT BLOCKS - Only YAML metadata present: {', '.join(yaml_content)}")
                self.processed_elements['missing_content_blocks'] += 1
            else:
                assets.append("⚠️ CRITICAL: No content at all - Empty page")
                self.processed_elements['empty_pages'] += 1

        # Database links
        if page.get('database_link'):
            assets.append(f"Database Link: {page['database_link']}")
            self.processed_elements['database_links'] += 1

        # Special case: Letters page
        if title == "Letters" and self.letters:
            assets.append(f"Letter Templates: {len(self.letters)} letters will be added")
            self.processed_elements['letter_templates'] += len(self.letters)

        # Check for unused/skipped elements
        skipped = []
        if page.get('slug'):
            skipped.append('slug (not used in Notion)')
        if page.get('icon_png'):
            skipped.append('icon_png (backup asset)')
        if page.get('cover_png'):
            skipped.append('cover_png (backup asset)')
        if page.get('alt_text'):
            skipped.append('alt_text (accessibility)')

        if skipped:
            self.skipped_elements[title].extend(skipped)

        return assets

    def generate_report(self) -> str:
        """Generate comprehensive deployment report"""
        report = []
        report.append("# NOTION TEMPLATE DEPLOYMENT ASSET MAP")
        report.append("=" * 60)
        report.append("")

        # Load all data
        data = self.load_all_yamls()

        # Summary statistics
        total_pages = self._count_all_pages(data['pages'])
        report.append("## SUMMARY STATISTICS")
        report.append(f"- Total Pages to Deploy: {total_pages}")
        report.append(f"- Top-Level Pages: {len(data['pages'])}")
        report.append(f"- Database Schemas: {len(self.database_schemas)}")
        report.append(f"- Letter Templates: {len(self.letters)}")
        report.append("")

        # Detailed page hierarchy
        report.append("## COMPLETE PAGE HIERARCHY WITH ASSETS")
        report.append("=" * 60)
        report.append("")

        # Group pages by source file for organization
        pages_by_source = defaultdict(list)
        for page in data['pages']:
            source = page.get('_source_file', 'unknown')
            pages_by_source[source].append(page)

        # Process key files first for logical organization
        priority_files = [
            '01_pages_core.yaml',
            '02_pages_extended.yaml',
            '11_executor_task_profiles.yaml',
            '09_admin_rollout_setup.yaml',
            '16_letters_database.yaml',
            '25_digital_legacy.yaml',
            '25_help_system.yaml'
        ]

        for source_file in priority_files:
            if source_file in pages_by_source:
                report.extend(self._format_pages_section(source_file, pages_by_source[source_file]))

        # Process remaining files
        for source_file in sorted(pages_by_source.keys()):
            if source_file not in priority_files:
                report.extend(self._format_pages_section(source_file, pages_by_source[source_file]))

        # Database schemas section
        report.append("")
        report.append("## DATABASE SCHEMAS")
        report.append("=" * 60)
        for db_name, db_schema in self.database_schemas.items():
            report.append(f"\n### {db_name}")
            report.append(f"Source: {db_schema.get('_source_file', 'unknown')}")
            if db_schema.get('description'):
                report.append(f"Description: {db_schema['description']}")
            prop_count = len(db_schema.get('properties', {}))
            report.append(f"Properties: {prop_count} fields defined")

        # Letters section
        report.append("")
        report.append("## LETTER TEMPLATES")
        report.append("=" * 60)
        report.append(f"Total: {len(self.letters)} templates")
        for letter in self.letters[:5]:  # Show first 5 as examples
            report.append(f"- {letter.get('Title', 'Untitled')}: {letter.get('Category', 'N/A')}")
        if len(self.letters) > 5:
            report.append(f"... and {len(self.letters) - 5} more")

        # Analysis section
        report.append("")
        report.append("## DEPLOYMENT ANALYSIS")
        report.append("=" * 60)

        # Add critical missing content section FIRST
        if self.processed_elements.get('missing_content_blocks', 0) > 0:
            report.append("\n## ⚠️ CRITICAL DATA LOSS DETECTED")
            report.append("=" * 60)
            report.append(f"**{self.processed_elements.get('missing_content_blocks', 0)} pages are MISSING their content blocks!**")
            report.append("These pages have only YAML metadata (description, role, etc.) but NO actual content.")
            report.append("This represents a MAJOR data loss that must be recovered.")
            report.append("")

        report.append("\n### Content Analysis:")
        for element, count in sorted(self.processed_elements.items()):
            if count > 0:
                if 'missing' in element or 'empty' in element:
                    report.append(f"- ⚠️ {element}: {count}")
                else:
                    report.append(f"- ✓ {element}: {count}")

        report.append("\n### Skipped/Unused YAML Elements:")
        if self.skipped_elements:
            for page_title, elements in sorted(self.skipped_elements.items()):
                if elements:
                    report.append(f"\n{page_title}:")
                    for elem in elements:
                        report.append(f"  - {elem}")
        else:
            report.append("- None detected (all elements processed)")

        report.append("\n### Known Limitations:")
        report.append("- icon_file/cover_file: Requires external asset generation system")
        report.append("- Local asset files: Notion API requires external hosting")
        report.append("- Formula properties: Only work in database entries, not pages")
        report.append("- Markdown in blocks: Converted to Notion rich text format")

        return "\n".join(report)

    def _format_pages_section(self, source_file: str, pages: List[Dict]) -> List[str]:
        """Format a section of pages from a source file"""
        lines = []
        lines.append(f"\n### SOURCE: {source_file}")
        lines.append("-" * 40)

        for page in pages:
            lines.extend(self._format_page(page, 0))

        return lines

    def _format_page(self, page: Dict, level: int) -> List[str]:
        """Format a single page with its assets and children"""
        lines = []
        indent = "  " * level
        title = page.get('title', 'Untitled')

        # Page header
        if page.get('_is_child'):
            lines.append(f"{indent}└─ {title}")
        else:
            lines.append(f"\n{indent}📄 {title}")

        # Parent relationship
        if page.get('parent'):
            lines.append(f"{indent}   Parent: {page['parent']}")

        # Assets
        assets = self.analyze_page_assets(page, level)
        for asset in assets:
            lines.append(f"{indent}   • {asset}")

        # Children
        if 'children' in page:
            lines.append(f"{indent}   • Child Pages: {len(page['children'])} nested pages")
            for child in page['children']:
                lines.extend(self._format_page(child, level + 1))

        return lines

    def _count_all_pages(self, pages: List[Dict]) -> int:
        """Recursively count all pages including children"""
        count = 0
        for page in pages:
            count += 1
            if 'children' in page:
                count += self._count_all_pages(page['children'])
        return count


if __name__ == "__main__":
    analyzer = DeploymentAnalyzer()
    report = analyzer.generate_report()

    # Save to file
    output_file = Path("deployment_assets_map.md")
    output_file.write_text(report)
    print(f"✅ Report generated: {output_file}")
    print(f"📄 Total lines: {len(report.splitlines())}")
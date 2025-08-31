"""CSV Import Module for Notion Deployment.

Provides automated CSV data import functionality with support for:
- Multiple CSV files
- Field mapping configuration
- Data type conversion
- Batch processing
- Error handling and logging
"""

import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from constants import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class CSVImporter:
    """Handles automated CSV import to Notion databases."""
    
    def __init__(self, csv_dir: str = "csv", mapping_file: str = "csv_mapping.json"):
        """Initialize CSV importer with configuration.
        
        Args:
            csv_dir: Directory containing CSV files
            mapping_file: JSON file with field mappings
        """
        self.csv_dir = Path(csv_dir)
        self.mapping_file = Path(mapping_file)
        self.mappings = self._load_mappings()
        self.imported_count = 0
        self.error_count = 0
        
    def _load_mappings(self) -> Dict[str, Any]:
        """Load field mapping configuration from JSON file."""
        if not self.mapping_file.exists():
            logger.warning(f"Mapping file {self.mapping_file} not found, using default mappings")
            return self._get_default_mappings()
        
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in mapping file: {e}")
            return self._get_default_mappings()
    
    def _get_default_mappings(self) -> Dict[str, Any]:
        """Return default CSV to Notion field mappings."""
        return {
            "contacts.csv": {
                "database": "Contacts",
                "fields": {
                    "Name": {"type": "title", "csv_column": "name"},
                    "Email": {"type": "email", "csv_column": "email"},
                    "Phone": {"type": "phone_number", "csv_column": "phone"},
                    "Relationship": {"type": "select", "csv_column": "relationship"},
                    "Notes": {"type": "rich_text", "csv_column": "notes"}
                }
            },
            "assets.csv": {
                "database": "Assets",
                "fields": {
                    "Asset Name": {"type": "title", "csv_column": "asset_name"},
                    "Category": {"type": "select", "csv_column": "category"},
                    "Value": {"type": "number", "csv_column": "value"},
                    "Location": {"type": "rich_text", "csv_column": "location"},
                    "Description": {"type": "rich_text", "csv_column": "description"}
                }
            },
            "documents.csv": {
                "database": "Important Documents",
                "fields": {
                    "Document Name": {"type": "title", "csv_column": "document_name"},
                    "Type": {"type": "select", "csv_column": "type"},
                    "Location": {"type": "rich_text", "csv_column": "location"},
                    "Expiry Date": {"type": "date", "csv_column": "expiry_date"},
                    "Notes": {"type": "rich_text", "csv_column": "notes"}
                }
            }
        }
    
    def import_all_csv_files(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Import all CSV files found in the CSV directory.
        
        Args:
            state: Current deployment state
            
        Returns:
            Import statistics and results
        """
        results = {
            "imported": [],
            "failed": [],
            "total_rows": 0,
            "errors": []
        }
        
        if not self.csv_dir.exists():
            logger.info(f"CSV directory {self.csv_dir} not found, skipping CSV import")
            return results
        
        csv_files = list(self.csv_dir.glob("*.csv"))
        if not csv_files:
            logger.info("No CSV files found to import")
            return results
        
        logger.info(f"Found {len(csv_files)} CSV files to import")
        
        for csv_file in csv_files:
            file_name = csv_file.name
            if file_name not in self.mappings:
                logger.warning(f"No mapping found for {file_name}, skipping")
                results["failed"].append(file_name)
                continue
            
            try:
                rows_imported = self._import_csv_file(csv_file, state)
                results["imported"].append(file_name)
                results["total_rows"] += rows_imported
                logger.info(f"Imported {rows_imported} rows from {file_name}")
            except Exception as e:
                logger.error(f"Failed to import {file_name}: {e}")
                results["failed"].append(file_name)
                results["errors"].append(str(e))
        
        return results
    
    def _import_csv_file(self, csv_file: Path, state: Dict[str, Any]) -> int:
        """Import a single CSV file to its mapped database.
        
        Args:
            csv_file: Path to CSV file
            state: Current deployment state
            
        Returns:
            Number of rows imported
        """
        file_name = csv_file.name
        mapping = self.mappings[file_name]
        database_name = mapping["database"]
        field_mappings = mapping["fields"]
        
        # Find database ID in state
        database_id = self._find_database_id(state, database_name)
        if not database_id:
            raise ValueError(f"Database '{database_name}' not found in deployment state")
        
        rows_imported = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                try:
                    properties = self._convert_row_to_properties(row, field_mappings)
                    if self._create_database_row(database_id, properties, state):
                        rows_imported += 1
                except Exception as e:
                    logger.error(f"Error importing row {row_num} from {file_name}: {e}")
                    self.error_count += 1
        
        self.imported_count += rows_imported
        return rows_imported
    
    def _find_database_id(self, state: Dict[str, Any], database_name: str) -> Optional[str]:
        """Find database ID from state by name.
        
        Args:
            state: Current deployment state
            database_name: Name of the database
            
        Returns:
            Database ID if found, None otherwise
        """
        databases = state.get("databases", {})
        for db_id, db_info in databases.items():
            if db_info.get("name") == database_name:
                return db_id
        return None
    
    def _convert_row_to_properties(self, row: Dict[str, str], 
                                   field_mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CSV row to Notion properties format.
        
        Args:
            row: CSV row data
            field_mappings: Field mapping configuration
            
        Returns:
            Notion properties dictionary
        """
        properties = {}
        
        for notion_field, mapping in field_mappings.items():
            csv_column = mapping["csv_column"]
            field_type = mapping["type"]
            value = row.get(csv_column, "")
            
            if not value:
                continue
            
            if field_type == "title":
                properties[notion_field] = {
                    "title": [{"text": {"content": value}}]
                }
            elif field_type == "rich_text":
                properties[notion_field] = {
                    "rich_text": [{"text": {"content": value}}]
                }
            elif field_type == "number":
                try:
                    properties[notion_field] = {
                        "number": float(value)
                    }
                except ValueError:
                    logger.warning(f"Invalid number value: {value}")
            elif field_type == "select":
                properties[notion_field] = {
                    "select": {"name": value}
                }
            elif field_type == "email":
                properties[notion_field] = {
                    "email": value
                }
            elif field_type == "phone_number":
                properties[notion_field] = {
                    "phone_number": value
                }
            elif field_type == "date":
                # Assume ISO format date
                properties[notion_field] = {
                    "date": {"start": value}
                }
            elif field_type == "checkbox":
                properties[notion_field] = {
                    "checkbox": value.lower() in ("true", "yes", "1")
                }
            elif field_type == "url":
                properties[notion_field] = {
                    "url": value
                }
        
        return properties
    
    def _create_database_row(self, database_id: str, properties: Dict[str, Any], 
                            state: Dict[str, Any]) -> bool:
        """Create a new row in Notion database.
        
        Args:
            database_id: Target database ID
            properties: Row properties
            state: Current deployment state
            
        Returns:
            True if successful, False otherwise
        """
        # This would call the actual Notion API
        # For now, we'll store it in state for later processing
        if "csv_imports" not in state:
            state["csv_imports"] = []
        
        state["csv_imports"].append({
            "database_id": database_id,
            "properties": properties
        })
        
        return True
    
    def get_import_stats(self) -> Dict[str, int]:
        """Get import statistics.
        
        Returns:
            Dictionary with import stats
        """
        return {
            "imported": self.imported_count,
            "errors": self.error_count,
            "success_rate": (self.imported_count / (self.imported_count + self.error_count) * 100) 
                           if (self.imported_count + self.error_count) > 0 else 0
        }


def import_csv_data(state: Dict[str, Any], csv_dir: Optional[str] = None) -> Dict[str, Any]:
    """Main entry point for CSV import functionality.
    
    Args:
        state: Current deployment state
        csv_dir: Optional CSV directory path
        
    Returns:
        Import results
    """
    csv_directory = csv_dir or os.getenv("CSV_IMPORT_DIR", "csv")
    importer = CSVImporter(csv_directory)
    
    logger.info("Starting automated CSV import...")
    results = importer.import_all_csv_files(state)
    stats = importer.get_import_stats()
    
    logger.info(f"CSV Import completed: {stats['imported']} rows imported, "
                f"{stats['errors']} errors, {stats['success_rate']:.1f}% success rate")
    
    return {
        "results": results,
        "stats": stats
    }
# Configuration Backup Directory

This directory contains automatic backups of emotional configuration changes.

## Structure

- `emotional_config/` - Timestamped backups of `emotional_config.yaml`
- Backup format: `emotional_config_YYYY-MM-DD_HH-MM-SS.yaml`

## Automatic Backup Rules

1. Backup created before any configuration changes
2. Maximum 10 backups retained (oldest auto-deleted)  
3. Manual backups can be created via API
4. Reset-to-defaults creates backup before reset

## Restoration

Use the web interface "Reset to Defaults" or manually copy a backup file to `../emotional_config.yaml`
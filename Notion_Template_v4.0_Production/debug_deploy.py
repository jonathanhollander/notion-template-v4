#!/usr/bin/env python3
"""
Debug deployment wrapper with enhanced logging options
Provides CLI flags for detailed debugging of Notion deployment
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Debug deployment wrapper with enhanced logging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic deployment with API debugging
  python debug_deploy.py --debug-api

  # Full debugging (API + assets + request tracing)
  python debug_deploy.py --debug-all --dry-run

  # Asset pipeline debugging only
  python debug_deploy.py --debug-assets --test --generate-assets

  # Trace specific requests with correlation IDs
  python debug_deploy.py --trace-requests --verbose

  # View debug logs after run
  python debug_deploy.py --show-logs

Debug Log Files Created:
  logs/deploy_debug_api.log     - All API requests/responses (JSON format)
  logs/deploy_debug_assets.log  - Asset processing pipeline details
  logs/deploy_debug_trace.log   - Request tracing with correlation IDs
  logs/deploy_errors.log        - All errors with full context
  logs/deployment.log           - Main deployment log
        """
    )

    # Debug flags
    debug_group = parser.add_argument_group('Debug Options')
    debug_group.add_argument('--debug-api', action='store_true',
                           help='Enable detailed API request/response logging')
    debug_group.add_argument('--debug-assets', action='store_true',
                           help='Enable asset deployment pipeline logging')
    debug_group.add_argument('--trace-requests', action='store_true',
                           help='Enable request correlation tracing')
    debug_group.add_argument('--debug-all', action='store_true',
                           help='Enable all debugging options')

    # Log management
    log_group = parser.add_argument_group('Log Management')
    log_group.add_argument('--show-logs', action='store_true',
                          help='Show recent debug logs and exit')
    log_group.add_argument('--clear-logs', action='store_true',
                          help='Clear all debug logs and exit')
    log_group.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                          default='INFO', help='Set logging level')

    # Deploy.py pass-through arguments
    deploy_group = parser.add_argument_group('Deployment Options')
    deploy_group.add_argument('--dry-run', action='store_true',
                             help='Simulate deployment without API calls')
    deploy_group.add_argument('--test', action='store_true',
                             help='Run in test mode')
    deploy_group.add_argument('--generate-assets', action='store_true',
                             help='Generate assets during deployment')
    deploy_group.add_argument('--verbose', action='count', default=0,
                             help='Increase verbosity (-v, -vv, -vvv)')
    deploy_group.add_argument('--parent-id', type=str,
                             help='Parent page ID for deployment')

    args = parser.parse_args()

    # Handle log management commands
    if args.show_logs:
        show_recent_logs()
        return

    if args.clear_logs:
        clear_debug_logs()
        return

    # Set up environment variables for debug flags
    env = os.environ.copy()

    if args.debug_all:
        args.debug_api = True
        args.debug_assets = True
        args.trace_requests = True

    if args.debug_api:
        env['DEBUG_API'] = 'true'
        print("🔍 API debugging enabled - requests/responses will be logged to logs/deploy_debug_api.log")

    if args.debug_assets:
        env['DEBUG_ASSETS'] = 'true'
        print("📦 Asset debugging enabled - pipeline details will be logged to logs/deploy_debug_assets.log")

    if args.trace_requests:
        env['TRACE_REQUESTS'] = 'true'
        print("🔗 Request tracing enabled - correlation IDs will be logged to logs/deploy_debug_trace.log")

    env['LOG_LEVEL'] = args.log_level

    # Build deploy.py command
    deploy_cmd = [sys.executable, 'deploy.py']

    # Add deploy.py arguments
    if args.dry_run:
        deploy_cmd.append('--dry-run')
    if args.test:
        deploy_cmd.append('--test')
    if args.generate_assets:
        deploy_cmd.append('--generate-assets')
    if args.parent_id:
        deploy_cmd.extend(['--parent-id', args.parent_id])

    # Add verbosity
    if args.verbose:
        deploy_cmd.extend(['-' + 'v' * min(args.verbose, 3)])

    # Ensure logs directory exists
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("🚀 Starting enhanced debug deployment")
    print(f"📊 Log level: {args.log_level}")
    print(f"📝 Main log: logs/deployment.log")
    print(f"❌ Error log: logs/deploy_errors.log")
    print("=" * 60)

    # Run deploy.py with enhanced environment
    try:
        result = subprocess.run(deploy_cmd, env=env, cwd=Path.cwd())

        print("=" * 60)
        print("📋 Debug deployment completed")
        print(f"Exit code: {result.returncode}")

        # Show log summary
        show_log_summary()

        return result.returncode

    except KeyboardInterrupt:
        print("\n⚠️  Deployment interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Failed to run deployment: {e}")
        return 1


def show_recent_logs():
    """Show recent entries from debug logs"""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        print("📝 No logs directory found")
        return

    log_files = {
        'deployment.log': 'Main Deployment',
        'deploy_errors.log': 'Errors Only',
        'deploy_debug_api.log': 'API Debug',
        'deploy_debug_assets.log': 'Assets Debug',
        'deploy_debug_trace.log': 'Request Tracing'
    }

    print("📋 Recent Debug Logs:")
    print("=" * 50)

    for filename, description in log_files.items():
        log_file = logs_dir / filename
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"\n{description} ({filename}):")
                        print("-" * 30)
                        # Show last 10 lines
                        for line in lines[-10:]:
                            print(f"  {line.rstrip()}")
                        print(f"  ... (showing last 10 of {len(lines)} lines)")
                    else:
                        print(f"\n{description} ({filename}): Empty")
            except Exception as e:
                print(f"\n{description} ({filename}): Error reading - {e}")
        else:
            print(f"\n{description} ({filename}): Not found")


def clear_debug_logs():
    """Clear all debug log files"""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        print("📝 No logs directory found")
        return

    log_files = [
        'deployment.log',
        'deploy_errors.log',
        'deploy_debug_api.log',
        'deploy_debug_assets.log',
        'deploy_debug_trace.log'
    ]

    cleared_count = 0
    for filename in log_files:
        log_file = logs_dir / filename
        if log_file.exists():
            try:
                log_file.unlink()
                cleared_count += 1
                print(f"🗑️  Cleared {filename}")
            except Exception as e:
                print(f"❌ Failed to clear {filename}: {e}")

    if cleared_count > 0:
        print(f"✅ Cleared {cleared_count} debug log files")
    else:
        print("📝 No debug log files to clear")


def show_log_summary():
    """Show summary of log files created"""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        return

    log_files = [
        ('deployment.log', 'Main deployment log'),
        ('deploy_errors.log', 'Errors and warnings'),
        ('deploy_debug_api.log', 'API requests/responses (JSON)'),
        ('deploy_debug_assets.log', 'Asset processing details'),
        ('deploy_debug_trace.log', 'Request correlation tracing')
    ]

    print("\n📊 Debug Log Files Created:")
    for filename, description in log_files:
        log_file = logs_dir / filename
        if log_file.exists():
            size = log_file.stat().st_size
            if size > 0:
                size_str = f"{size:,} bytes"
                if size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                if size > 1024*1024:
                    size_str = f"{size/(1024*1024):.1f} MB"

                print(f"  📄 {filename} - {description} ({size_str})")

    print(f"\nTo view logs: python debug_deploy.py --show-logs")
    print(f"To clear logs: python debug_deploy.py --clear-logs")


if __name__ == '__main__':
    sys.exit(main())
#!/usr/bin/env python3
"""
Simple debug wrapper - ALL logging goes to ONE file
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--show-log':
        show_log()
        return

    if len(sys.argv) > 1 and sys.argv[1] == '--clear-log':
        clear_log()
        return

    # Set up ONE debug log file with color coding
    env = os.environ.copy()
    env['LOG_LEVEL'] = 'DEBUG'
    env['LOG_FILE'] = 'logs/debug.log'
    env['DEBUG_API'] = 'true'
    env['DEBUG_ASSETS'] = 'true'
    env['USE_SIMPLE_LOGGING'] = 'true'  # Flag to use simple unified logging

    # Ensure logs directory exists
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    # Clear the debug log
    debug_log = logs_dir / 'debug.log'
    if debug_log.exists():
        debug_log.unlink()

    # Build deploy.py command
    deploy_cmd = [sys.executable, 'deploy.py'] + sys.argv[1:]

    print("🚀 Running deployment with debug logging")
    print("📝 ALL output will be in: logs/debug.log")
    print("=" * 50)

    try:
        # Run deploy.py
        result = subprocess.run(deploy_cmd, env=env)

        print("=" * 50)
        print(f"✅ Deployment finished (exit code: {result.returncode})")
        print("📄 View debug log: python simple_debug.py --show-log")

        return result.returncode

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

def show_log():
    """Show the debug log with color coding for different log types"""
    # Check for debug.log first, then deployment.log
    debug_log = Path('logs/debug.log')
    if not debug_log.exists():
        debug_log = Path('logs/deployment.log')

    if not debug_log.exists():
        print("📝 No debug log found. Run deployment first.")
        return

    print(f"📄 Debug Log ({debug_log}):")
    print("=" * 60)
    print("🟢 = API Calls | 🔵 = Asset Processing | 🔴 = Errors | ⚫ = General | 🟣 = Requests | 🟠 = YAML Processing")
    print("=" * 60)

    try:
        with open(debug_log, 'r') as f:
            lines = f.readlines()
            if lines:
                for line in lines:
                    # Add color coding based on log content
                    colored_line = color_code_log_line(line.rstrip())
                    print(colored_line)
            else:
                print("(Log file is empty)")
    except Exception as e:
        print(f"❌ Error reading log: {e}")

def color_code_log_line(line):
    """Add color prefixes to log lines based on content"""
    line_lower = line.lower()

    # API calls and responses
    if any(keyword in line_lower for keyword in ['api_request', 'api_response', 'post /v1/', 'patch /v1/', 'get /v1/', 'status_code:', 'notion api']):
        return f"🟢 {line}"

    # Asset processing
    elif any(keyword in line_lower for keyword in ['asset', 'icon', 'cover', 'image', 'processing', 'block creation', 'page creation']):
        return f"🔵 {line}"

    # Errors and warnings
    elif any(keyword in line_lower for keyword in ['error', 'failed', 'exception', 'warning', 'critical']):
        return f"🔴 {line}"

    # Request tracing and correlation
    elif any(keyword in line_lower for keyword in ['correlation_id', 'request_id', 'tracing', 'elapsed_seconds']):
        return f"🟣 {line}"

    # YAML processing
    elif any(keyword in line_lower for keyword in ['yaml', 'section', 'parsing', 'configuration']):
        return f"🟠 {line}"

    # General logging
    else:
        return f"⚫ {line}"

def clear_log():
    """Clear the debug log"""
    cleared = False

    # Clear both possible log files
    for log_file in ['logs/debug.log', 'logs/deployment.log']:
        log_path = Path(log_file)
        if log_path.exists():
            log_path.unlink()
            print(f"🗑️ Cleared {log_file}")
            cleared = True

    if not cleared:
        print("📝 No debug logs to clear")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python simple_debug.py --dry-run          # Run with debug logging")
        print("  python simple_debug.py --show-log         # View the debug log")
        print("  python simple_debug.py --clear-log        # Clear the debug log")
        print("")
        print("All deploy.py options work:")
        print("  python simple_debug.py --dry-run --verbose")
        print("  python simple_debug.py --test --generate-assets")
        sys.exit(1)

    sys.exit(main())
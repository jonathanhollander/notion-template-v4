#!/usr/bin/env python3
"""
Comprehensive Security Logging for Estate Planning Concierge v4.0
Tracks security events, authentication attempts, and suspicious activities
"""

import logging
import json
import sqlite3
import aiosqlite
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib
import asyncio
from enum import Enum

class SecurityEventType(Enum):
    """Types of security events to log"""
    AUTH_SUCCESS = "authentication_success"
    AUTH_FAILURE = "authentication_failure"
    CSRF_VALIDATION_FAILED = "csrf_validation_failed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_INPUT = "invalid_input_detected"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    SESSION_HIJACK_ATTEMPT = "session_hijack_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation_attempt"
    DATA_EXFILTRATION = "data_exfiltration_attempt"
    BRUTE_FORCE_DETECTED = "brute_force_detected"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    API_ABUSE = "api_abuse"
    FILE_UPLOAD_BLOCKED = "file_upload_blocked"

class SecurityLogger:
    """Comprehensive security event logger with SQLite backend"""
    
    def __init__(self, db_path: str = "security_events.db", 
                 log_file: str = "security.log",
                 alert_threshold: int = 5):
        """
        Initialize security logger
        
        Args:
            db_path: Path to SQLite database for security events
            log_file: Path to security log file
            alert_threshold: Number of suspicious events before alerting
        """
        self.db_path = db_path
        self.alert_threshold = alert_threshold
        
        # Setup file logger
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # File handler with rotation
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(event_type)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Initialize database
        self._init_database()
        
        # Track recent events for pattern detection
        self.recent_events = {}
    
    def _init_database(self):
        """Initialize security events database"""
        with sqlite3.connect(self.db_path) as conn:
            # Main security events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    session_id TEXT,
                    user_id TEXT,
                    endpoint TEXT,
                    method TEXT,
                    request_data TEXT,
                    response_code INTEGER,
                    message TEXT,
                    stack_trace TEXT,
                    timestamp REAL NOT NULL,
                    handled BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create indexes for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON security_events(timestamp DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_ip 
                ON security_events(ip_address)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_type 
                ON security_events(event_type)
            """)
            
            # IP reputation tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ip_reputation (
                    ip_address TEXT PRIMARY KEY,
                    threat_score INTEGER DEFAULT 0,
                    total_events INTEGER DEFAULT 0,
                    suspicious_events INTEGER DEFAULT 0,
                    first_seen REAL NOT NULL,
                    last_seen REAL NOT NULL,
                    is_blocked BOOLEAN DEFAULT FALSE,
                    block_reason TEXT,
                    block_expires REAL
                )
            """)
            
            # Pattern detection table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS attack_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    ip_address TEXT,
                    detected_at REAL NOT NULL,
                    event_count INTEGER,
                    pattern_data TEXT,
                    severity TEXT,
                    mitigated BOOLEAN DEFAULT FALSE
                )
            """)
            
            conn.commit()
    
    def log_event(self, event_type: SecurityEventType, 
                 severity: str = "medium",
                 ip_address: Optional[str] = None,
                 user_agent: Optional[str] = None,
                 session_id: Optional[str] = None,
                 user_id: Optional[str] = None,
                 endpoint: Optional[str] = None,
                 method: Optional[str] = None,
                 request_data: Optional[Dict] = None,
                 response_code: Optional[int] = None,
                 message: Optional[str] = None,
                 stack_trace: Optional[str] = None) -> int:
        """
        Log a security event
        
        Args:
            event_type: Type of security event
            severity: Event severity (low, medium, high, critical)
            Other args: Event context information
            
        Returns:
            Event ID
        """
        timestamp = datetime.now().timestamp()
        
        # Sanitize request data to prevent logging sensitive info
        safe_request_data = self._sanitize_request_data(request_data) if request_data else None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO security_events 
                (event_type, severity, ip_address, user_agent, session_id, 
                 user_id, endpoint, method, request_data, response_code, 
                 message, stack_trace, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_type.value, severity, ip_address, user_agent, session_id,
                user_id, endpoint, method, 
                json.dumps(safe_request_data) if safe_request_data else None,
                response_code, message, stack_trace, timestamp
            ))
            
            event_id = cursor.lastrowid
            
            # Update IP reputation
            if ip_address:
                self._update_ip_reputation(conn, ip_address, event_type, severity)
            
            # Check for attack patterns
            if severity in ['high', 'critical']:
                self._detect_patterns(conn, ip_address, event_type)
            
            conn.commit()
        
        # Log to file
        self.logger.log(
            logging.WARNING if severity in ['high', 'critical'] else logging.INFO,
            f"{message or event_type.value} - IP: {ip_address} - Session: {session_id}",
            extra={'event_type': event_type.value}
        )
        
        # Check if we need to trigger alerts
        if severity in ['high', 'critical']:
            self._check_alert_threshold(ip_address, event_type)
        
        return event_id
    
    async def log_event_async(self, event_type: SecurityEventType,
                            severity: str = "medium",
                            **kwargs) -> int:
        """Async version of log_event"""
        timestamp = datetime.now().timestamp()
        
        request_data = kwargs.get('request_data')
        safe_request_data = self._sanitize_request_data(request_data) if request_data else None
        
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute("""
                INSERT INTO security_events 
                (event_type, severity, ip_address, user_agent, session_id, 
                 user_id, endpoint, method, request_data, response_code, 
                 message, stack_trace, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_type.value, severity, 
                kwargs.get('ip_address'), kwargs.get('user_agent'),
                kwargs.get('session_id'), kwargs.get('user_id'),
                kwargs.get('endpoint'), kwargs.get('method'),
                json.dumps(safe_request_data) if safe_request_data else None,
                kwargs.get('response_code'), kwargs.get('message'),
                kwargs.get('stack_trace'), timestamp
            ))
            
            event_id = cursor.lastrowid
            await conn.commit()
        
        return event_id
    
    def _sanitize_request_data(self, data: Dict) -> Dict:
        """Remove sensitive information from request data before logging"""
        sensitive_keys = {
            'password', 'token', 'api_key', 'secret', 'csrf_token',
            'session_id', 'credit_card', 'ssn', 'bank_account'
        }
        
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_request_data(value)
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:100] + '...[TRUNCATED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _update_ip_reputation(self, conn: sqlite3.Connection, 
                            ip_address: str, 
                            event_type: SecurityEventType,
                            severity: str):
        """Update IP reputation based on security events"""
        now = datetime.now().timestamp()
        
        # Check if IP exists
        cursor = conn.execute(
            "SELECT threat_score, total_events, suspicious_events FROM ip_reputation WHERE ip_address = ?",
            (ip_address,)
        )
        row = cursor.fetchone()
        
        if row:
            threat_score, total_events, suspicious_events = row
            total_events += 1
            
            # Increase threat score based on severity
            if severity == 'critical':
                threat_score += 10
                suspicious_events += 1
            elif severity == 'high':
                threat_score += 5
                suspicious_events += 1
            elif severity == 'medium':
                threat_score += 2
            
            conn.execute("""
                UPDATE ip_reputation 
                SET threat_score = ?, total_events = ?, suspicious_events = ?, last_seen = ?
                WHERE ip_address = ?
            """, (threat_score, total_events, suspicious_events, now, ip_address))
            
            # Auto-block if threat score too high
            if threat_score >= 50:
                block_expires = now + (24 * 3600)  # 24 hour block
                conn.execute("""
                    UPDATE ip_reputation 
                    SET is_blocked = TRUE, block_reason = ?, block_expires = ?
                    WHERE ip_address = ?
                """, (f"High threat score: {threat_score}", block_expires, ip_address))
                
                self.logger.critical(f"IP {ip_address} auto-blocked due to high threat score: {threat_score}")
        else:
            # New IP
            threat_score = 10 if severity == 'critical' else (5 if severity == 'high' else 0)
            suspicious_events = 1 if severity in ['high', 'critical'] else 0
            
            conn.execute("""
                INSERT INTO ip_reputation 
                (ip_address, threat_score, total_events, suspicious_events, first_seen, last_seen)
                VALUES (?, ?, 1, ?, ?, ?)
            """, (ip_address, threat_score, suspicious_events, now, now))
    
    def _detect_patterns(self, conn: sqlite3.Connection, 
                        ip_address: str, 
                        event_type: SecurityEventType):
        """Detect attack patterns from event sequences"""
        now = datetime.now().timestamp()
        window = now - 300  # 5 minute window
        
        # Count recent similar events
        cursor = conn.execute("""
            SELECT COUNT(*) FROM security_events 
            WHERE ip_address = ? AND event_type = ? AND timestamp > ?
        """, (ip_address, event_type.value, window))
        
        count = cursor.fetchone()[0]
        
        # Detect patterns
        pattern_detected = None
        
        if count >= 10:
            pattern_detected = "rapid_fire_attack"
        elif event_type in [SecurityEventType.SQL_INJECTION_ATTEMPT, 
                           SecurityEventType.XSS_ATTEMPT]:
            pattern_detected = "injection_attack_pattern"
        elif event_type == SecurityEventType.AUTH_FAILURE and count >= 5:
            pattern_detected = "brute_force_pattern"
        
        if pattern_detected:
            conn.execute("""
                INSERT INTO attack_patterns 
                (pattern_type, ip_address, detected_at, event_count, severity)
                VALUES (?, ?, ?, ?, ?)
            """, (pattern_detected, ip_address, now, count, 'high'))
            
            self.logger.warning(f"Attack pattern detected: {pattern_detected} from {ip_address}")
    
    def _check_alert_threshold(self, ip_address: str, event_type: SecurityEventType):
        """Check if we need to trigger security alerts"""
        key = f"{ip_address}:{event_type.value}"
        now = datetime.now().timestamp()
        
        if key not in self.recent_events:
            self.recent_events[key] = []
        
        # Add current event
        self.recent_events[key].append(now)
        
        # Remove old events (older than 5 minutes)
        self.recent_events[key] = [t for t in self.recent_events[key] if t > now - 300]
        
        # Check threshold
        if len(self.recent_events[key]) >= self.alert_threshold:
            self.trigger_alert(ip_address, event_type, len(self.recent_events[key]))
    
    def trigger_alert(self, ip_address: str, event_type: SecurityEventType, count: int):
        """Trigger security alert (in production, send to monitoring system)"""
        alert_message = f"SECURITY ALERT: {count} {event_type.value} events from {ip_address} in 5 minutes"
        self.logger.critical(alert_message)
        
        # In production, integrate with:
        # - Email alerts
        # - Slack/Discord webhooks  
        # - PagerDuty
        # - SIEM systems
        print(f"\n🚨 {alert_message}\n")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP address is blocked"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT is_blocked, block_expires FROM ip_reputation 
                WHERE ip_address = ?
            """, (ip_address,))
            
            row = cursor.fetchone()
            if row:
                is_blocked, block_expires = row
                if is_blocked:
                    if block_expires and datetime.now().timestamp() > block_expires:
                        # Block expired, unblock
                        conn.execute("""
                            UPDATE ip_reputation 
                            SET is_blocked = FALSE, block_expires = NULL 
                            WHERE ip_address = ?
                        """, (ip_address,))
                        conn.commit()
                        return False
                    return True
        
        return False
    
    def get_threat_score(self, ip_address: str) -> int:
        """Get threat score for an IP address"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT threat_score FROM ip_reputation WHERE ip_address = ?",
                (ip_address,)
            )
            row = cursor.fetchone()
            return row[0] if row else 0
    
    def get_recent_events(self, hours: int = 24, 
                         severity_filter: Optional[str] = None) -> List[Dict]:
        """Get recent security events"""
        since = datetime.now().timestamp() - (hours * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = """
                SELECT * FROM security_events 
                WHERE timestamp > ?
            """
            params = [since]
            
            if severity_filter:
                query += " AND severity = ?"
                params.append(severity_filter)
            
            query += " ORDER BY timestamp DESC LIMIT 1000"
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        now = datetime.now().timestamp()
        day_ago = now - (24 * 3600)
        week_ago = now - (7 * 24 * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            # Event statistics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high,
                    SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low
                FROM security_events 
                WHERE timestamp > ?
            """, (day_ago,))
            
            stats = dict(cursor.fetchone())
            
            # Top threat IPs
            cursor = conn.execute("""
                SELECT ip_address, threat_score, suspicious_events, is_blocked
                FROM ip_reputation 
                ORDER BY threat_score DESC 
                LIMIT 10
            """)
            top_threats = [dict(row) for row in cursor.fetchall()]
            
            # Recent patterns
            cursor = conn.execute("""
                SELECT pattern_type, COUNT(*) as count 
                FROM attack_patterns 
                WHERE detected_at > ?
                GROUP BY pattern_type
            """, (week_ago,))
            patterns = dict(cursor.fetchall())
            
            # Event type distribution
            cursor = conn.execute("""
                SELECT event_type, COUNT(*) as count 
                FROM security_events 
                WHERE timestamp > ?
                GROUP BY event_type 
                ORDER BY count DESC
            """, (day_ago,))
            event_distribution = dict(cursor.fetchall())
        
        return {
            'generated_at': datetime.now().isoformat(),
            'period': '24_hours',
            'statistics': stats,
            'top_threat_ips': top_threats,
            'attack_patterns': patterns,
            'event_distribution': event_distribution,
            'blocked_ips_count': len([ip for ip in top_threats if ip.get('is_blocked')])
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize security logger
    sec_logger = SecurityLogger()
    
    # Test logging various security events
    print("Testing Security Logger...")
    
    # Successful authentication
    sec_logger.log_event(
        SecurityEventType.AUTH_SUCCESS,
        severity="low",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
        session_id="test_session_123",
        endpoint="/api/login",
        method="POST",
        message="User authenticated successfully"
    )
    
    # Failed authentication attempts (potential brute force)
    for i in range(6):
        sec_logger.log_event(
            SecurityEventType.AUTH_FAILURE,
            severity="medium",
            ip_address="10.0.0.50",
            user_agent="Suspicious Bot",
            endpoint="/api/login",
            method="POST",
            message=f"Authentication failed - attempt {i+1}"
        )
    
    # SQL injection attempt
    sec_logger.log_event(
        SecurityEventType.SQL_INJECTION_ATTEMPT,
        severity="critical",
        ip_address="10.0.0.50",
        endpoint="/api/users",
        method="GET",
        request_data={"id": "1 OR 1=1"},
        message="SQL injection detected in query parameter"
    )
    
    # XSS attempt
    sec_logger.log_event(
        SecurityEventType.XSS_ATTEMPT,
        severity="high",
        ip_address="172.16.0.99",
        endpoint="/api/comments",
        method="POST",
        request_data={"comment": "<script>alert('xss')</script>"},
        message="XSS attempt blocked in user input"
    )
    
    # Check IP reputation
    print(f"\nIP 10.0.0.50 threat score: {sec_logger.get_threat_score('10.0.0.50')}")
    print(f"IP 10.0.0.50 blocked: {sec_logger.is_ip_blocked('10.0.0.50')}")
    
    # Generate security report
    report = sec_logger.generate_security_report()
    print(f"\nSecurity Report:")
    print(json.dumps(report, indent=2))
    
    print("\nSecurity Logger tests complete!")
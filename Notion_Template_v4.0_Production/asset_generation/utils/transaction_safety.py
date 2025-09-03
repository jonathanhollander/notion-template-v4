"""Transaction safety manager for financial operations."""

import json
import asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
import logging

from .exceptions import (
    BudgetExceededError,
    TransactionError,
    RollbackError,
    APIError
)


@dataclass
class Transaction:
    """Represents a financial transaction."""
    id: str
    timestamp: str
    asset_type: str
    cost: float
    status: str  # 'pending', 'success', 'failed', 'rolled_back'
    prompt: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    api_response: Optional[Dict] = None


class TransactionManager:
    """Manages financial transactions with safety guarantees."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """Initialize transaction manager.
        
        Args:
            config: Application configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.total_cost = 0.0
        self.transactions = []
        self.transaction_log_path = Path(config.get('logging', {}).get(
            'transaction_log', 'logs/transactions.json'
        ))
        self.transaction_log_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_transaction_history()
        
    def _load_transaction_history(self):
        """Load previous transaction history if exists."""
        if self.transaction_log_path.exists():
            try:
                with open(self.transaction_log_path, 'r') as f:
                    data = json.load(f)
                    self.total_cost = data.get('total_cost', 0.0)
                    self.transactions = data.get('transactions', [])
                    self.logger.info(f"Loaded transaction history: ${self.total_cost:.2f} spent")
            except Exception as e:
                self.logger.warning(f"Could not load transaction history: {e}")
                
    def _save_transaction_log(self):
        """Save transaction log to file."""
        try:
            with open(self.transaction_log_path, 'w') as f:
                json.dump({
                    'total_cost': self.total_cost,
                    'last_updated': datetime.now().isoformat(),
                    'transactions': [asdict(t) if isinstance(t, Transaction) else t 
                                   for t in self.transactions[-100:]]  # Keep last 100
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save transaction log: {e}")
            
    def get_budget_limit(self, is_production: bool = False) -> float:
        """Get the appropriate budget limit.
        
        Args:
            is_production: Whether this is production or sample generation
            
        Returns:
            Budget limit in dollars
        """
        if is_production:
            return self.config.get('budget', {}).get('production_limit', 25.0)
        return self.config.get('budget', {}).get('sample_limit', 1.0)
        
    def check_budget(self, cost: float, is_production: bool = False) -> bool:
        """Check if operation would exceed budget.
        
        Args:
            cost: Cost of the operation
            is_production: Whether this is production generation
            
        Returns:
            True if within budget
            
        Raises:
            BudgetExceededError: If operation would exceed budget
        """
        limit = self.get_budget_limit(is_production)
        if self.total_cost + cost > limit:
            raise BudgetExceededError(
                f"Operation would exceed budget: ${self.total_cost + cost:.2f} > ${limit:.2f}"
            )
        return True
        
    async def execute_with_transaction(
        self,
        asset_type: str,
        cost: float,
        api_call: Callable,
        download_call: Optional[Callable] = None,
        prompt: Optional[str] = None,
        is_production: bool = False,
        max_retries: int = 3
    ) -> Any:
        """Execute an API call with transaction safety.
        
        Args:
            asset_type: Type of asset being generated
            cost: Cost of the operation
            api_call: Async function to call the API
            download_call: Optional async function to download result
            prompt: Prompt used for generation
            is_production: Whether this is production generation
            max_retries: Maximum number of retries
            
        Returns:
            Result from the API call
            
        Raises:
            BudgetExceededError: If budget would be exceeded
            TransactionError: If transaction fails after retries
        """
        # Pre-flight budget check
        self.check_budget(cost, is_production)
        
        # Create transaction record
        transaction = Transaction(
            id=f"{asset_type}_{datetime.now().timestamp()}",
            timestamp=datetime.now().isoformat(),
            asset_type=asset_type,
            cost=cost,
            status='pending',
            prompt=prompt
        )
        
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Log transaction start
                self.logger.info(f"Starting transaction {transaction.id}: ${cost:.2f}")
                
                # Execute API call
                result = await api_call()
                transaction.api_response = result if isinstance(result, dict) else {'output': result}
                
                # Download and verify if download function provided
                if download_call:
                    download_result = await download_call(result)
                    if not download_result:
                        raise TransactionError("Download verification failed")
                        
                # Success - update transaction and cost
                transaction.status = 'success'
                self.total_cost += cost
                self.transactions.append(transaction)
                self._save_transaction_log()
                
                self.logger.info(
                    f"Transaction {transaction.id} successful. "
                    f"Cost: ${cost:.2f}, Total: ${self.total_cost:.2f}"
                )
                
                return result
                
            except Exception as e:
                retry_count += 1
                transaction.retry_count = retry_count
                last_error = str(e)
                
                if retry_count < max_retries:
                    # Exponential backoff
                    wait_time = 2 ** retry_count
                    self.logger.warning(
                        f"Transaction {transaction.id} failed (attempt {retry_count}/{max_retries}): {e}"
                        f" Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Final failure
                    transaction.status = 'failed'
                    transaction.error = last_error
                    self.transactions.append(transaction)
                    self._save_transaction_log()
                    
                    self.logger.error(
                        f"Transaction {transaction.id} failed after {max_retries} attempts: {last_error}"
                    )
                    raise TransactionError(f"Transaction failed after {max_retries} attempts: {last_error}")
                    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """Attempt to rollback a transaction.
        
        Args:
            transaction_id: ID of transaction to rollback
            
        Returns:
            True if rollback successful
            
        Note:
            This is mainly for logging/auditing as API charges usually can't be reversed
        """
        for transaction in self.transactions:
            if (isinstance(transaction, Transaction) and transaction.id == transaction_id) or \
               (isinstance(transaction, dict) and transaction.get('id') == transaction_id):
                if isinstance(transaction, dict):
                    transaction['status'] = 'rolled_back'
                    # Don't deduct cost as API charges are usually non-refundable
                    self.logger.warning(
                        f"Transaction {transaction_id} marked as rolled back. "
                        f"Note: API charges may not be refundable."
                    )
                else:
                    transaction.status = 'rolled_back'
                self._save_transaction_log()
                return True
        return False
        
    def get_transaction_summary(self) -> Dict[str, Any]:
        """Get summary of all transactions.
        
        Returns:
            Dictionary with transaction statistics
        """
        successful = sum(1 for t in self.transactions 
                        if (isinstance(t, dict) and t.get('status') == 'success') or
                           (isinstance(t, Transaction) and t.status == 'success'))
        failed = sum(1 for t in self.transactions 
                    if (isinstance(t, dict) and t.get('status') == 'failed') or
                       (isinstance(t, Transaction) and t.status == 'failed'))
                       
        return {
            'total_cost': self.total_cost,
            'total_transactions': len(self.transactions),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(self.transactions) if self.transactions else 0
        }


class CircuitBreaker:
    """Circuit breaker pattern for API calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
        
    def call_succeeded(self):
        """Record successful call."""
        self.failure_count = 0
        self.state = 'closed'
        
    def call_failed(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            
    def can_attempt_call(self) -> bool:
        """Check if call can be attempted.
        
        Returns:
            True if call can be attempted
        """
        if self.state == 'closed':
            return True
            
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'half-open'
                return True
            return False
            
        # half-open state
        return True
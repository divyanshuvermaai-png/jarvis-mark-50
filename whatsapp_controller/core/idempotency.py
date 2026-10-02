import time

class IdempotencyManager:
    """Prevents duplicate execution of high-risk actions across retries."""
    def __init__(self, expiration_seconds=60):
        self.cache = {}
        self.expiration = expiration_seconds

    def check_and_register(self, op_id: str) -> bool:
        """Returns True if this is a new operation, False if it's a duplicate."""
        now = time.time()
        # Cleanup old entries
        self.cache = {k: v for k, v in self.cache.items() if now - v < self.expiration}
        
        if op_id in self.cache:
            return False
            
        self.cache[op_id] = now
        return True

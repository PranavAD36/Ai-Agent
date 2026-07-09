import os
import logging
from typing import Set

class KeyRedactionFilter(logging.Filter):
    """Logging filter that redacts active API keys from log records."""
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.sensitive_tokens: Set[str] = set()
        self._load_tokens_from_env()

    def _load_tokens_from_env(self):
        # Scan env for keys
        for key, val in os.environ.items():
            if any(term in key.upper() for term in ["API_KEY", "TOKEN", "SECRET"]):
                # Skip short values or placeholders
                if len(val) > 8 and not val.startswith("your_"):
                    self.sensitive_tokens.add(val)
                    # Also register substrings just in case (e.g. prefix)
                    if "_" in val:
                        parts = val.split("_")
                        for part in parts:
                            if len(part) > 10:
                                self.sensitive_tokens.add(part)

    def register_token(self, token: str):
        if token and len(token) > 8 and not token.startswith("your_"):
            self.sensitive_tokens.add(token)

    def filter(self, record: logging.LogRecord) -> bool:
        if not isinstance(record.msg, str):
            return True
            
        message = record.msg
        for token in self.sensitive_tokens:
            if token in message:
                message = message.replace(token, "[REDACTED_API_KEY]")
        
        # Check for typical API key patterns in case they weren't in env
        # e.g., Groq pattern: gsk_[a-zA-Z0-9_]+
        import re
        message = re.sub(r'gsk_[a-zA-Z0-9_]{30,}', '[REDACTED_API_KEY]', message)
        message = re.sub(r'AIzaSy[a-zA-Z0-9_-]{33}', '[REDACTED_API_KEY]', message)
        
        record.msg = message
        return True

# Initialize global logger
logger = logging.getLogger("MultiLLM_Failover")
logger.setLevel(logging.INFO)

# Avoid adding multiple handlers if already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [LLM_FAILOVER] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Apply key redaction filter
redaction_filter = KeyRedactionFilter()
logger.addFilter(redaction_filter)

def register_sensitive_token(token: str):
    """Dynamically register a new sensitive token for redaction."""
    redaction_filter.register_token(token)

# Claude Code Spec-Driven Development

Kiro-style Spec Driven Development implementation using claude code slash commands, hooks and agents.

## Project Context

### Paths
- Steering: `.kiro/steering/`
- Specs: `.kiro/specs/`
- Commands: `.claude/commands/`

### Steering vs Specification

**Steering** (`.kiro/steering/`) - Guide AI with project-wide rules and context
**Specs** (`.kiro/specs/`) - Formalize development process for individual features

### Active Specifications
- **startup-platform**: Kaggle-like startup platform with home page and talent resources (Phase: initialized)
- **company-listing**: Company database with CSV import, filtering, pagination, and detail pages (Phase: initialized)
- **company-reviews**: Company employee review system with 7-criteria rating and search functionality (Phase: initialized)
- **oauth-authentication**: OAuth認証サービス (Google, Facebook, メール認証) with session management (Phase: initialized)
- Check `.kiro/specs/` for active specifications
- Use `/kiro:spec-status [feature-name]` to check progress

## Development Guidelines
- Think in English, but generate responses in Japanese (思考は英語、回答の生成は日本語で行うように)

## Workflow

### Phase 0: Steering (Optional)
`/kiro:steering` - Create/update steering documents
`/kiro:steering-custom` - Create custom steering for specialized contexts

Note: Optional for new features or small additions. You can proceed directly to spec-init.

### Phase 1: Specification Creation
1. `/kiro:spec-init [detailed description]` - Initialize spec with detailed project description
2. `/kiro:spec-requirements [feature]` - Generate requirements document
3. `/kiro:spec-design [feature]` - Interactive: "Have you reviewed requirements.md? [y/N]"
4. `/kiro:spec-tasks [feature]` - Interactive: Confirms both requirements and design review

### Phase 2: Progress Tracking
`/kiro:spec-status [feature]` - Check current progress and phases

## Development Rules
1. **Consider steering**: Run `/kiro:steering` before major development (optional for new features)
2. **Follow 3-phase approval workflow**: Requirements → Design → Tasks → Implementation
3. **Approval required**: Each phase requires human review (interactive prompt or manual)
4. **No skipping phases**: Design requires approved requirements; Tasks require approved design
5. **Update task status**: Mark tasks as completed when working on them
6. **Keep steering current**: Run `/kiro:steering` after significant changes
7. **Check spec compliance**: Use `/kiro:spec-status` to verify alignment

## Steering Configuration

### Current Steering Files
Managed by `/kiro:steering` command. Updates here reflect command changes.

### Active Steering Files
- `product.md`: Always included - Product context and business objectives
- `tech.md`: Always included - Technology stack and architectural decisions
- `structure.md`: Always included - File organization and code patterns

### Custom Steering Files
<!-- Added by /kiro:steering-custom command -->
<!-- Format:
- `filename.md`: Mode - Pattern(s) - Description
  Mode: Always|Conditional|Manual
  Pattern: File patterns for Conditional mode
-->

### Inclusion Modes
- **Always**: Loaded in every interaction (default)
- **Conditional**: Loaded for specific file patterns (e.g., "*.test.js")
- **Manual**: Reference with `@filename.md` syntax

## Code Anti-Patterns

### Exception Handling

#### ❌ Bad Pattern - Silent Exception Suppression
```python
# AI often writes this pattern - DO NOT USE
try:
    result = api_call()
    process_data(result)
except Exception:  # or bare except:
    pass  # Silently ignoring errors
```

#### ✅ Good Pattern - Proper Exception Handling
```python
import logging
logger = logging.getLogger(__name__)

try:
    result = api_call()
    process_data(result)
except APIError as e:
    logger.exception("API呼び出しに失敗: %s", e)
    raise  # Re-raise to not hide errors
except DataProcessingError as e:
    logger.exception("データ処理に失敗: %s", e)
    # Return default value if appropriate
    return default_response()
```

**Key Points:**
- Never use bare `except:` or broad `except Exception:` without proper handling
- Always log exceptions with context
- Use specific exception types when possible
- Re-raise exceptions unless you have a valid reason to suppress them
- Provide meaningful fallback behavior when appropriate

### SQL Injection & Path Manipulation

#### ❌ Bad Pattern - SQL Injection & Unsafe File Operations
```python
import sqlite3

def get_user(name):
    # SQL injection vulnerability
    cur.execute(f"SELECT * FROM users WHERE name='{name}'")

def read_file(filename):
    # Path traversal vulnerability
    return open(f"/uploads/{filename}").read()
```

#### ✅ Good Pattern - Secure Database & File Operations
```python
import sqlite3
from pathlib import Path

def get_user(name):
    # Use parameterized queries to prevent SQL injection
    cur.execute("SELECT * FROM users WHERE name = ?", (name,))

def read_file(filename):
    # Path normalization and directory traversal prevention
    base = Path("uploads").resolve()
    target = (base / Path(filename).name).resolve()

    # Python 3.11+: Strict path validation
    if not target.is_relative_to(base):
        raise ValueError("Invalid path")

    return target.read_text(encoding="utf-8")
```

**Key Points:**
- Always use parameterized queries (`?` placeholders) for SQL statements
- Never use string formatting (`f-strings`, `.format()`, `%`) for SQL queries
- Use `pathlib.Path` for secure file path handling
- Validate file paths are within expected directories using `is_relative_to()`
- Always specify encoding explicitly when reading text files
- Use `Path.name` to strip directory components from user input

### Logging Sensitive Information

#### ❌ Bad Pattern - Exposing Secrets in Logs
```python
# Never log sensitive information
logger.info(f"APIトークン: {token}")
logger.debug(f"パスワード: {password}")
print(f"クレジット情報: {credit_card}")
```

#### ✅ Good Pattern - Safe Logging Practices
```python
# Log successful operations without exposing secrets
logger.info("認証完了")  # No sensitive information
logger.debug("ユーザーID: %s", user.id)  # Only user ID

# For credit cards, show only last 4 digits
logger.info("カード登録: ****%s", card_number[-4:])

# For tokens, log only metadata
logger.info("API認証成功 - スコープ: %s", token_scope)
```

**Key Points:**
- Never log passwords, API tokens, or authentication credentials
- Never log full credit card numbers, SSNs, or other PII
- Log only the minimum information needed for debugging
- Use partial data (last 4 digits) or metadata instead of full values
- Consider using structured logging with sanitization filters
- Always assume logs may be accessed by unauthorized parties

### Datetime & Timezone Handling

#### ❌ Bad Pattern - Naive Datetime Usage
```python
from datetime import datetime, timedelta

# Naive datetime without timezone - causes bugs across timezones
now = datetime.now()
expiry = now + timedelta(days=1)
```

#### ✅ Good Pattern - Timezone-Aware Datetime
```python
from datetime import datetime, timezone, timedelta

# Always use timezone-aware datetime
now = datetime.now(timezone.utc)
expiry = now + timedelta(days=1)

# Store in UTC, convert for display
def format_for_user(utc_time, user_timezone):
    local_time = utc_time.astimezone(user_timezone)
    return local_time.strftime('%Y-%m-%d %H:%M')

# Example usage
from zoneinfo import ZoneInfo  # Python 3.9+

user_tz = ZoneInfo("Asia/Tokyo")
display_time = format_for_user(now, user_tz)
```

**Key Points:**
- Always use timezone-aware datetime objects (`datetime.now(timezone.utc)`)
- Never use naive `datetime.now()` without timezone information
- Store all timestamps in UTC in databases
- Convert to local timezone only for user display
- Use `zoneinfo` (Python 3.9+) or `pytz` for timezone handling
- Test datetime logic across different timezones and DST transitions

### Floating-Point Comparison

#### ❌ Bad Pattern - Direct Float Equality
```python
# Floating-point precision errors cause unexpected behavior
score = 0.1 + 0.1 + 0.1
if score == 0.3:  # May be False due to precision errors
    print("正解")
```

#### ✅ Good Pattern - Safe Float Comparison & Decimal for Money
```python
import math
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Use math.isclose() for float comparison
score = 0.1 + 0.1 + 0.1
if math.isclose(score, 0.3, rel_tol=1e-9):
    print("正解")

# For financial calculations, always use Decimal
getcontext().rounding = ROUND_HALF_UP

price = Decimal('19.99')
tax = Decimal('0.08')
total = price * (1 + tax)

# Example: currency formatting
def format_currency(amount):
    return f"¥{amount:.2f}"

print(format_currency(total))  # ¥21.59
```

**Key Points:**
- Never use `==` or `!=` for floating-point comparisons
- Use `math.isclose()` with appropriate tolerance for float equality
- Always use `Decimal` for financial and monetary calculations
- Set explicit rounding mode with `getcontext().rounding`
- Initialize `Decimal` with strings, not floats: `Decimal('19.99')`
- Consider using specialized libraries like `money` for complex financial logic

### Pandas Chained Assignment

#### ❌ Bad Pattern - Chained Assignment Warning
```python
import pandas as pd

# This triggers SettingWithCopyWarning
df[df.score > 80]['grade'] = 'A'
```

#### ✅ Good Pattern - Safe DataFrame Assignment
```python
import pandas as pd

# Method 1: Use .loc with boolean mask
mask = df.score > 80
df.loc[mask, 'grade'] = 'A'

# Method 2: Explicit copy when working with subset
df_subset = df[df.score > 80].copy()
df_subset['grade'] = 'A'

# Method 3: Direct .loc assignment (most recommended)
df.loc[df.score > 80, 'grade'] = 'A'

# For conditional assignment with multiple conditions
df.loc[(df.score > 80) & (df.attendance > 0.9), 'grade'] = 'A'
df.loc[(df.score >= 60) & (df.score <= 80), 'grade'] = 'B'
df.loc[df.score < 60, 'grade'] = 'F'
```

**Key Points:**
- Never use chained assignment like `df[condition]['column'] = value`
- Always use `.loc[mask, column]` for conditional assignment
- Use explicit `.copy()` when working with DataFrame subsets
- Combine multiple conditions with `&` (and) or `|` (or) operators
- Wrap conditions in parentheses when using multiple operators
- Consider using `pandas.DataFrame.assign()` for method chaining

### Blocking I/O in Async Functions

#### ❌ Bad Pattern - Blocking I/O in Async Function
```python
import requests

async def fetch_data(url):
    # Using blocking I/O defeats the purpose of async
    response = requests.get(url)
    return response.json()
```

#### ✅ Good Pattern - True Async I/O
```python
import httpx
import asyncio
import aiofiles

async def fetch_data(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

# For file operations
async def read_file_async(filepath):
    async with aiofiles.open(filepath, 'r') as file:
        content = await file.read()
        return content

# For database operations (example with asyncpg)
import asyncpg

async def get_user_async(user_id):
    conn = await asyncpg.connect('postgresql://...')
    try:
        result = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        return result
    finally:
        await conn.close()

# Multiple concurrent requests
async def fetch_multiple(urls):
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

**Key Points:**
- Never use blocking libraries (`requests`, `open()`, `time.sleep()`) in async functions
- Use async-compatible libraries: `httpx` instead of `requests`, `aiofiles` instead of `open()`
- Always use `await` with async operations
- Use `asyncio.gather()` for concurrent operations
- Set appropriate timeouts for network operations
- Use async context managers (`async with`) for resource management
- For database access, use async drivers like `asyncpg`, `aiomysql`, or `motor`

### Resource Management & Context Managers

#### ❌ Bad Pattern - Resource Leaks
```python
def process_file(path):
    f = open(path)
    data = f.read()  # Missing f.close() - resource leak
    return data.upper()

# Database connection leak
import sqlite3
def get_user(user_id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()  # Connection never closed
```

#### ✅ Good Pattern - Proper Resource Management
```python
def process_file(path):
    with open(path, encoding="utf-8") as f:
        data = f.read()
    return data.upper()

# Multiple resources
def copy_file(src, dst):
    with open(src, encoding="utf-8") as f_in, \
         open(dst, 'w', encoding="utf-8") as f_out:
        f_out.write(f_in.read())

# Database with context manager
import sqlite3
def get_user(user_id):
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

# Custom context manager
from contextlib import contextmanager
import tempfile
import os

@contextmanager
def temp_file():
    fd, path = tempfile.mkstemp()
    try:
        yield path
    finally:
        os.close(fd)
        os.unlink(path)

# Usage
def process_temp_data(data):
    with temp_file() as tmp_path:
        with open(tmp_path, 'w') as f:
            f.write(data)
        # Process file...
        return result
```

**Key Points:**
- Always use `with` statements for file operations and resource management
- Always specify encoding explicitly: `open(path, encoding="utf-8")`
- Use context managers for database connections, network requests, locks
- Handle multiple resources with comma-separated `with` statements
- Create custom context managers with `@contextmanager` for reusable patterns
- Remember that `with` ensures cleanup even if exceptions occur
- Common resources needing context managers: files, DB connections, locks, temporary files

### Hardcoded Values & Configuration

#### ❌ Bad Pattern - Hardcoded Configuration
```python
# Hardcoded values make code inflexible and insecure
API_URL = "https://api.example.com"
MAX_RETRIES = 3
SECRET_KEY = "abc123"  # Secret exposed in code!
DATABASE_URL = "postgresql://user:pass@localhost:5432/db"

def make_api_call():
    response = requests.get(f"{API_URL}/data", headers={
        "Authorization": f"Bearer {SECRET_KEY}"
    })
    return response.json()
```

#### ✅ Good Pattern - Proper Configuration Management
```python
import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Environment-specific settings with defaults
    api_url: str = "http://localhost:8000"
    max_retries: int = 3
    debug: bool = False

    # Required secrets (no defaults)
    secret_key: str
    database_url: str

    # Optional settings
    redis_url: Optional[str] = None

    class Config:
        env_file = ".env"
        env_prefix = "APP_"  # Environment variables like APP_SECRET_KEY

settings = Settings()

# Alternative: Simple environment variable approach
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
SECRET_KEY = os.getenv("SECRET_KEY")  # Required, will raise error if missing

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

def make_api_call():
    response = requests.get(f"{settings.api_url}/data", headers={
        "Authorization": f"Bearer {settings.secret_key}"
    })
    return response.json()
```

**Example .env file:**
```bash
APP_SECRET_KEY=your-secret-key-here
APP_DATABASE_URL=postgresql://user:pass@localhost:5432/db
APP_API_URL=https://api.production.com
APP_DEBUG=false
```

**Key Points:**
- Never hardcode secrets, API keys, or passwords in source code
- Use environment variables or configuration files for all settings
- Provide sensible defaults for non-sensitive configuration
- Use tools like `pydantic-settings` for type-safe configuration
- Always add `.env` files to `.gitignore`
- Validate required configuration at startup
- Use different configurations for development, staging, and production
- Consider using secret management systems for sensitive data in production

### Hallucinated Functions & Incorrect APIs

#### ❌ Bad Pattern - Non-existent Methods & Wrong Parameters
```python
import pandas as pd
import requests

# These methods/parameters don't exist!
df.save_to_csv("output.csv")  # pandas.DataFrame has no save_to_csv method
requests.get(url, header={"Authorization": token})  # header should be headers
response.get_json()  # requests.Response has no get_json method
os.path.join_path(a, b, c)  # os.path has no join_path method
```

#### ✅ Good Pattern - Correct API Usage
```python
import pandas as pd
import requests
import os

# Correct pandas methods
df.to_csv("output.csv", index=False)
df.to_json("output.json", orient="records")
df.to_excel("output.xlsx", index=False)

# Correct requests parameters
response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
data = response.json()  # Correct method name

# Correct os.path usage
file_path = os.path.join("folder", "subfolder", "file.txt")

# Common correct patterns
import json
with open("data.json", "r") as f:
    data = json.load(f)  # Not json.loads() for files

# SQLAlchemy correct usage
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()  # Not sessionmaker.create_session()

# Flask correct usage
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/api/data", methods=["POST"])
def handle_data():
    data = request.get_json()  # Not request.json()
    return jsonify({"status": "success"})
```

**Key Points:**
- Always verify API method names and parameters in official documentation
- Common mistakes: `header` vs `headers`, `json()` vs `get_json()`, `save_to_csv()` vs `to_csv()`
- Use IDE with autocomplete or check library documentation when unsure
- Test code snippets in a REPL or small script before using in production
- Be especially careful with:
  - Pandas: Use `to_csv()`, `to_json()`, `to_excel()` (not `save_*` methods)
  - Requests: Use `headers` parameter and `response.json()` method
  - OS path operations: Use `os.path.join()` (not `join_path()`)
  - JSON: Use `json.load()` for files, `json.loads()` for strings

### Performance Anti-Patterns

#### ❌ Bad Pattern - Performance Killers
```python
# String concatenation in loop - O(n²) complexity
result = ""
for item in large_list:
    result += str(item)  # Creates new string each time

# Loading entire large file into memory
with open("huge_file.txt") as f:
    lines = f.read().split('\n')  # Memory exhaustion

# Nested loop for matching - O(n²) complexity
matches = []
for a in list1:
    for b in list2:
        if a.id == b.id:
            matches.append((a, b))

# Repeated database queries in loop
users = []
for user_id in user_ids:
    user = db.query(User).filter(User.id == user_id).first()  # N+1 problem
    users.append(user)
```

#### ✅ Good Pattern - Optimized Performance
```python
# Efficient string building
result = "".join(str(item) for item in large_list)

# Alternative for complex string building
from io import StringIO
buffer = StringIO()
for item in large_list:
    buffer.write(str(item))
result = buffer.getvalue()

# Streaming file processing
def process_large_file(filename):
    with open(filename) as f:
        for line in f:  # Process one line at a time
            yield process_line(line.strip())

# Use generator for memory efficiency
processed = list(process_large_file("huge_file.txt"))

# Dictionary lookup for fast matching - O(n) complexity
lookup = {b.id: b for b in list2}
matches = [(a, lookup[a.id]) for a in list1 if a.id in lookup]

# Bulk database queries
users = db.query(User).filter(User.id.in_(user_ids)).all()
user_dict = {user.id: user for user in users}

# List comprehension vs loops (faster)
# Instead of:
squares = []
for x in range(1000):
    squares.append(x**2)

# Use:
squares = [x**2 for x in range(1000)]

# Set operations for fast membership testing
valid_ids = {1, 2, 3, 4, 5}
filtered_items = [item for item in items if item.id in valid_ids]  # O(1) lookup
```

**Key Points:**
- Never use `+=` for string concatenation in loops; use `"".join()` instead
- Use generators and streaming for large files instead of loading everything into memory
- Replace nested loops with dictionary lookups when possible (O(n²) → O(n))
- Avoid N+1 database query problems; use bulk queries with `filter().in_()`
- Use list comprehensions instead of explicit loops for better performance
- Use sets for fast membership testing (O(1) vs O(n) for lists)
- Consider using `itertools` for efficient iteration patterns
- Profile code with `cProfile` to identify actual bottlenecks before optimizing

### Insecure Random Generation

#### ❌ Bad Pattern - Using Predictable Random for Security
```python
import random
import string

# Predictable pseudo-random - vulnerable to attacks
token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
session_id = str(random.randint(100000, 999999))
api_key = random.random()

# Insecure token comparison - timing attack vulnerability
def authenticate(provided_token, expected_token):
    return provided_token == expected_token  # Vulnerable to timing attacks
```

#### ✅ Good Pattern - Cryptographically Secure Random
```python
import secrets
import string
from hmac import compare_digest

# Cryptographically secure random generation
token = secrets.token_urlsafe(32)  # URL-safe base64 encoded
password = secrets.token_hex(16)   # Hexadecimal string
api_key = secrets.token_bytes(32)  # Raw bytes

# Custom character set with secure random
def generate_secure_code(length=8):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Secure token comparison (timing attack resistant)
def authenticate(provided_token, expected_token):
    return compare_digest(provided_token, expected_token)

# Generate secure random numbers
def secure_random_int(min_val, max_val):
    """Generate cryptographically secure random integer"""
    return secrets.randbelow(max_val - min_val + 1) + min_val

# Example usage for session management
class SessionManager:
    def create_session(self, user_id):
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_hex(16)
        return {
            'session_id': session_id,
            'csrf_token': csrf_token,
            'user_id': user_id
        }

    def verify_csrf_token(self, provided_token, stored_token):
        return compare_digest(provided_token, stored_token)

# Secure password salt generation
import hashlib

def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(32)
    hashed = hashlib.pbkdf2_hmac('sha256',
                               password.encode('utf-8'),
                               salt.encode('utf-8'),
                               100000)
    return salt, hashed.hex()
```

**Key Points:**
- Never use `random` module for security-sensitive operations (tokens, passwords, keys)
- Always use `secrets` module for cryptographically secure random generation
- Use `secrets.token_urlsafe()` for URL-safe tokens
- Use `secrets.token_hex()` for hexadecimal tokens
- Use `secrets.token_bytes()` for binary data
- Always use `hmac.compare_digest()` for secure string comparison
- Use `secrets.choice()` instead of `random.choice()` for secure selection
- Generate sufficiently long tokens (minimum 32 bytes for high security)
- Store password salts securely and use strong hashing algorithms like PBKDF2, bcrypt, or Argon2

### Inefficient Logging with F-strings

#### ❌ Bad Pattern - Eager String Formatting in Logs
```python
import logging

logger = logging.getLogger(__name__)

# F-strings always execute formatting, even when logging is disabled
logger.debug(f"ユーザー {user.name} がログインしました")
logger.debug(f"処理時間: {elapsed:.2f}秒")
logger.debug(f"データ: {expensive_computation()}")  # Always computed!

# String concatenation also always executes
logger.info("リクエスト: " + request.method + " " + request.path)
```

#### ✅ Good Pattern - Lazy Logging with Format Strings
```python
import logging

logger = logging.getLogger(__name__)

# Lazy evaluation - formatting only happens if log level is enabled
logger.debug("ユーザー %s がログインしました", user.name)
logger.debug("処理時間: %.2f秒", elapsed)
logger.debug("データ: %s", expensive_computation())  # Only computed if debug enabled

# Multiple arguments
logger.info("リクエスト: %s %s", request.method, request.path)

# Using newer format syntax (also lazy)
logger.info("ユーザー {} がアクション {} を実行", user.name, action)

# Dictionary formatting for structured logging
logger.info(
    "User login attempt",
    extra={
        "user_id": user.id,
        "username": user.name,
        "ip_address": request.remote_addr,
        "success": True
    }
)

# Conditional logging for expensive operations
if logger.isEnabledFor(logging.DEBUG):
    debug_data = expensive_debug_computation()
    logger.debug("Debug data: %s", debug_data)

# Exception logging with context
try:
    risky_operation()
except Exception as e:
    logger.exception("Operation failed for user %s", user.id)
    # Don't use f-strings here either:
    # logger.exception(f"Operation failed for user {user.id}")  # Bad
```

**Performance Comparison:**
```python
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Debug messages won't be shown

def expensive_operation():
    time.sleep(0.1)  # Simulate expensive computation
    return "expensive result"

# Bad - Always executes expensive operation
logger.debug(f"Result: {expensive_operation()}")  # Takes 0.1 seconds even though not logged

# Good - Only executes if debug logging is enabled
logger.debug("Result: %s", expensive_operation())  # Skipped immediately
```

**Key Points:**
- Never use f-strings or string concatenation in logging statements
- Use `%s`, `%d`, `%.2f` format placeholders for lazy evaluation
- Formatting only occurs if the log level is enabled, saving CPU time
- Use `logger.isEnabledFor(level)` for expensive computations before logging
- Use structured logging with `extra` parameter for better log analysis
- Always use `logger.exception()` instead of `logger.error()` when logging exceptions
- Consider using logging libraries like `structlog` for more advanced structured logging


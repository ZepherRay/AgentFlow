"""Server startup script with UTF-8 encoding fix for Windows."""
import sys
import io

# Force UTF-8 encoding for stdout/stderr (fix GBK on Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import uvicorn

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

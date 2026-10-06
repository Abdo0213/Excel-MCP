import os
import re
from typing import Generator, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

try:
    from src.config import settings
except ImportError:
    from config import settings

try:
    from src.mcp_server.server import execute_excel_code
except ImportError:
    from mcp_server.server import execute_excel_code

DEFAULT_SYSTEM_PROMPT = """You are an expert Python data scientist. 
Write ONLY valid Python code to fulfill the user's Excel request.
Use `pandas` and `openpyxl`.

FILE LOCATION RULES:
1. INPUTS: Any dataset or input files to read MUST be loaded from the `inputs/` directory (e.g., `inputs/train_data.csv`, `inputs/dummy_sales_data.xlsx`).
2. OUTPUTS: ALL generated files, modified Excel spreadsheets, CSVs, reports, and plot images MUST ALWAYS be saved inside the `outputs/` directory (e.g., `outputs/result.xlsx`, `outputs/chart.png`). Always ensure the destination directory exists using `os.makedirs('outputs', exist_ok=True)`.

POLISHED EXCEL REQUIREMENTS:
Every generated .xlsx MUST look professionally formatted — never a bare dataframe dump:
- Bold header row with fill color (e.g., dark green #2e8b62, white bold text) and freeze the top row (freeze_panes='A2').
- Auto-adjust column widths to fit content (iterate over columns and set width = max length of cells + 2).
- Apply an alternating or light border/fill table style, and set a consistent font (Calibri 11).
- Apply sensible number formats: currency '$#,##0', dates 'yyyy-mm-dd', percentages '0.0%'.
- Add a title row or sheet title where appropriate, and bold key totals/summary rows.
- Charts must have a title, labeled axes, and tight layout.

DYNAMIC DEPENDENCY INSTALLATION:
If you need any other library (like matplotlib, seaborn, etc.) and you encounter a ModuleNotFoundError, you MUST dynamically install it at the very top of your script using:
```python
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "library_name"])
```
ALWAYS print a short confirmation summary at the end of your script, including the path of every file you created or saved.
Return ONLY python code inside a ```python ``` block."""


class ExcelAgent:
    """Agentic LLM coordinator for Excel and Data analysis tasks with self-healing retry loop."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_retries: Optional[int] = None,
    ):
        self.model = model or settings.ollama_model
        self.api_key = api_key or settings.ollama_api_key
        self.base_url = base_url or settings.ollama_base_url
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.max_retries = max_retries if max_retries is not None else settings.max_retries
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @staticmethod
    def extract_code(response_text: str) -> str:
        """Extract Python code enclosed in markdown fences from the LLM response."""
        code_match = re.search(r"```python\n(.*?)\n```", response_text, re.DOTALL)
        if code_match:
            return code_match.group(1)
        return response_text.replace("```python", "").replace("```", "").strip()

    def run_step_by_step(self, user_prompt: str) -> Generator[Dict[str, Any], None, None]:
        """
        Executes the user prompt using an agentic retry loop.
        Yields state dictionaries at each step for frontend UI or CLI reporting.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(1, self.max_retries + 1):
            yield {
                "type": "attempt_start",
                "attempt": attempt,
                "max_retries": self.max_retries,
            }

            # 1. Code Generation
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                response_text = response.choices[0].message.content or ""
                python_code = self.extract_code(response_text)
                messages.append({"role": "assistant", "content": response_text})

                yield {
                    "type": "code_generated",
                    "attempt": attempt,
                    "code": python_code,
                }
            except Exception as e:
                yield {
                    "type": "generation_error",
                    "attempt": attempt,
                    "error": str(e),
                }
                return

            # 2. Code Execution via MCP Server
            try:
                output = execute_excel_code(python_code=python_code)
                is_error = "Error during execution:" in output

                if is_error:
                    yield {
                        "type": "execution_failed",
                        "attempt": attempt,
                        "output": output,
                    }
                    # Prepare error feedback for the LLM in next iteration
                    error_feedback = (
                        f"The execution failed with the following error:\n{output}\n"
                        f"Please analyze the error, fix the code, and return the FULL updated Python script inside a ```python ``` block. "
                        f"If it's a ModuleNotFoundError, remember to pip install it via subprocess at the top of the script."
                    )
                    messages.append({"role": "user", "content": error_feedback})
                else:
                    yield {
                        "type": "execution_success",
                        "attempt": attempt,
                        "output": output,
                    }
                    return

            except Exception as e:
                yield {
                    "type": "mcp_error",
                    "attempt": attempt,
                    "error": str(e),
                }
                return

        yield {
            "type": "all_retries_exhausted",
            "max_retries": self.max_retries,
        }

    def run(self, user_prompt: str) -> Dict[str, Any]:
        """Synchronous helper for single-call execution."""
        last_event = {}
        for event in self.run_step_by_step(user_prompt):
            last_event = event
        return last_event

"""CLI interface for running the SheetPT without the Streamlit UI."""
import os
import sys
import argparse
from dotenv import load_dotenv

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.config import settings
except ImportError:
    from config import settings

try:
    from src.agent.excel_agent import ExcelAgent
except ImportError:
    from agent.excel_agent import ExcelAgent


def main():
    parser = argparse.ArgumentParser(description="SheetPT CLI")
    parser.add_argument(
        "--prompt",
        "-p",
        type=str,
        default="Create an excel file in outputs/cloud_demo.xlsx with two columns 'Item' and 'Price'. Add 3 items and save.",
        help="The natural language prompt to execute.",
    )
    parser.add_argument(
        "--retries",
        "-r",
        type=int,
        default=settings.max_retries,
        help="Maximum self-healing retries upon error.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("🤖 EXCEL ANALYST AGENT (CLI RUNNER)")
    print("=" * 60)
    print(f"User Request: {args.prompt}\n")

    agent = ExcelAgent(max_retries=args.retries)

    for event in agent.run_step_by_step(args.prompt):
        event_type = event.get("type")
        attempt = event.get("attempt", 1)

        if event_type == "attempt_start":
            print(f"--- [Attempt {attempt}/{event.get('max_retries')}] Generating code with LLM... ---")

        elif event_type == "code_generated":
            print("\n--- GENERATED CODE ---")
            print(event.get("code", "").strip())
            print("----------------------\n")
            print("Passing code to MCP Server for execution...")

        elif event_type == "generation_error":
            print(f"❌ Error during code generation: {event.get('error')}")
            break

        elif event_type == "execution_failed":
            print(f"⚠️ Execution failed on attempt {attempt}:")
            print(event.get("output", "").strip())
            print("\nFeeding error log back to LLM for self-correction...\n")

        elif event_type == "mcp_error":
            print(f"❌ MCP Server Error: {event.get('error')}")
            break

        elif event_type == "execution_success":
            print("\n" + "=" * 60)
            print(f"✅ SUCCESS on Attempt {attempt}!")
            print("=" * 60)
            print("MCP Server Output:")
            print(event.get("output", "").strip())
            print("=" * 60)
            break

        elif event_type == "all_retries_exhausted":
            print(f"\n❌ Failed to resolve errors after {event.get('max_retries')} attempts.")


if __name__ == "__main__":
    main()

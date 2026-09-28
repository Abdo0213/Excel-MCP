import os
import re
from dotenv import load_dotenv
from openai import OpenAI

# We import the MCP tool directly for demonstration
from server import execute_excel_code

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "dummy")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/v1")

client = OpenAI(
    api_key=OLLAMA_API_KEY,
    base_url=OLLAMA_BASE_URL,
)

SYSTEM_PROMPT = """You are an expert Python data scientist. 
Write ONLY valid Python code to fulfill the user's Excel request.
Use `pandas` and `openpyxl`.
Return ONLY python code inside a ```python ``` block."""

def main():
    print("Agent: Waiting for user input...")
    user_prompt = "Create an excel file named 'cloud_demo.xlsx' with two columns 'Item' and 'Price'. Add 3 random items and save."
    print(f"User: {user_prompt}")
    
    print("\nAgent: Asking Ollama Cloud to generate code...")
    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        response_text = response.choices[0].message.content
        
        code_match = re.search(r'```python\n(.*?)\n```', response_text, re.DOTALL)
        if code_match:
            python_code = code_match.group(1)
        else:
            python_code = response_text.replace('```python', '').replace('```', '').strip()
            
        print("\n=== GENERATED CODE FROM AGENT ===")
        print(python_code)
        print("=================================\n")
        
        print("Agent: Passing code to MCP Server (execute_excel_code)...")
        
        output = execute_excel_code(python_code=python_code)
        
        print("\n=== MCP SERVER OUTPUT ===")
        print(output.strip())
        print("=========================\n")
        
        if os.path.exists("cloud_demo.xlsx"):
            print("Success! File 'cloud_demo.xlsx' was successfully created by the MCP server!")
            
    except Exception as e:
        print(f"\nAgent: Error during code generation/execution - {e}")

if __name__ == "__main__":
    main()

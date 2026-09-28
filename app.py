import os
import re
import sys
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# We import the MCP tool directly for demonstration
from server import execute_excel_code

# Load environment variables
load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "dummy")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/v1")

# Initialize OpenAI client for Ollama Cloud
client = OpenAI(
    api_key=OLLAMA_API_KEY,
    base_url=OLLAMA_BASE_URL,
)

SYSTEM_PROMPT = """You are an expert Python data scientist. 
Write ONLY valid Python code to fulfill the user's Excel request.
Use `pandas` and `openpyxl`.
If you need any other library (like matplotlib, seaborn, etc.) and you encounter a ModuleNotFoundError, you MUST dynamically install it at the very top of your script using:
```python
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "library_name"])
```
Return ONLY python code inside a ```python ``` block."""

# Streamlit App UI
st.set_page_config(page_title="Excel Analyst Agent", page_icon="📊", layout="centered")

st.title("📊 Excel Analyst Agent")
st.markdown("Enter a natural language request below. The agent will generate the Python code, execute it, and **automatically retry and debug itself** if it encounters any errors (like missing libraries).")

MAX_RETRIES = 3

user_prompt = st.text_area("What would you like to do?", height=100, placeholder="Create an excel file with random data, plot it with matplotlib, and save the plot.")

if st.button("Run Task", type="primary"):
    if not user_prompt.strip():
        st.warning("Please enter a prompt first.")
    else:
        
        # Message history array to maintain context during retries
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        success = False
        
        for attempt in range(1, MAX_RETRIES + 1):
            st.markdown(f"### Attempt {attempt} / {MAX_RETRIES}")
            
            with st.spinner("🤖 Agent is analyzing and generating code..."):
                try:
                    response = client.chat.completions.create(
                        model=OLLAMA_MODEL,
                        messages=messages
                    )
                    
                    response_text = response.choices[0].message.content
                    
                    # Extract Python code
                    code_match = re.search(r'```python\n(.*?)\n```', response_text, re.DOTALL)
                    if code_match:
                        python_code = code_match.group(1)
                    else:
                        python_code = response_text.replace('```python', '').replace('```', '').strip()
                        
                    # Add agent's response to history
                    messages.append({"role": "assistant", "content": response_text})
                    
                    with st.expander(f"View Generated Code (Attempt {attempt})", expanded=False):
                        st.code(python_code, language="python")
                        
                except Exception as e:
                    st.error(f"❌ Error during code generation: {e}")
                    st.stop()
                    
            with st.spinner("⚙️ Executing code in MCP Server..."):
                try:
                    output = execute_excel_code(python_code=python_code)
                    
                    if "Error during execution:" in output:
                        st.error("Execution failed. Agent is analyzing the error for the next attempt...")
                        with st.expander("View Error Log"):
                            st.code(output)
                        
                        # Feed the error back to the LLM
                        error_feedback = f"The execution failed with the following error:\n{output}\nPlease analyze the error, fix the code, and return the FULL updated Python script inside a ```python ``` block. If it's a ModuleNotFoundError, remember to pip install it via subprocess at the top of the script."
                        messages.append({"role": "user", "content": error_feedback})
                    else:
                        st.success("Execution completed successfully!")
                        st.markdown("### MCP Server Output")
                        st.info(output)
                        st.balloons()
                        success = True
                        break # Break out of the retry loop
                        
                except Exception as e:
                    st.error(f"❌ Critical error communicating with MCP Server: {e}")
                    st.stop()
                    
        if not success:
            st.error(f"Agent failed to resolve the issue after {MAX_RETRIES} attempts. Please review the errors above and try modifying your prompt.")

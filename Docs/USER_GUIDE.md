# User & Setup Guide

## 1. Prerequisites & Virtual Environment

Ensure you have **Python 3.10+** installed.

Activate your virtual environment and install dependencies:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## 2. Configuration (`.env`)

Configure your `.env` file in the project root:

```env
OLLAMA_MODEL=llama3.1
OLLAMA_API_KEY=your_ollama_api_key_here
OLLAMA_BASE_URL=https://ollama.com/v1
```

---

## 3. Running the Application

### Option A: Streamlit Web UI (Frontend)
Run the isolated Streamlit frontend:

```powershell
python -m streamlit run src/frontend/app.py
```
*(Or `python -m streamlit run src/app.py`)*

Open `http://localhost:8501` in your browser.

### Option B: Structured CLI Agent
Run the command-line agent with custom prompts:

```powershell
python src/cli_agent.py --prompt "Read inputs/train_data.csv and calculate average age by class"
```

---

## 4. Working with Inputs and Outputs

- **File Upload via UI**: You can upload `.csv`, `.xlsx`, `.xls`, `.json`, or `.parquet` files directly from the Streamlit UI. They are saved automatically to `inputs/` and a 5-row preview is shown.
- **Input Datasets (`inputs/`)**: All datasets uploaded or manually placed in `inputs/` can be directly referenced in user prompts (e.g., `inputs/my_data.csv`).
- **Generated Outputs (`outputs/`)**: All generated spreadsheets, charts, and EDA reports are automatically written into `outputs/` by the agent.

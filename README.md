# Excel Analyst Agent (MCP Server & Streamlit UI)

## Overview
This project is an **Agentic Excel Analyst** that takes natural language requests from users, dynamically generates Python code to fulfill those requests (using pandas, openpyxl, matplotlib, etc.), and securely executes the code locally using an MCP (Model Context Protocol) Server architecture. 

It features a modular **Streamlit Web UI**, an isolated **Agent Core**, and an **Agentic Retry Loop** that allows the agent to self-correct and install missing libraries automatically if an execution error occurs.

---

## Project Structure

```
.
├── Docs/                     # Documentation & technical guides
│   ├── ARCHITECTURE.md
│   └── USER_GUIDE.md
├── inputs/                   # Input datasets (CSV, Excel)
│   ├── dummy_sales_data.xlsx
│   ├── test_data.csv
│   ├── train_data.csv
│   └── train_data_cleaned.csv
├── outputs/                  # Generated files and analysis plots
│   ├── boda.xlsx
│   ├── cloud_demo.xlsx
│   ├── titanic_eda_report.xlsx
│   └── eda_plots/
│       ├── age_distribution.png
│       ├── correlation_heatmap.png
│       ├── survival_by_sex.png
│       └── survival_count.png
├── src/                      # Source code root
│   ├── __init__.py
│   ├── config.py             # Pydantic Settings & schema configuration
│   ├── app.py                # Main web application entry point
│   ├── cli_agent.py          # Structured CLI Agent runner
│   ├── agent/                # Agent Core package (LLM & retry logic)
│   │   ├── __init__.py
│   │   └── excel_agent.py    # ExcelAgent class & self-healing generator
│   ├── frontend/             # Dedicated UI module
│   │   ├── __init__.py
│   │   └── app.py            # Streamlit dashboard
│   └── mcp_server/           # MCP Server package
│       ├── __init__.py
│       └── server.py         # MCP execution server & tools
├── .env                      # Environment variables
├── .gitignore
├── README.md
└── requirements.txt
```

---

## System Architecture

```mermaid
graph TD
    classDef userNode fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef uiNode fill:#e7f5ff,stroke:#1864ab,stroke-width:2px;
    classDef agentNode fill:#d1e7dd,stroke:#0f5132,stroke-width:2px;
    classDef mcpNode fill:#cfe2ff,stroke:#084298,stroke-width:2px;
    classDef internalNode fill:#fff3cd,stroke:#664d03,stroke-width:1px;
    classDef cloudNode fill:#e2e3e5,stroke:#41464b,stroke-width:1px;

    User(["User"]):::userNode
    StreamlitUI["Frontend UI (src/frontend/app.py)"]:::uiNode
    CLI["CLI Agent (src/cli_agent.py)"]:::uiNode
    AgentCore["Agent Core (src/agent/excel_agent.py)"]:::agentNode
    OllamaCloud[("Ollama Cloud API")]:::cloudNode
    
    subgraph MCP_Server ["MCP Server Environment (src/mcp_server)"]
        SingleTool{"Tool: execute_excel_code"}:::mcpNode
        InputsDir[("inputs/")]:::internalNode
        OutputsDir[("outputs/")]:::internalNode
    end
    
    User -->|Web Prompt| StreamlitUI
    User -->|CLI Flag| CLI
    StreamlitUI --> AgentCore
    CLI --> AgentCore
    AgentCore -->|1. Request Code| OllamaCloud
    OllamaCloud -.->|2. Return Python Script| AgentCore
    AgentCore -->|3. Dispatch Code| SingleTool
    SingleTool -->|4. Read Data| InputsDir
    SingleTool -->|5. Write Outputs| OutputsDir
    SingleTool -.->|6. Result / Stdout| AgentCore
    
    AgentCore -.->|7. If Error: Self-Correct| OllamaCloud
    AgentCore -->|8. Stream Events| StreamlitUI
    AgentCore -->|8. Stream Events| CLI
```

---

## How to Run

### 1. Launch the Frontend Web UI:
```powershell
python -m streamlit run src/frontend/app.py
```
*(Or `python -m streamlit run src/app.py`)*

### 2. Launch the CLI Agent:
```powershell
python src/cli_agent.py --prompt "Read inputs/train_data.csv and summarize missing values"
```

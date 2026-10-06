# System Architecture & Design

## Overview
The **Excel Analyst Agent** is an agentic AI system designed to understand natural language instructions, generate executable Python code for Excel/Data manipulation, and execute that code in an isolated MCP (Model Context Protocol) Server environment with autonomous self-healing capabilities.

---

## Directory Structure

```
.
├── Docs/                     # Documentation and architectural guides
│   ├── ARCHITECTURE.md       # Detailed technical architecture
│   └── USER_GUIDE.md         # Setup and usage instructions
├── inputs/                   # Raw input datasets (CSVs, Excel files)
│   ├── dummy_sales_data.xlsx
│   ├── test_data.csv
│   ├── train_data.csv
│   └── train_data_cleaned.csv
├── outputs/                  # Agent-generated Excel files, EDA reports, and charts
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
│   ├── config.py             # Pydantic Settings & Environment schema
│   ├── app.py                # App entrypoint
│   ├── cli_agent.py          # Standalone CLI Agent runner
│   ├── agent/                # Core Agent package (LLM & retry logic)
│   │   ├── __init__.py
│   │   └── excel_agent.py    # ExcelAgent class & self-healing generator
│   ├── frontend/             # Frontend UI package (Streamlit)
│   │   ├── __init__.py
│   │   └── app.py            # Streamlit dashboard implementation
│   └── mcp_server/           # MCP Server package
│       ├── __init__.py
│       └── server.py         # MCP execution server and tools
├── .env                      # API keys and environment variables
├── .gitignore                # Git ignore configuration
├── README.md                 # Project root documentation
└── requirements.txt          # Python dependencies
```

---

## Component Architecture

```mermaid
graph TD
    classDef userNode fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef uiNode fill:#e7f5ff,stroke:#1864ab,stroke-width:2px;
    classDef agentNode fill:#d1e7dd,stroke:#0f5132,stroke-width:2px;
    classDef mcpNode fill:#cfe2ff,stroke:#084298,stroke-width:2px;
    classDef internalNode fill:#fff3cd,stroke:#664d03,stroke-width:1px;
    classDef cloudNode fill:#e2e3e5,stroke:#41464b,stroke-width:1px;

    User((User)):::userNode
    StreamlitUI[Frontend UI\nsrc/frontend/app.py]:::uiNode
    CLI[CLI Agent\nsrc/cli_agent.py]:::uiNode
    AgentCore[Agent Core\nsrc/agent/excel_agent.py]:::agentNode
    OllamaCloud[(Ollama Cloud API\ne.g. Llama 3.1)]:::cloudNode
    
    subgraph MCP_Server [MCP Server Environment (src/mcp_server)]
        SingleTool{Tool: execute_excel_code}:::mcpNode
        InputsDir[(inputs/)]:::internalNode
        OutputsDir[(outputs/)]:::internalNode
    end
    
    User -->|Web Prompt| StreamlitUI
    User -->|CLI Command| CLI
    StreamlitUI --> AgentCore
    CLI --> AgentCore
    AgentCore -->|1. Generate Code| OllamaCloud
    OllamaCloud -.->|2. Return Python Script| AgentCore
    AgentCore -->|3. Dispatch Code| SingleTool
    SingleTool -->|4. Read Data| InputsDir
    SingleTool -->|5. Save Results / Plots| OutputsDir
    SingleTool -.->|6. Stdout / Execution Log| AgentCore
    
    AgentCore -.->|7. Self-Correction Loop on Error| OllamaCloud
    AgentCore -->|8. Stream Step Events| StreamlitUI
    AgentCore -->|8. Stream Step Events| CLI
```

---

## Key Modules

### 1. `src/agent/excel_agent.py`
- Holds all agentic orchestration, LLM calling, system prompting, regex code extraction, and dynamic self-healing retry logic.
- Yields step-by-step events for real-time visualization in both UI and CLI.

### 2. `src/frontend/app.py`
- Modular Streamlit frontend completely decoupled from agent business logic.
- Displays dynamic retry attempts, code preview expanders, error logs, and dataset explorers.

### 3. `src/cli_agent.py`
- Structured command-line tool allowing execution without running the web browser.

### 4. `src/mcp_server/server.py`
- Decoupled MCP tool execution environment exposing `execute_excel_code`.

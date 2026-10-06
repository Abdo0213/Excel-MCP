import os
import sys
import pandas as pd
import streamlit as st

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
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


def get_input_files():
    """List files in the inputs/ directory."""
    if settings.inputs_dir.exists():
        return [f.name for f in settings.inputs_dir.iterdir() if not f.name.startswith(".")]
    return []


def get_output_files():
    """List files in the outputs/ directory."""
    if settings.outputs_dir.exists():
        return [f.name for f in settings.outputs_dir.iterdir() if not f.name.startswith(".")]
    return []


def main():
    st.set_page_config(
        page_title="Excel Analyst Agent",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    settings.ensure_directories()

    # Sidebar: Configurations & File Explorer
    with st.sidebar:
        st.header("⚙️ Agent Settings")
        model = st.text_input("Model Name", value=settings.ollama_model)
        max_retries = st.slider("Max Self-Healing Retries", min_value=1, max_value=5, value=settings.max_retries)

        st.divider()
        st.subheader("📂 Available Input Files")
        input_files = get_input_files()
        if input_files:
            for f in input_files:
                st.code(f"inputs/{f}", language="text")
        else:
            st.caption("No files currently in `inputs/`.")

        st.divider()
        st.subheader("📁 Output Files")
        output_files = get_output_files()
        if output_files:
            for f in output_files:
                st.code(f"outputs/{f}", language="text")
        else:
            st.caption("No generated files in `outputs/` yet.")

    # Main Area
    st.title("📊 Excel Analyst Agent")
    st.markdown(
        "Upload your datasets, describe your analysis or modifications in natural language, "
        "and watch the agent generate, execute, and self-heal Python code in the **MCP Server**."
    )

    # 📤 File Upload Section
    with st.expander("📤 Upload Dataset to `inputs/`", expanded=True):
        uploaded_file = st.file_uploader(
            "Choose a dataset to save to `inputs/`",
            type=["csv", "xlsx", "xls", "json", "parquet"],
            help="Uploaded files are automatically saved to the inputs/ directory and available for the agent.",
        )

        if uploaded_file is not None:
            saved_file_path = settings.inputs_dir / uploaded_file.name
            
            # Save uploaded file
            with open(saved_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"✅ Saved **{uploaded_file.name}** to `inputs/{uploaded_file.name}`")

            # Quick Dataset Preview
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_preview = pd.read_csv(saved_file_path, nrows=5)
                    st.caption("📊 Dataset Preview (First 5 rows):")
                    st.dataframe(df_preview, use_container_width=True)
                elif uploaded_file.name.endswith((".xlsx", ".xls")):
                    df_preview = pd.read_excel(saved_file_path, nrows=5)
                    st.caption("📊 Dataset Preview (First 5 rows):")
                    st.dataframe(df_preview, use_container_width=True)
            except Exception as e:
                st.caption(f"Preview unavailable: {e}")

    # Prompt Section
    user_prompt = st.text_area(
        "What data task would you like to perform?",
        height=120,
        placeholder="Example: Load inputs/train_data.csv, compute survival rate by Sex and Pclass, save the table in outputs/titanic_analysis.xlsx, and plot a chart in outputs/eda_plots/survival.png",
    )

    if st.button("🚀 Run Task", type="primary", use_container_width=True):
        if not user_prompt.strip():
            st.warning("Please enter a prompt first.")
            return

        agent = ExcelAgent(model=model, max_retries=max_retries)
        success = False

        status_container = st.container()

        with status_container:
            for event in agent.run_step_by_step(user_prompt):
                event_type = event.get("type")
                attempt = event.get("attempt", 1)

                if event_type == "attempt_start":
                    st.markdown(f"### 🔄 Attempt {attempt} of {event.get('max_retries')}")

                elif event_type == "code_generated":
                    with st.expander(f"📝 Generated Python Code (Attempt {attempt})", expanded=False):
                        st.code(event.get("code", ""), language="python")

                elif event_type == "generation_error":
                    st.error(f"❌ Error during code generation: {event.get('error')}")
                    break

                elif event_type == "execution_failed":
                    st.warning(f"⚠️ Execution encountered an error on Attempt {attempt}. Passing error log back to agent...")
                    with st.expander(f"⚠️ Error Traceback (Attempt {attempt})", expanded=False):
                        st.code(event.get("output", ""))

                elif event_type == "mcp_error":
                    st.error(f"❌ MCP Server Communication Error: {event.get('error')}")
                    break

                elif event_type == "execution_success":
                    st.success(f"✅ Execution completed successfully on Attempt {attempt}!")
                    st.markdown("#### 📋 MCP Server Output")
                    st.info(event.get("output", ""))
                    st.balloons()
                    success = True
                    break

                elif event_type == "all_retries_exhausted":
                    st.error(f"❌ Agent could not resolve execution errors after {event.get('max_retries')} attempts.")

        if not success and event_type != "execution_success":
            st.info("💡 Tip: Try adjusting your prompt or verifying the input file paths.")


if __name__ == "__main__":
    main()

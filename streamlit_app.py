import streamlit as st
from openai import OpenAI
import sympy as sp
import sys
import io

# Page settings
st.set_page_config(page_title="Banach Logic Agent", page_icon="🧠")
st.title("🧠 Banach Space Logic Agent")
st.write("Powered by `o3-mini` reasoning and `SymPy` symbolic execution.")

# Initialize OpenAI Client
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing OpenAI API Key in Streamlit Secrets!", icon="🚨")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Tool: Controlled Python Execution Sandbox for SymPy
def execute_symbolic_math(code_string):
    """Executes code using SymPy and returns stdout string safely."""
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    # Expose math components safely into local environment
    local_env = {"sp": sp, "sympy": sp}
    try:
        # Execute the python script requested by the agent
        exec(code_string, {}, local_env)
        sys.stdout = old_stdout
        return redirected_output.getvalue()
    except Exception as e:
        sys.stdout = old_stdout
        return f"Execution Error: {str(e)}"

# Guardrail and operational prompts combined
BANACH_DEVELOPER_PROMPT = (
    "You are an elite reasoning agent specializing in Banach Space Theory and Functional Analysis.\n"
    "CRITICAL GUARDRAIL: You must strictly only answer questions within this domain. If a user asks "
    "about cooking, generic web development, sports, etc., politely refuse to answer.\n\n"
    "AXIOMATIC REASONING: You must think step-by-step through axioms, properties (reflexivity, completeness, norms), "
    "and major theorems (Hahn-Banach, Open Mapping).\n\n"
    "MATHEMATICAL TOOL RIGOR: If the user requires concrete matrix equations, finite-dimensional calculations, "
    "polynomial expansions, or symbolic algebraic checks within a space, you should write a short snippet using the 'sympy' library "
    "and explain what needs to be verified."
)

# Initialize Session History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "developer", "content": BANACH_DEVELOPER_PROMPT}
    ]

# Display history
for msg in st.session_state.messages:
    if msg["role"] not in ["developer", "system"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# Handle Chat Input
if user_query := st.chat_input("Ask a proof, theorem, or symbolic question..."):
    with st.chat_message("user"):
        st.write(user_query)
    
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # o3-mini uses reasoning_effort to handle internal chain-of-thought logic
            stream = client.chat.completions.create(
                model="o3-mini",
                messages=st.session_state.messages,
                reasoning_effort="medium", 
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.write(full_response + "▌")
            
            response_placeholder.write(full_response)
            
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            st.stop()
            
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Sidebar Tool UI: Allows the user or agent to test symbolic logic live via SymPy
st.sidebar.header("🧮 Live Symbolic Math Engine")
st.sidebar.write("Verify finite-dimensional operator representations or functions using SymPy here:")
sample_code = """import sympy as sp
x = sp.Symbol('x')
# Check if a function is normalized or integrate over a bound
f = sp.exp(-x)
integral = sp.integrate(f, (x, 0, sp.oo))
print(f"Integral value: {integral}")
"""
user_code = st.sidebar.text_area("SymPy Code Sandbox:", value=sample_code, height=180)
if st.sidebar.button("Run Symbolic Engine"):
    result = execute_symbolic_math(user_code)
    st.sidebar.code(result if result.strip() else "Code executed successfully with no print output.")

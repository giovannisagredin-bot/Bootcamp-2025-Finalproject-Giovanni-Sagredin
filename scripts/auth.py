import os
import json
import streamlit as st  # type: ignore[import-not-found]
import requests
from typing import Optional
import google.auth
import google.auth.transport.requests
from google.oauth2 import id_token

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")  # "local" or "production"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
IS_LOCAL = ENVIRONMENT == "local"

def get_gcp_identity_token() -> Optional[str]:
    """Get GCP identity token for Cloud Run authentication using gcloud."""
    # Skip GCP auth in local environment
    if IS_LOCAL:
        return None

    try:
        import subprocess

        # Use gcloud to get identity token directly
        result = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            token = result.stdout.strip()
            return token
        else:
            error_msg = result.stderr.strip()
            st.error(f"⚠️ GCP Auth Error: {error_msg}")
            st.info("Run: gcloud auth login")
            return None

    except FileNotFoundError:
        st.error("⚠️ gcloud CLI not found. Install Google Cloud SDK.")
        return None
    except Exception as e:
        st.error(f"⚠️ GCP Authentication Error: {e}")
        st.info("Run: gcloud auth login")
        return None

providers = ["mock", "google", "openai", "deepseek"]

st.set_page_config(
    page_title="Trading Chat - Login",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "message_count" not in st.session_state:
    st.session_state.message_count = 0
if "feedback_sent" not in st.session_state:
    st.session_state.feedback_sent = False
if "show_feedback_prompt" not in st.session_state:
    st.session_state.show_feedback_prompt = False


def api_get(endpoint: str, params: Optional[dict] = None, headers: Optional[dict] = None) -> Optional[dict]:
    """Make GET request to API"""
    try:
        if headers is None:
            headers = {}

        # Add app auth token as Bearer token (backend expects this format)
        if st.session_state.auth_token:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        # For production: also add GCP Identity Token if available
        elif not IS_LOCAL:
            gcp_token = get_gcp_identity_token()
            if gcp_token:
                headers["Authorization"] = f"Bearer {gcp_token}"

        response = requests.get(f"{API_BASE_URL}{endpoint}", params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_data = response.json()
            error_msg = error_data.get("detail", str(e))
            st.error(error_msg)
        except Exception:
            st.error(f"API Error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return None


def api_post(endpoint: str, json_data: dict, headers: Optional[dict] = None) -> Optional[dict]:
    """Make POST request to API"""
    try:
        if headers is None:
            headers = {}

        # Add app auth token as Bearer token (backend expects this format)
        if st.session_state.auth_token:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        # For production: also add GCP Identity Token if available
        elif not IS_LOCAL:
            gcp_token = get_gcp_identity_token()
            if gcp_token:
                headers["Authorization"] = f"Bearer {gcp_token}"

        response = requests.post(f"{API_BASE_URL}{endpoint}", json=json_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_data = response.json()
            error_msg = error_data.get("detail", str(e))
            st.error(error_msg)
        except Exception:
            st.error(f"API Error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return None


def api_delete(endpoint: str, json_data: Optional[dict] = None, headers: Optional[dict] = None) -> Optional[dict]:
    """Make DELETE request to API"""
    try:
        if headers is None:
            headers = {}

        # Add app auth token as Bearer token (backend expects this format)
        if st.session_state.auth_token:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        # For production: also add GCP Identity Token if available
        elif not IS_LOCAL:
            gcp_token = get_gcp_identity_token()
            if gcp_token:
                headers["Authorization"] = f"Bearer {gcp_token}"

        response = requests.delete(f"{API_BASE_URL}{endpoint}", json=json_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_data = response.json()
            error_msg = error_data.get("detail", str(e))
            st.error(error_msg)
        except Exception:
            st.error(f"API Error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return None

def api_put(endpoint: str, json_data: dict, headers: Optional[dict] = None) -> Optional[dict]:
    """Make PUT request to API"""
    try:
        if headers is None:
            headers = {}

        # Add app auth token as Bearer token (backend expects this format)
        if st.session_state.auth_token:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        # For production: also add GCP Identity Token if available
        elif not IS_LOCAL:
            gcp_token = get_gcp_identity_token()
            if gcp_token:
                headers["Authorization"] = f"Bearer {gcp_token}"

        response = requests.put(f"{API_BASE_URL}{endpoint}", json=json_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_data = response.json()
            error_msg = error_data.get("detail", str(e))
            st.error(error_msg)
        except Exception:
            st.error(f"API Error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return None


def login(email: str, notion_token: str, notion_database_id: str) -> bool:
    """Login user and store auth token"""
    data = {
        "email": email,
        "notion_token": notion_token,
        "notion_database_id": notion_database_id
    }

    result = api_post("/v1/auth/login", data)
    if result:
        st.session_state.auth_token = result["auth_token"]
        st.session_state.user_info = {
            "user_id": result["user_id"],
            "email": result["email"]
        }
        return True
    return False


def logout():
    """Logout user and clear session"""
    if st.session_state.auth_token:
        api_post("/v1/auth/logout", {})

    st.session_state.auth_token = None
    st.session_state.user_info = None
    st.session_state.messages = []
    st.session_state.active_session_id = None


# Check if user is logged in
if not st.session_state.auth_token:
    # Login Page
    st.title("🔐 Trading Chat - Login")
    st.markdown("**Existing users:** Login with just your email")
    st.markdown("**New users:** Expand the Notion credentials section below")

    with st.form("login_form"):
        st.markdown("### Your Credentials")

        email = st.text_input(
            "Email",
            placeholder="your.email@example.com",
            help="Your email address"
        )

        st.markdown("---")
        st.markdown("**First time?** Expand below to add Notion credentials:")

        with st.expander("➕ Notion Credentials (required for new users)", expanded=False):
            st.caption("If you've already registered, leave these empty to login with just your email")

            notion_token = st.text_input(
                "Notion Integration Token",
                type="password",
                placeholder="secret_... (optional for existing users)",
                help="Your Notion internal integration token (starts with secret_)"
            )

            notion_database_id = st.text_input(
                "Notion Database ID",
                placeholder="2865afdc4c2b8... (optional for existing users)",
                help="Your Notion trading database ID (32 character UUID)"
            )

        submit = st.form_submit_button("🚀 Login")

    if submit:
        if not email:
            st.error("Please enter your email")
        else:
            with st.spinner("Logging in..."):
                # Pass empty strings as None
                assert(notion_token is not None)
                token = notion_token
                assert(notion_database_id is not None)
                db_id = notion_database_id if notion_database_id else ""

                if login(email, token, db_id):
                    st.success("✅ Login successful! Redirecting to chat...")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Login failed. If you're a new user, please provide Notion credentials.")

    # Help section
    st.markdown("---")
    st.markdown("### 🤔 How to get your Notion credentials?")

    with st.expander("📖 Step-by-step guide"):
        st.markdown("""
        **1. Create a Notion Integration:**
        - Go to [Notion Integrations](https://www.notion.so/my-integrations)
        - Click "New integration"
        - Give it a name (e.g., "Trading Chat")
        - Copy the **Internal Integration Token** (starts with `secret_`)

        **2. Share your database with the integration:**
        - Open your Notion trading database
        - Click the three dots (•••) in the top right
        - Select "Add connections"
        - Find and select your integration

        **3. Get your Database ID:**
        - Open your Notion trading database
        - Look at the URL: `https://www.notion.so/[workspace]/[database_id]?v=...`
        - Copy the **32-character ID** between the workspace name and `?v=`
        - Example: `2865afdc4c2b8103881ed47b12bb3a44`

        **Need help?** Check the [Notion API documentation](https://developers.notion.com/docs/getting-started)
        """)

else:
    # User is logged in - show full chat interface
    st.title("💬 Trading Chat with AI")

    # Sidebar - User info
    st.sidebar.title("Trading Chat")

    # Environment indicator
    if IS_LOCAL:
        st.sidebar.success("🏠 Local Mode (No GCP Auth)")
    else:
        st.sidebar.info("☁️ Production Mode (GCP Auth)")

    st.sidebar.markdown("---")

    # Display user info
    if st.session_state.user_info:
        st.sidebar.markdown(f"👤 **{st.session_state.user_info['email']}**")
        st.sidebar.caption(f"ID: {st.session_state.user_info['user_id'][:8]}...")

        if st.sidebar.button("🚪 Logout"):
            logout()
            st.rerun()

    st.sidebar.markdown("---")

    # Get user_id from session state
    user_id = st.session_state.user_info.get("user_id", "") if st.session_state.user_info else ""

    # Initialize active session
    if "active_session_id" not in st.session_state:
        st.session_state.active_session_id = None

    # Session management
    with st.sidebar:
        st.markdown("### Chat Sessions")

        # Get existing sessions
        sessions_data = api_get("/v1/sessions", params={"user_id": user_id})

        if sessions_data and sessions_data.get('sessions'):
            sessions = sessions_data['sessions']
            session_options = {f"{s['session_id'][:8]}... ({s.get('message_count', 0)} msgs)": s['session_id'] for s in sessions}

            if st.session_state.active_session_id and st.session_state.active_session_id in session_options.values():
                default_display = [k for k, v in session_options.items() if v == st.session_state.active_session_id][0]
                default_index = list(session_options.keys()).index(default_display) + 1
            else:
                default_index = 0

            selected_display = st.selectbox(
                "Select Session",
                ["Create New Session"] + list(session_options.keys()),
                index=default_index
            )

            if selected_display == "Create New Session":
                st.session_state.active_session_id = None
            else:
                st.session_state.active_session_id = session_options[selected_display]
        else:
            st.session_state.active_session_id = None
            st.info("No sessions yet. Start a new one!")

        if st.button("➕ New Session"):
            st.session_state.active_session_id = None
            st.session_state.messages = []
            st.session_state.loaded_session = None
            st.rerun()

        if st.session_state.active_session_id:
            if st.button("🗑️ Delete Session"):
                result = api_delete(f"/v1/sessions/{st.session_state.active_session_id}")
                if result:
                    st.success("Session deleted!")
                    st.session_state.active_session_id = None
                    st.session_state.messages = []
                    st.session_state.loaded_session = None
                    st.rerun()

    st.sidebar.markdown("---")

    # Assimilated Knowledge Management
    st.sidebar.markdown("### 🎓 Assimilated Knowledge")
    with st.sidebar.expander("Manage AI's Long-Term Memory", expanded=False):

        # Fetch knowledge
        knowledge_list = api_get("/v1/memory/knowledge")

        if knowledge_list is not None:
            # State to manage which item is being edited
            if "editing_knowledge_index" not in st.session_state:
                st.session_state.editing_knowledge_index = None

            for i, knowledge in enumerate(knowledge_list):
                st.markdown("---")
                if st.session_state.editing_knowledge_index == i:
                    # --- EDIT MODE ---
                    edited_text = st.text_area("Edit knowledge", value=knowledge, key=f"edit_knowledge_{i}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Save", key=f"save_knowledge_{i}", use_container_width=True):
                            if edited_text != knowledge:
                                result = api_put(
                                    "/v1/memory/knowledge",
                                    json_data={"old_knowledge": knowledge, "new_knowledge": edited_text}
                                )
                                if result:
                                    st.success("Knowledge updated!")
                                else:
                                    st.error("Failed to update knowledge.")
                            st.session_state.editing_knowledge_index = None
                            st.rerun()

                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_edit_{i}", use_container_width=True):
                            st.session_state.editing_knowledge_index = None
                            st.rerun()

                else:
                    # --- DISPLAY MODE ---
                    st.info(knowledge)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✏️ Edit", key=f"edit_knowledge_{i}", use_container_width=True):
                            st.session_state.editing_knowledge_index = i
                            st.rerun()
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_knowledge_{i}", use_container_width=True):
                            result = api_delete("/v1/memory/knowledge", json_data={"knowledge": knowledge})
                            if result:
                                st.success("Knowledge deleted!")
                                st.session_state.editing_knowledge_index = None # Reset edit state
                                st.rerun()
                            else:
                                st.error("Failed to delete knowledge.")
            
            # --- ADD NEW KNOWLEDGE ---
            st.markdown("---")
            new_knowledge_text = st.text_area("Add new knowledge", key="new_knowledge_input", placeholder="Add a new 'golden rule'...")
            if st.button("➕ Add New", key="add_new_knowledge"):
                if new_knowledge_text:
                    result = api_post("/v1/memory/knowledge", {"knowledge": new_knowledge_text})
                    if result:
                        st.success("New knowledge added!")
                        st.rerun()
                else:
                    st.warning("Cannot add empty knowledge.")

    st.sidebar.markdown("---")
    st.sidebar.caption("FastAPI Backend: " + API_BASE_URL)

    # Main chat interface
    session_id = st.session_state.active_session_id

    col1, col2 = st.columns([3, 1])

    with col2:
        st.markdown("### Settings")
        chat_provider = st.selectbox("AI Provider", providers, key="chat_provider")
        st.caption(f"Session ID: {session_id[:8] if session_id else 'New'}...")

        st.markdown("---")
        st.markdown("### 💡 Notion Queries")
        st.info("Ask about your trades and I'll query your Notion database!")
        st.markdown("**Example queries:**")
        st.markdown("- Show me profitable XAUUSD trades")
        st.markdown("- What are my recent losses?")
        st.markdown("- Analyze my M15 timeframe trades")

        st.markdown("---")
        st.markdown("### 🎥 RAG (Knowledge Base)")
        enable_rag = st.checkbox(
            "Enable RAG",
            value=True,  # ← ENABLED by default for video citations
            help="Search knowledge base for relevant context before answering"
        )

        if enable_rag:
            # Get available collections from ChromaDB
            try:
                import chromadb  # type: ignore[import-not-found]
                from pathlib import Path

                chroma_path = Path("var/chromadb")
                if chroma_path.exists():
                    client = chromadb.PersistentClient(path=str(chroma_path))
                    collections = client.list_collections()

                    if collections:
                        # Get collection info
                        collection_options = []
                        for coll_item in collections:
                            if isinstance(coll_item, str):
                                coll_name = coll_item
                            elif hasattr(coll_item, 'name'):
                                coll_name = coll_item.name
                            else:
                                coll_name = str(coll_item)

                            coll = client.get_collection(coll_name)
                            count = coll.count()
                            collection_options.append(f"{coll_name} ({count} docs)")

                        selected = st.selectbox(
                            "Select Collection",
                            options=collection_options,
                            help="Choose which knowledge base to search"
                        )

                        if selected:
                            parts = selected.split(" (")
                            rag_collection = parts[0] if parts else "trades_transcripts"
                            doc_count = parts[1].split(" ")[0].rstrip(")") if len(parts) > 1 else "0"
                        else:
                            rag_collection = "trades_transcripts"
                            doc_count = "0"

                        st.success(f"✅ Using: **{rag_collection}** with **{doc_count}** documents")
                    else:
                        st.warning("⚠️ No collections found in ChromaDB")
                        rag_collection = "trades_transcripts"
                else:
                    st.warning("⚠️ ChromaDB not found")
                    rag_collection = "trades_transcripts"
            except Exception as e:
                st.error(f"Error loading collections: {e}")
                rag_collection = "trades_transcripts"
        else:
            rag_collection = "trades_transcripts"

        st.markdown("---")
        st.markdown("### 🎯 Validator Examples (Few-Shot Learning)")
        enable_validator = st.checkbox(
            "Enable Validator Examples",
            value=True,
            help="Use analyzed sessions as examples to improve responses (recommended for trading questions)"
        )

        if enable_validator:
            validator_smart_mode = st.checkbox(
                "Smart Mode",
                value=True,
                help="Only use examples for complex trading queries (faster for simple questions)"
            )
        else:
            validator_smart_mode = False

    with col1:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if session_id and not st.session_state.get("loaded_session") == session_id:
            messages_data = api_get(
                f"/v1/sessions/{session_id}/messages",
                params={"user_id": user_id}
            )
            if messages_data and messages_data.get('messages'):
                st.session_state.messages = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in messages_data['messages']
                ]
            st.session_state.loaded_session = session_id

        message_container = st.container(height=900)

        with message_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if user_prompt := st.chat_input("Ask about your trades..."):
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with message_container:
                with st.chat_message("user"):
                    st.markdown(user_prompt)

            # Handle slash commands or proceed with chat
            if user_prompt.strip() == "/show_memory":
                with message_container:
                    with st.chat_message("assistant"):
                        with st.spinner("Fetching memory..."):
                            memory_data = api_get("/v1/memory/show")
                            if memory_data:
                                # Display the JSON object nicely
                                st.json(memory_data)
                                # Also save the raw content to the message history as a markdown code block
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": f"```json\n{json.dumps(memory_data, indent=2)}\n```"
                                })
                            else:
                                error_content = "Failed to fetch memory."
                                st.error(error_content)
                                st.session_state.messages.append({"role": "assistant", "content": error_content})
                # Rerun to clear input and settle state
                st.rerun()

            else:  # Proceed with normal chat logic
                with message_container:
                    with st.chat_message("assistant"):
                        status_placeholder = st.empty()
                        step1_placeholder = st.empty()
                        step2_placeholder = st.empty()
                        step3_placeholder = st.empty()

            # Call chat API
            data = {
                "prompt": user_prompt,
                "provider": chat_provider,
                "use_memory": True,
                "session_id": session_id,
                "user_id": user_id,
                "enable_rag": enable_rag,
                "rag_collection": rag_collection,
                "enable_validator_examples": enable_validator,
                "validator_smart_mode": validator_smart_mode
            }

            try:
                # Prepare headers with authentication
                stream_headers = {}

                # Add app auth token as Bearer token (backend expects this format)
                if st.session_state.auth_token:
                    stream_headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
                # For production: also add GCP Identity Token if available
                elif not IS_LOCAL:
                    gcp_token = get_gcp_identity_token()
                    if gcp_token:
                        stream_headers["Authorization"] = f"Bearer {gcp_token}"

                response = requests.post(
                    f"{API_BASE_URL}/v1/chat/stream",
                    json=data,
                    headers=stream_headers,
                    stream=True
                )

                final_response = None
                new_session_id = None
                pipeline_steps = []
                step1_duration = 0
                step2_duration = 0
                step3_duration = 0

                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            event_json = line_str[6:]
                            event = json.loads(event_json)
                            event_type = event.get('event')

                            if event_type == 'session_created':
                                new_session_id = event.get('session_id')
                                pipeline_steps.append("✓ Session")
                                status_placeholder.caption(f"🔄 {' → '.join(pipeline_steps)}")

                            elif event_type == 'message_saved':
                                pipeline_steps.append("✓ Saved")
                                status_placeholder.caption(f"🔄 {' → '.join(pipeline_steps)}")

                            elif event_type == 'rag_retrieving':
                                pipeline_steps.append("🔍 RAG...")
                                status_placeholder.caption(f"🔄 {' → '.join(pipeline_steps)}")

                            elif event_type == 'rag_retrieved':
                                chunks = event.get('chunks', 0)
                                pipeline_steps[-1] = f"✓ {chunks} chunks"
                                status_placeholder.caption(f"🔄 {' → '.join(pipeline_steps)}")

                            elif event_type == 'context_loaded':
                                pipeline_steps.append("✓ Context")
                                status_placeholder.caption(f"🔄 {' → '.join(pipeline_steps)}")

                            elif event_type == 'generating':
                                pipeline_steps.append("🤖 Thinking...")
                                status_placeholder.caption(f"🔄 {' → '.join(pipeline_steps)}")

                            elif event_type == 'generated':
                                text = event.get('text', '')
                                step1_duration = event.get('duration_ms', 0)
                                pipeline_steps[-1] = "✓ Generated"
                                status_placeholder.caption(f"🔄 {' → '.join(pipeline_steps)}")

                                with step1_placeholder.container():
                                    st.markdown(text)
                                    st.caption(f"⏱️ Completed in {step1_duration}ms")

                            elif event_type == 'function_call':
                                func_name = event.get('function', '')
                                args = event.get('args', {})
                                pipeline_steps.append("⚙️ Function...")
                                status_placeholder.caption(f"🔄 {' → '.join(pipeline_steps)}")

                                with step2_placeholder.container():
                                    with st.expander("⚙️ Function Call", expanded=False):
                                        st.markdown(f"**Function:** `{func_name}`")
                                        st.code(json.dumps(args, indent=2), language="json")

                            elif event_type == 'function_result':
                                result_data = event.get('result', {})
                                pipeline_steps[-1] = "✓ Function"
                                status_placeholder.caption(f"🔄 {' → '.join(pipeline_steps)}")

                                with step2_placeholder.container():
                                    with st.expander("⚙️ Function Result", expanded=False):
                                        st.json(result_data)

                            elif event_type == 'response_generating':
                                pipeline_steps.append("💡 Synthesizing...")
                                status_placeholder.caption(f"🔄 {' → '.join(pipeline_steps)}")

                            elif event_type == 'response_generated':
                                text = event.get('text', '')
                                step3_duration = event.get('duration_ms', 0)
                                pipeline_steps[-1] = "✓ Response"
                                status_placeholder.caption(f"🔄 {' → '.join(pipeline_steps)}")

                                with step3_placeholder.container():
                                    st.markdown(text)
                                    st.caption(f"⏱️ Completed in {step3_duration}ms")

                            elif event_type == 'complete':
                                final_response = event.get('response')
                                new_session_id = new_session_id or event.get('session_id')
                                total_duration = event.get('total_duration_ms', 0)
                                status_placeholder.success(f"✅ Complete in {total_duration}ms")

                            elif event_type == 'error':
                                error_msg = event.get('error', 'Unknown error')
                                pipeline_steps.append("❌ Error")
                                status_placeholder.error(f"Error: {error_msg}")

                if final_response:
                    if not session_id and new_session_id:
                        st.session_state.active_session_id = new_session_id
                        st.session_state.loaded_session = new_session_id
                        session_id = new_session_id

                    st.session_state.messages.append({"role": "assistant", "content": final_response})

                    # Increment message count and check if feedback prompt should be shown
                    st.session_state.message_count += 1
                    if st.session_state.message_count % 10 == 0 and not st.session_state.feedback_sent:
                        st.session_state.show_feedback_prompt = True

                    st.rerun()

            except Exception as e:
                status_placeholder.error(f"❌ Error: {str(e)}")

        # Feedback prompt - show every 10 messages
        if st.session_state.show_feedback_prompt and st.session_state.active_session_id:
            st.markdown("---")
            st.markdown("### 💡 Feedback richiesto!")
            st.info(f"Hai raggiunto {st.session_state.message_count} messaggi. Vuoi inviare questa sessione per analisi e miglioramento?")

            with st.form("feedback_form"):
                send_feedback = st.checkbox(
                    "✅ Sì, invia questa chat come feedback",
                    value=False,
                    help="La sessione verrà analizzata e salvata nel knowledge base per migliorare future interazioni"
                )

                user_description = st.text_area(
                    "📝 Descrizione opzionale (cosa è andato bene/male?)",
                    placeholder="Es: 'Ottima analisi dei trade XAUUSD' oppure 'Ha avuto problemi a capire la mia domanda sui timeframe'",
                    help="Questa descrizione aiuterà il sistema a migliorare"
                )

                col_submit, col_skip = st.columns(2)
                with col_submit:
                    submit_feedback = st.form_submit_button("📤 Invia Feedback", use_container_width=True)
                with col_skip:
                    skip_feedback = st.form_submit_button("⏭️ Salta", use_container_width=True)

                if submit_feedback and send_feedback:
                    with st.spinner("Invio feedback in background..."):
                        feedback_data = {
                            "session_id": st.session_state.active_session_id,
                            "user_description": user_description
                        }

                        result = api_post("/v1/feedback/submit", feedback_data)

                        if result:
                            st.success("✅ Feedback inviato! L'analisi è in corso in background.")
                            st.session_state.show_feedback_prompt = False
                            st.session_state.feedback_sent = True
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Errore nell'invio del feedback. Riprova più tardi.")

                if skip_feedback or (submit_feedback and not send_feedback):
                    st.session_state.show_feedback_prompt = False
                    st.rerun()

        if st.session_state.messages:
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                st.session_state.loaded_session = None
                st.session_state.message_count = 0
                st.session_state.feedback_sent = False
                st.session_state.show_feedback_prompt = False
                st.rerun()
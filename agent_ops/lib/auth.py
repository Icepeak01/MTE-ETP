# lib/auth.py
import streamlit as st

def ensure_logged_in():
    if not st.session_state.get("auth"):
        st.warning("Please log in.")
        st.stop()

def can_access(allowed_roles=("admin","attendant")):
    role = st.session_state.get("role")
    return role in allowed_roles

def require_role(allowed_roles=("admin","attendant")):
    if not can_access(allowed_roles):
        st.warning("No access for your role.")
        if st.button("← Back to Home"):
            goto("home")
        st.stop()

def goto(view_key: str, do_rerun=True):
    st.session_state["view"] = view_key
    if do_rerun:
        st.rerun()



def logout_button():
    if st.button("Logout"):
        for k in ("auth","username","role","view"):
            st.session_state.pop(k, None)
        st.rerun()

def role_badge(role: str):
    color = "#2b90d9" if role=="admin" else "#43a047"
    st.markdown(
        f"""<div style="text-align:right;">
        <span style="background:{color};color:white;padding:6px 10px;border-radius:8px;">{role.upper()}</span>
        </div>""", unsafe_allow_html=True
    )

def view_header(title: str, back_to="home"):
    cols = st.columns([6,2,2])
    with cols[0]: st.title(title)
    with cols[1]: role_badge(st.session_state.get("role","?"))
    with cols[2]: logout_button()
    # NOTE: no on_click callback here; call goto() directly
    if st.button("← Back to Home", key=f"back_{title}"):
        goto(back_to)
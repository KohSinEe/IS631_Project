"""
Friendly, light theme for FridgeBuddy.
Warm cream background, soft greens and coral accents, rounded typography.
"""
CUSTOM_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap');

/* Base: warm light theme */
.stApp {
    background: linear-gradient(180deg, #faf8f5 0%, #f5f0e8 50%, #f0ebe3 100%);
    color: #374151;
}
html, body, [class*="css"], .stMarkdown, label, p {
    font-family: 'DM Sans', sans-serif;
    color: #374151;
}

/* Headings: warm dark */
h1, h2, h3 {
    font-family: 'DM Sans', sans-serif;
    color: #1f2937;
    font-weight: 600;
}
h1 { font-size: 1.85rem; }
h2 { font-size: 1.35rem; }
h3 { font-size: 1.1rem; }

.block-container {
    padding-top: 1.75rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}

/* Sidebar (if used) */
section[data-testid="stSidebar"] > div {
    background: linear-gradient(180deg, #ffffff 0%, #faf8f5 100%);
    border-right: 1px solid rgba(45, 138, 94, 0.15);
}

/* Metric cards: soft white with colored left border */
.metric-card {
    background: #ffffff;
    border: 1px solid rgba(45, 138, 94, 0.12);
    border-radius: 1rem;
    padding: 1rem 1.25rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    border-left: 4px solid #86c8a4;
}
.metric-card h3 {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.25rem;
    color: #6b7280;
    font-weight: 500;
}
.metric-card p {
    font-size: 1.75rem;
    margin: 0;
    color: #1f2937;
    font-weight: 600;
}
.metric-green {
    border-left-color: #2d8a5e;
}
.metric-green h3 { color: #166534; }
.metric-orange {
    border-left-color: #ea580c;
}
.metric-orange h3 { color: #9a3412; }
.metric-red {
    border-left-color: #dc2626;
}
.metric-red h3 { color: #991b1b; }

/* Pills / labels */
.pill-label {
    background: rgba(45, 138, 94, 0.12);
    border-radius: 999px;
    padding: 0.25rem 0.75rem;
    font-size: 0.85rem;
    color: #166534;
    display: inline-block;
}
.danger-pill {
    background: rgba(220, 38, 38, 0.1);
    color: #991b1b;
}

/* Streamlit elements: softer borders and radius */
.stButton > button {
    font-family: 'DM Sans', sans-serif;
    border-radius: 0.6rem;
    font-weight: 500;
    transition: box-shadow 0.2s ease, transform 0.1s ease;
}
.stButton > button:hover {
    box-shadow: 0 4px 12px rgba(45, 138, 94, 0.2);
}
[data-testid="stDataFrame"] {
    border-radius: 0.75rem;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
/* Inputs */
.stTextInput input, .stNumberInput input {
    border-radius: 0.5rem;
    border-color: rgba(45, 138, 94, 0.25);
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #2d8a5e;
    box-shadow: 0 0 0 2px rgba(45, 138, 94, 0.2);
}

/* Expander headers */
.streamlit-expanderHeader {
    background: #ffffff;
    border-radius: 0.5rem;
    border: 1px solid rgba(45, 138, 94, 0.12);
}

/* Landing hero (public view) */
.landing-hero {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
}
.landing-hero h1 {
    color: #1f2937;
    font-size: 2.25rem;
    margin-bottom: 0.35rem;
}
.landing-tagline {
    color: #6b7280;
    font-size: 1.1rem;
    font-weight: 500;
}

/* Dashboard welcome header */
.dashboard-welcome h1 { font-size: 1.75rem; color: #1f2937; margin-bottom: 0.2rem; }
.dashboard-welcome h3 { font-size: 1rem; color: #6b7280; font-weight: 500; }

/* Account button and popover: prevent text overlapping */
[data-testid="stPopover"] {
    min-width: 12rem;
}
[data-testid="stPopover"] button {
    min-width: 8rem;
    white-space: nowrap;
}
/* Popover content (dropdown) - wide enough for "Invite to fridge", "Delete fridge" */
[data-testid="stPopover"] [role="dialog"],
[data-testid="stPopover"] > div > div {
    min-width: 14rem;
}
</style>
"""

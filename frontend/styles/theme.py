CUSTOM_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&display=swap');
.stApp {
    background: radial-gradient(circle at top, #1e1b4b 0%, #0f172a 55%, #020617 100%);
    color: #f8fafc;
}
section[data-testid="stSidebar"] > div {
    background: rgba(15, 23, 42, 0.85);
    border-right: 1px solid rgba(148, 163, 184, 0.2);
}
html, body, [class*="css"], .stMarkdown, label, input, button {
    font-family: 'Space Grotesk', sans-serif;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
.metric-card {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 1rem;
    padding: 1rem 1.25rem;
}
.metric-card h3 {
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.2rem;
    color: #94a3b8;
}
.metric-card p {
    font-size: 2rem;
    margin: 0;
    color: #f8fafc;
}
.metric-blue::before {
    background: linear-gradient(180deg, #38bdf8, #6366f1);
}
.metric-green::before {
    background: linear-gradient(180deg, #22c55e, #4ade80);
}
.metric-orange::before {
    background: linear-gradient(180deg, #fb923c, #f97316);
}
.metric-red::before {
    background: linear-gradient(180deg, #f87171, #ef4444);
}
.pill-label {
    background: rgba(59, 130, 246, 0.15);
    border-radius: 999px;
    padding: 0.2rem 0.8rem;
    font-size: 0.85rem;
    color: #bfdbfe;
    display: inline-block;
}
.danger-pill {
    background: rgba(248, 113, 113, 0.15);
    color: #fecaca;
}
</style>
"""

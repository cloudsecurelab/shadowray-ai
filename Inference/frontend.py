"""
Enterprise Sentiment Analysis UI
Powered by Ray Serve + Gradio

Make sure port-forward is active:
  kubectl port-forward service/raycluster-sample-head-svc 8000:8000 -n default
"""

import gradio as gr
import requests
import json
from datetime import datetime

RAY_SERVE_URL = "http://localhost:8000/analyze"

history = []

def analyze_sentiment(text):
    if not text or not text.strip():
        return "⚠️ Please enter some text to analyze.", "", "", format_history()

    try:
        response = requests.post(
            RAY_SERVE_URL,
            headers={"Content-Type": "application/json"},
            json={"text": text},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        sentiment = result.get("sentiment", "UNKNOWN")
        score = result.get("confidence", 0.0)
        confidence = f"{score * 100:.1f}%"

        if sentiment == "POSITIVE":
            emoji = "🟢"
            sentiment_display = "## 🟢 POSITIVE"
        elif sentiment == "NEGATIVE":
            emoji = "🔴"
            sentiment_display = "## 🔴 NEGATIVE"
        else:
            emoji = "🟡"
            sentiment_display = f"## 🟡 {sentiment}"

        confidence_display = f"**Confidence:** {confidence}"

        # Sanitize text for HTML table (escape < > & |)
        safe_text = text[:60] + "..." if len(text) > 60 else text
        safe_text = safe_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        history.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "text": safe_text,
            "sentiment": sentiment,
            "emoji": emoji,
            "confidence": confidence,
        })

        return (
            sentiment_display,
            confidence_display,
            f"```json\n{json.dumps(result, indent=2)}\n```",
            format_history()
        )

    except requests.exceptions.ConnectionError:
        return (
            "## ❌ Connection Error",
            "Could not reach Ray Serve endpoint.",
            "Make sure port-forward is active:\n`kubectl port-forward service/raycluster-sample-head-svc 8000:8000`",
            format_history()
        )
    except Exception as e:
        return "## ❌ Error", str(e), "", format_history()


def format_history():
    if not history:
        return "<p style='color:#64748b;font-style:italic'>No analyses yet.</p>"

    rows = ""
    for h in history[:10]:
        color = "#22c55e" if h["sentiment"] == "POSITIVE" else "#ef4444" if h["sentiment"] == "NEGATIVE" else "#eab308"
        rows += f"""
        <tr>
            <td style='padding:8px 12px;color:#475569;white-space:nowrap'>{h['time']}</td>
            <td style='padding:8px 12px;color:#1e293b;max-width:300px'>{h['text']}</td>
            <td style='padding:8px 12px;color:{color};font-weight:600;white-space:nowrap'>{h['emoji']} {h['sentiment']}</td>
            <td style='padding:8px 12px;color:#1e293b;white-space:nowrap'>{h['confidence']}</td>
        </tr>"""

    return f"""
    <table style='width:100%;border-collapse:collapse;font-size:0.9em;font-family:Inter,sans-serif'>
        <thead>
            <tr style='border-bottom:1px solid #334155'>
                <th style='padding:8px 12px;text-align:left;color:#64748b;font-weight:600'>Time</th>
                <th style='padding:8px 12px;text-align:left;color:#64748b;font-weight:600'>Text</th>
                <th style='padding:8px 12px;text-align:left;color:#64748b;font-weight:600'>Sentiment</th>
                <th style='padding:8px 12px;text-align:left;color:#64748b;font-weight:600'>Confidence</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


def clear_all():
    history.clear()
    return "", "_Awaiting analysis..._", "", "", format_history()


SAMPLES = [
    ["Setting up GPU nodes was really frustrating and took forever."],
    ["After 18 hours we finally got it working and the results are amazing!"],
    ["The model accuracy is acceptable but deployment was painful."],
    ["I absolutely love how Ray handles distributed workloads seamlessly."],
    ["This is the worst developer experience I have ever encountered."],
]

CSS = """
    .header-box {
        background: linear-gradient(135deg, #1e3a5f 0%, #0f2847 100%);
        border-radius: 12px;
        padding: 24px 32px;
        margin-bottom: 8px;
    }
    .header-box h1 { color: white !important; margin: 0; font-size: 1.8em; }
    .header-box p  { color: #94b4d4 !important; margin: 4px 0 0 0; font-size: 0.95em; }
    .badge {
        display: inline-block;
        background: #22c55e22;
        border: 1px solid #22c55e66;
        color: #22c55e;
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 0.78em;
        font-weight: 600;
        margin-top: 8px;
    }
    footer { display: none !important; }
"""

THEME = gr.themes.Base(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "sans-serif"],
)

with gr.Blocks(title="Enterprise Sentiment Analysis") as demo:

    gr.HTML("""
        <script>
            document.addEventListener('keydown', function(e) {
                if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                    e.preventDefault();
                    // Try multiple selectors to find the primary button
                    var btn = document.querySelector('button.primary') ||
                            document.querySelector('.gr-button-primary') ||
                            document.querySelector('button[variant="primary"]');
                    if (btn) {
                        btn.click();
                    }
                }
            });
        </script>
    """)

    gr.HTML("""
        <div class="header-box">
            <h1>Enterprise Sentiment Analysis</h1>
            <p>Powered by Ray Serve · Distributed AI Infrastructure · Real-time Inference</p>
            <span class="badge">● LIVE</span>
        </div>
    """)

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### Input")
            text_input = gr.Textbox(
                placeholder="Enter text and press Enter to analyze...",
                lines=4,
                label="",
                show_label=False,
                container=False,
            )
            with gr.Row():
                analyze_btn = gr.Button("Analyze", variant="primary", scale=3)
                clear_btn = gr.Button("Clear", variant="secondary", scale=1)

            gr.Markdown("#### Sample inputs")
            gr.Examples(examples=SAMPLES, inputs=text_input, label="")

        with gr.Column(scale=2):
            gr.Markdown("### Result")
            sentiment_out = gr.Markdown("_Awaiting analysis..._")
            confidence_out = gr.Markdown("")
            with gr.Accordion("Raw API Response", open=False):
                raw_out = gr.Markdown("")

    gr.Markdown("---")
    gr.Markdown("### Analysis History")
    history_out = gr.HTML("<p style='color:#64748b;font-style:italic'>No analyses yet.</p>")

    gr.HTML("""
        <div style="margin-top:16px; padding: 12px 16px; background:#1e293b; border-radius:8px; font-size:0.82em; color:#cbd5e1;">
            <b style="color:#94a3b8">Infrastructure:</b> &nbsp;
            Ray Serve endpoint → <code>http://localhost:8000/analyze</code> &nbsp;|&nbsp;
            Ray Dashboard → <code>http://localhost:8265</code> &nbsp;|&nbsp;
            <span style="color:#22c55e">●</span> OKE Cluster
        </div>
    """)

    analyze_btn.click(
        fn=analyze_sentiment,
        inputs=[text_input],
        outputs=[sentiment_out, confidence_out, raw_out, history_out]
    )
    text_input.submit(
        fn=analyze_sentiment,
        inputs=[text_input],
        outputs=[sentiment_out, confidence_out, raw_out, history_out]
    )
    clear_btn.click(
        fn=clear_all,
        inputs=[],
        outputs=[text_input, sentiment_out, confidence_out, raw_out, history_out]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=THEME,
        css=CSS,
    )

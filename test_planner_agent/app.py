import os
import logging
import asyncio
import json
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

from test_planner_agent.agent import app as adk_app
from test_planner_agent.config import PRD_SAMPLE_PATH
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_planner_web")

app = FastAPI(title="Agentic Test Planner Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()
runner = Runner(
    app=adk_app,
    session_service=session_service,
    artifact_service=artifact_service,
)

class GenerateRequest(BaseModel):
    url: str
    prd: Optional[str] = None
    depth: Optional[int] = 2
    pages: Optional[int] = 5

# CSS & HTML Template
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TestMind · Agentic Test Planner</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2220%22 fill=%22%23080a10%22/><text y=%2270%22 x=%2215%22 font-size=%2260%22 fill=%22%233b82f6%22>🧠</text></svg>">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&family=DM+Mono&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {
            --bg-color: #080a10;
            --surface-color: rgba(17, 22, 39, 0.7);
            --surface-border: rgba(255, 255, 255, 0.08);
            --primary-color: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.15);
            --accent-color: #10b981;
            --accent-glow: rgba(16, 185, 129, 0.15);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --font-display: 'Outfit', sans-serif;
            --font-body: 'Space Grotesk', sans-serif;
            --font-mono: 'DM Mono', monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: var(--font-body);
            background-color: var(--bg-color);
            color: var(--text-primary);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background-image: 
                radial-gradient(circle at 10% 15%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 85%, rgba(16, 185, 129, 0.05) 0%, transparent 45%);
            background-attachment: fixed;
        }

        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 40px;
            border-b: 1px solid var(--surface-border);
            background: rgba(8, 10, 16, 0.8);
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo-section {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            font-size: 24px;
            color: var(--primary-color);
            text-shadow: 0 0 10px var(--primary-glow);
        }

        .logo-text {
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 20px;
            letter-spacing: -0.02em;
        }

        .logo-text span {
            color: var(--primary-color);
        }

        .badge {
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.2);
            color: var(--primary-color);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .container {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 30px;
            padding: 20px 40px 30px 40px;
            flex: 1;
            overflow: hidden;
        }

        aside {
            display: flex;
            flex-direction: column;
            gap: 20px;
            overflow-y: auto;
            padding-right: 5px;
        }

        .card {
            background: var(--surface-color);
            border: 1px solid var(--surface-border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
        }

        .card-title {
            font-family: var(--font-display);
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-primary);
        }

        .card-title i {
            color: var(--primary-color);
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 16px;
        }

        label {
            font-size: 12px;
            font-weight: 500;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        input[type="text"], textarea {
            background: rgba(8, 10, 16, 0.5);
            border: 1px solid var(--surface-border);
            border-radius: 8px;
            padding: 12px;
            color: var(--text-primary);
            font-family: var(--font-body);
            font-size: 13px;
            transition: all 0.2s ease;
        }

        input[type="text"]:focus, textarea:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 10px var(--primary-glow);
        }

        textarea {
            resize: vertical;
            min-height: 180px;
            font-family: var(--font-mono);
            font-size: 11px;
            line-height: 1.5;
        }

        .btn {
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 14px;
            font-family: var(--font-display);
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 10px;
            width: 100%;
        }

        .btn:hover {
            background: #2563eb;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        .btn:disabled {
            background: var(--text-muted);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .spin {
            animation: spin 1.2s linear infinite;
            display: inline-block;
        }

        @keyframes spin {
            100% { transform: rotate(360deg); }
        }

        .console-logs {
            background: #040508;
            border: 1px solid var(--surface-border);
            border-radius: 8px;
            padding: 14px;
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--accent-color);
            height: 150px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .log-entry {
            display: flex;
            gap: 8px;
        }

        .log-time {
            color: var(--text-muted);
            flex-shrink: 0;
        }

        .log-text {
            word-break: break-all;
        }

        main {
            display: flex;
            flex-direction: column;
            overflow: hidden;
            height: 100%;
        }

        .tab-header {
            display: flex;
            border-b: 1px solid var(--surface-border);
            margin-bottom: 20px;
            gap: 10px;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 10px 16px;
            font-family: var(--font-display);
            font-weight: 500;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
        }

        .tab-btn:hover {
            color: var(--text-primary);
        }

        .tab-btn.active {
            color: var(--primary-color);
        }

        .tab-btn.active::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--primary-color);
            box-shadow: 0 0 10px var(--primary-color);
        }

        .tab-content {
            flex: 1;
            overflow-y: auto;
            background: var(--surface-color);
            border: 1px solid var(--surface-border);
            border-radius: 16px;
            padding: 30px;
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* Markdown Styling */
        .markdown-body {
            line-height: 1.6;
            font-size: 15px;
        }

        .markdown-body h1, .markdown-body h2, .markdown-body h3 {
            font-family: var(--font-display);
            font-weight: 600;
            margin-top: 24px;
            margin-bottom: 16px;
            color: var(--text-primary);
        }

        .markdown-body h1 { font-size: 22px; border-bottom: 1px solid var(--surface-border); padding-bottom: 8px; }
        .markdown-body h2 { font-size: 18px; border-bottom: 1px solid var(--surface-border); padding-bottom: 6px; }
        .markdown-body h3 { font-size: 15px; }

        .markdown-body p, .markdown-body ul, .markdown-body ol {
            margin-bottom: 16px;
            color: var(--text-secondary);
        }

        .markdown-body ul, .markdown-body ol {
            padding-left: 20px;
        }

        .markdown-body li {
            margin-bottom: 4px;
        }

        .markdown-body table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            font-size: 13px;
        }

        .markdown-body th, .markdown-body td {
            border: 1px solid var(--surface-border);
            padding: 10px 14px;
            text-align: left;
        }

        .markdown-body th {
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-primary);
            font-weight: 600;
        }

        .markdown-body tr:nth-child(even) td {
            background: rgba(255, 255, 255, 0.01);
        }

        .markdown-body code {
            font-family: var(--font-mono);
            font-size: 12px;
            background: rgba(255, 255, 255, 0.06);
            padding: 2px 6px;
            border-radius: 4px;
            color: #f472b6;
        }

        .markdown-body pre {
            background: #040508;
            border: 1px solid var(--surface-border);
            border-radius: 8px;
            padding: 16px;
            overflow-x: auto;
            margin-bottom: 16px;
        }

        .markdown-body pre code {
            background: transparent;
            padding: 0;
            color: #60a5fa;
            font-size: 12px;
        }

        .markdown-body blockquote {
            border-left: 4px solid var(--primary-color);
            background: rgba(59, 130, 246, 0.05);
            padding: 12px 18px;
            margin-bottom: 16px;
            border-radius: 0 8px 8px 0;
        }

        .raw-text {
            width: 100%;
            height: 100%;
            background: #040508;
            color: #93c5fd;
            border: none;
            font-family: var(--font-mono);
            font-size: 12px;
            padding: 16px;
            border-radius: 8px;
            resize: none;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-section">
            <i class="fa-solid fa-brain logo-icon"></i>
            <div class="logo-text">Test<span>Mind</span></div>
            <div class="badge">ADK 2.0</div>
        </div>
        <div style="font-size: 12px; color: var(--text-secondary)">
            <i class="fa-solid fa-circle-nodes" style="color: var(--accent-color); margin-right: 4px"></i> Active Session Engine
        </div>
    </header>

    <div class="container">
        <aside>
            <div class="card" style="flex: 1; display: flex; flex-direction: column;">
                <div class="card-title">
                    <i class="fa-solid fa-sliders"></i>
                    Audit Configuration
                </div>
                <div class="form-group">
                    <label for="sut-url">Subject Under Test (SUT) URL</label>
                    <input type="text" id="sut-url" value="https://healthspan.assurecraft.org">
                </div>
                <div style="display: flex; gap: 16px; margin-bottom: 16px;">
                    <div class="form-group" style="flex: 1; margin-bottom: 0;">
                        <label for="crawl-depth">Max Depth</label>
                        <input type="number" id="crawl-depth" value="2" min="1" max="5" style="width: 100%; background: rgba(8, 10, 16, 0.5); border: 1px solid var(--surface-border); border-radius: 8px; padding: 12px; color: var(--text-primary); font-family: var(--font-body); font-size: 13px;">
                    </div>
                    <div class="form-group" style="flex: 1; margin-bottom: 0;">
                        <label for="crawl-pages">Max Pages</label>
                        <input type="number" id="crawl-pages" value="5" min="1" max="50" style="width: 100%; background: rgba(8, 10, 16, 0.5); border: 1px solid var(--surface-border); border-radius: 8px; padding: 12px; color: var(--text-primary); font-family: var(--font-body); font-size: 13px;">
                    </div>
                </div>
                <div class="form-group" style="flex: 1; display: flex; flex-direction: column;">
                    <label for="prd-input">Product Requirements Document (PRD) [Optional]</label>
                    <textarea id="prd-input" placeholder="Paste SUT specifications here..."></textarea>
                </div>
                <button class="btn" id="generate-btn">
                    <i class="fa-solid fa-play"></i>
                    <span>Generate Test Plan</span>
                </button>
            </div>
            
            <div class="card">
                <div class="card-title">
                    <i class="fa-solid fa-terminal"></i>
                    Execution Logs
                </div>
                <div class="console-logs" id="log-console">
                    <div class="log-entry">
                        <span class="log-time">[System]</span>
                        <span class="log-text" style="color: var(--text-secondary)">Ready. Configure inputs and click Generate.</span>
                    </div>
                </div>
            </div>
        </aside>

        <main>
            <div class="tab-header">
                <button class="tab-btn active" onclick="switchTab('tab-preview')">
                    <i class="fa-solid fa-file-invoice"></i> Markdown Test Plan
                </button>
                <button class="tab-btn" onclick="switchTab('tab-raw')">
                    <i class="fa-solid fa-code"></i> Raw MD Source
                </button>
                <button class="tab-btn" onclick="switchTab('tab-mapping')">
                    <i class="fa-solid fa-crosshairs"></i> Locator Mapping (JSON)
                </button>
            </div>

            <div id="tab-preview" class="tab-content active markdown-body">
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; color: var(--text-secondary)">
                    <i class="fa-solid fa-file-invoice" style="font-size: 48px; margin-bottom: 16px; opacity: 0.3"></i>
                    <p>No test plan generated yet.</p>
                </div>
            </div>

            <div id="tab-raw" class="tab-content">
                <textarea class="raw-text" id="raw-markdown-area" readonly placeholder="Raw Markdown will appear here after generation..."></textarea>
            </div>

            <div id="tab-mapping" class="tab-content">
                <textarea class="raw-text" id="raw-json-area" readonly placeholder="JSON target mapping will appear here after generation..."></textarea>
            </div>
        </main>
    </div>

    <script>
        // Populate default PRD on load
        window.addEventListener('DOMContentLoaded', async () => {
            try {
                const res = await fetch('/api/default_prd');
                if (res.ok) {
                    const text = await res.text();
                    document.getElementById('prd-input').value = text;
                }
            } catch (err) {
                console.error("Failed to load default PRD:", err);
            }
        });

        function addLog(text, type = "info") {
            const consoleBox = document.getElementById("log-console");
            const entry = document.createElement("div");
            entry.className = "log-entry";
            
            const time = document.createElement("span");
            time.className = "log-time";
            const now = new Date();
            time.textContent = `[${now.toTimeString().split(' ')[0]}]`;
            
            const txt = document.createElement("span");
            txt.className = "log-text";
            txt.textContent = text;
            
            if (type === "error") {
                txt.style.color = "#ef4444";
            } else if (type === "success") {
                txt.style.color = "#10b981";
            } else if (type === "progress") {
                txt.style.color = "#60a5fa";
            }
            
            entry.appendChild(time);
            entry.appendChild(txt);
            consoleBox.appendChild(entry);
            consoleBox.scrollTop = consoleBox.scrollHeight;
        }

        function switchTab(tabId) {
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Activate target
            const targetBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn => btn.getAttribute('onclick').includes(tabId));
            if (targetBtn) targetBtn.classList.add('active');
            
            document.getElementById(tabId).classList.add('active');
        }

        let activeController = null;

        document.getElementById("generate-btn").addEventListener("click", async () => {
            const btn = document.getElementById("generate-btn");
            const btnText = btn.querySelector("span");
            const btnIcon = btn.querySelector("i");
            
            // If already running, act as a "Stop" button
            if (btn.classList.contains("running")) {
                if (activeController) {
                    activeController.abort();
                }
                return;
            }
            
            const urlInput = document.getElementById("sut-url").value.trim ? document.getElementById("sut-url").value.trim() : document.getElementById("sut-url").value;
            const prdInput = document.getElementById("prd-input").value;
            const depthInput = parseInt(document.getElementById("crawl-depth").value) || 2;
            const pagesInput = parseInt(document.getElementById("crawl-pages").value) || 5;
            
            if (!urlInput) {
                alert("Please enter SUT URL.");
                return;
            }
            
            // Set running state
            btn.classList.add("running");
            btn.style.background = "rgba(239, 68, 68, 0.15)";
            btn.style.border = "1px solid rgba(239, 68, 68, 0.4)";
            btn.style.color = "#ef4444";
            btnText.textContent = "Stop Planning";
            btnIcon.className = "fa-solid fa-stop";
            
            document.getElementById("tab-preview").innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; color: var(--text-secondary)">
                    <i class="fa-solid fa-spinner spin" style="font-size: 48px; margin-bottom: 16px; color: var(--primary-color)"></i>
                    <p id="spinner-title" style="font-weight: 500;">Executing Workflow Graph...</p>
                    <p id="spinner-message" style="font-size: 12px; margin-top: 8px; color: var(--text-muted)">Initializing crawler...</p>
                </div>
            `;
            
            addLog(`Starting Test Planning for target: ${urlInput}`, "progress");
            
            activeController = new AbortController();
            let isCompleted = false;
            
            try {
                const response = await fetch("/api/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url: urlInput, prd: prdInput, depth: depthInput, pages: pagesInput }),
                    signal: activeController.signal
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                // Read streaming events
                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8");
                let planMarkdown = "";
                let semanticMapping = "";
                let buffer = "";
                
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, { stream: true });
                    buffer += chunk;
                    // Use regex to split on real newlines (fixes raw-string \\n issue)
                    const lines = buffer.split(/\r?\n/);
                    
                    // Keep the last partial line in the buffer
                    buffer = lines.pop();
                    
                    for (const line of lines) {
                        if (!line.trim()) continue;
                        let data;
                        try {
                            data = JSON.parse(line);
                        } catch (err) {
                            // Skip unparseable lines (partial chunks)
                            continue;
                        }
                        if (data.type === "log" || data.type === "keep-alive") {
                            if (data.type === "log") addLog(data.message, "progress");
                            const spinnerMsg = document.getElementById("spinner-message");
                            if (spinnerMsg) {
                                if (data.message.includes("parse_input")) {
                                    spinnerMsg.textContent = "Parsing target URL and loading specs...";
                                } else if (data.message.includes("run_crawler")) {
                                    spinnerMsg.textContent = "Crawling SUT and auditing DOM elements...";
                                } else if (data.message.includes("intent_mapper")) {
                                    spinnerMsg.textContent = "Mapping requirements to logical user journeys...";
                                } else if (data.message.includes("scenario_matrix_agent")) {
                                    spinnerMsg.textContent = "Generating scenario matrix (P0-P2)...";
                                } else if (data.message.includes("element_grounding_agent")) {
                                    spinnerMsg.textContent = "Grounding locator selectors and test fixtures...";
                                } else if (data.message.includes("compile_output")) {
                                    spinnerMsg.textContent = "Compiling final test plan report...";
                                } else if (data.type === "keep-alive") {
                                    spinnerMsg.textContent = "AI agents processing... (this may take a few minutes)";
                                } else {
                                    let cleanMsg = data.message.replace(/^\[.*?\]\s*/, "");
                                    if (cleanMsg) spinnerMsg.textContent = cleanMsg;
                                }
                            }
                        } else if (data.type === "complete") {
                            isCompleted = true;
                            addLog("Test Plan generation finished!", "success");
                            planMarkdown = data.markdown;
                            semanticMapping = JSON.stringify(data.mapping, null, 2);
                            
                            // Render markdown
                            document.getElementById("tab-preview").innerHTML = marked.parse(planMarkdown);
                            document.getElementById("raw-markdown-area").value = planMarkdown;
                            document.getElementById("raw-json-area").value = semanticMapping;
                        } else if (data.type === "error") {
                            addLog(data.message, "error");
                            throw new Error(data.message);
                        }
                    }
                }
                
                if (!isCompleted) {
                    throw new Error("Stream closed before generation was completed (timeout or termination).");
                }
                
            } catch (err) {
                let displayMessage = err.message;
                if (err.name === "AbortError") {
                    displayMessage = "Planning stopped by user.";
                    addLog("Planning workflow stopped by user.", "error");
                } else {
                    addLog(`Execution failed: ${displayMessage}`, "error");
                }
                
                document.getElementById("tab-preview").innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; color: #ef4444; padding: 20px; text-align: center;">
                        <i class="fa-solid fa-triangle-exclamation" style="font-size: 48px; margin-bottom: 16px"></i>
                        <p style="font-weight: 600; font-size: 18px;">Workflow execution failed</p>
                        <p style="font-size: 14px; margin-top: 8px; color: var(--text-muted); max-width: 500px;">${displayMessage}</p>
                        <button class="primary-btn" style="margin-top: 20px; background: rgba(59, 130, 246, 0.1); border: 1px solid var(--primary-color); color: var(--primary-color)" onclick="document.getElementById('generate-btn').click()">
                            <i class="fa-solid fa-rotate-right"></i> Restart Planner
                        </button>
                    </div>
                `;
            } finally {
                // Restore button state
                btn.classList.remove("running");
                btn.removeAttribute("style");
                btnText.textContent = "Generate Test Plan";
                btnIcon.className = "fa-solid fa-play";
                activeController = null;
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    return HTMLResponse(content=HTML_TEMPLATE)

@app.get("/api/default_prd")
def get_default_prd():
    if os.path.exists(PRD_SAMPLE_PATH):
        with open(PRD_SAMPLE_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), media_type="text/markdown")
    return "No default PRD file found."

async def run_workflow_to_queue(queue: asyncio.Queue, req_url: str, req_prd: str, max_depth: int, max_pages: int, session_id: str):
    try:
        # Create session
        session = await session_service.create_session(
            app_name=adk_app.name,
            user_id="hackathon_reviewer"
        )
        
        # Formulate user message
        payload = {
            "url": req_url,
            "prd": req_prd,
            "max_depth": max_depth,
            "max_pages": max_pages
        }
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=json.dumps(payload))]
        )
        
        # Inject session variables (like temporary artifact dir)
        artifact_dir = os.path.join(os.getcwd(), "artifacts", session.id)
        session.state["artifact_dir"] = artifact_dir
        
        await queue.put({"type": "log", "message": "Executing workflow graph..."})
        
        # Run ADK workflow
        active_nodes = set()
        async for event in runner.run_async(
            user_id="hackathon_reviewer",
            session_id=session.id,
            new_message=content
        ):
            node_name = event.node_info.path.split("/")[-1] if event.node_info else "System"
            
            # Send a start log the first time we enter a node
            if node_name not in active_nodes:
                active_nodes.add(node_name)
                await queue.put({"type": "log", "message": f"[{node_name}] Starting execution..."})
            
            # Check for progress or model response logs
            if event.content and event.content.role == "model":
                await queue.put({"type": "log", "message": f"[{node_name}] Node finished calculation."})
            elif event.output:
                await queue.put({"type": "log", "message": f"[{node_name}] Emitted output."})
        
        # Fetch final state to get the plan
        final_session = await session_service.get_session(
            app_name=adk_app.name,
            session_id=session.id,
            user_id="hackathon_reviewer"
        )
        
        md_plan = final_session.state.get("test_plan_markdown", "")
        mapping = final_session.state.get("semantic_target_mapping", {})
        
        if md_plan:
            await queue.put({
                "type": "complete",
                "markdown": md_plan,
                "mapping": mapping
            })
        else:
            await queue.put({"type": "error", "message": "Workflow completed but no test plan was produced."})
            
    except asyncio.CancelledError:
        logger.info(f"Workflow execution cancelled for session: {session_id}")
        raise
    except Exception as e:
        logger.exception("Error during workflow execution:")
        await queue.put({"type": "error", "message": f"Workflow crash: {str(e)}"})
    finally:
        # Put None to signal end of stream
        await queue.put(None)

@app.post("/api/generate")
async def generate_test_plan(req: GenerateRequest):
    async def sse_generator():
        session_id = f"sess_{int(asyncio.get_event_loop().time())}"
        queue = asyncio.Queue()
        
        # Start workflow execution in background task
        task = asyncio.create_task(
            run_workflow_to_queue(queue, req.url, req.prd or "", req.depth or 2, req.pages or 5, session_id)
        )
        
        yield json.dumps({"type": "log", "message": f"Initializing ADK 2.0 session: {session_id}"}) + "\n"
        
        try:
            while True:
                try:
                    # Wait for items from the queue with a 5-second timeout (keep-alive beats GFE 60s idle)
                    item = await asyncio.wait_for(queue.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Yield a keep-alive heartbeat every 5s to prevent GFE idle timeout
                    yield json.dumps({
                        "type": "keep-alive", 
                        "message": "AI agents processing..."
                    }) + "\n"
                    continue
                
                if item is None:
                    # End of stream signaled
                    break
                
                yield json.dumps(item) + "\n"
                
        except asyncio.CancelledError:
            logger.info(f"User disconnected, cancelling background workflow: {session_id}")
            task.cancel()
            raise
        except Exception as e:
            logger.exception("Error in SSE generator stream:")
            yield json.dumps({"type": "error", "message": f"Stream error: {str(e)}"}) + "\n"

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    }
    return StreamingResponse(sse_generator(), headers=headers, media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

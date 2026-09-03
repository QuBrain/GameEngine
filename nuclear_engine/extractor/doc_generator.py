"""Static API Documentation Generator for Nuclear Option's 1,200+ decompiled classes."""

import json
from pathlib import Path
from typing import Dict, Any, List

from nuclear_engine.config import config
from nuclear_engine.extractor.code_indexer import CodeIndexer


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nuclear Option API Reference</title>
    <style>
        :root {
            --bg: #0d1117;
            --sidebar-bg: #161b22;
            --card-bg: #21262d;
            --border: #30363d;
            --text: #c9d1d9;
            --text-heading: #58a6ff;
            --accent: #238636;
            --code-bg: #161b22;
            --code-text: #79c0ff;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        #sidebar {
            width: 320px;
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
        }
        #search-box {
            padding: 16px;
            border-bottom: 1px solid var(--border);
        }
        #search {
            width: 100%;
            padding: 8px 12px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: #fff;
            font-size: 14px;
            outline: none;
        }
        #class-count {
            font-size: 12px;
            color: #8b949e;
            margin-top: 8px;
        }
        #class-list {
            flex: 1;
            overflow-y: auto;
            list-style: none;
        }
        #class-list li {
            padding: 8px 16px;
            cursor: pointer;
            font-size: 13px;
            font-family: Consolas, monospace;
            border-bottom: 1px solid rgba(48, 54, 61, 0.4);
        }
        #class-list li:hover {
            background: rgba(88, 166, 255, 0.1);
            color: #58a6ff;
        }
        #class-list li.active {
            background: rgba(35, 134, 54, 0.2);
            color: #3fb950;
            font-weight: bold;
        }
        #main {
            flex: 1;
            overflow-y: auto;
            padding: 32px 48px;
        }
        h1 { font-size: 28px; color: #fff; margin-bottom: 8px; }
        .inheritance { font-family: monospace; color: #8b949e; margin-bottom: 24px; }
        .section-title { font-size: 18px; color: var(--text-heading); border-bottom: 1px solid var(--border); padding-bottom: 6px; margin: 24px 0 12px 0; }
        .method-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 6px; padding: 12px 16px; margin-bottom: 10px; }
        .sig { font-family: Consolas, monospace; font-size: 13px; color: var(--code-text); }
        .access { color: #ff7b72; margin-right: 6px; }
        .ret { color: #7ee787; margin-right: 6px; }
        .name { color: #d2a8ff; font-weight: bold; }
        .params { color: #c9d1d9; }
    </style>
</head>
<body>
    <div id="sidebar">
        <div id="search-box">
            <input type="text" id="search" placeholder="Search 1,200+ classes..." autofocus>
            <div id="class-count">Loading...</div>
        </div>
        <ul id="class-list"></ul>
    </div>
    <div id="main">
        <div id="content">
            <h1>Select a class from the list to view its API</h1>
            <p style="color: #8b949e; margin-top: 12px;">Browse classes, method signatures, parameters, fields, and events.</p>
        </div>
    </div>

    <script>
        const API_DATA = __JSON_DATA__;
        const searchInput = document.getElementById('search');
        const classList = document.getElementById('class-list');
        const contentDiv = document.getElementById('content');
        const countDiv = document.getElementById('class-count');

        function renderList(filter = '') {
            classList.innerHTML = '';
            const q = filter.toLowerCase();
            const filtered = API_DATA.filter(c => c.name.toLowerCase().includes(q));
            countDiv.textContent = `${filtered.length} of ${API_DATA.length} classes`;

            filtered.forEach(c => {
                const li = document.createElement('li');
                li.textContent = c.name;
                li.onclick = () => selectClass(c, li);
                classList.appendChild(li);
            });
        }

        function selectClass(c, activeEl) {
            document.querySelectorAll('#class-list li').forEach(el => el.classList.remove('active'));
            if (activeEl) activeEl.classList.add('active');

            let html = `<h1>${c.name}</h1>`;
            html += `<div class="inheritance">Base: ${c.base || 'None'} | Interfaces: ${c.interfaces.length ? c.interfaces.join(', ') : 'None'}</div>`;

            if (c.methods.length) {
                html += `<div class="section-title">Methods (${c.methods.length})</div>`;
                c.methods.forEach(m => {
                    html += `<div class="method-card">
                        <div class="sig">
                            <span class="access">${m.access}</span>
                            <span class="ret">${m.return}</span>
                            <span class="name">${m.name}</span>(${'<span class="params">' + m.params + '</span>'})
                        </div>
                    </div>`;
                });
            }

            if (c.fields.length) {
                html += `<div class="section-title">Fields (${c.fields.length})</div>`;
                c.fields.forEach(f => {
                    html += `<div class="method-card">
                        <div class="sig">
                            <span class="access">${f.access}</span>
                            <span class="ret">${f.type}</span>
                            <span class="name">${f.name}</span>
                        </div>
                    </div>`;
                });
            }

            if (c.events && c.events.length) {
                html += `<div class="section-title">Events (${c.events.length})</div>`;
                c.events.forEach(e => {
                    html += `<div class="method-card">
                        <div class="sig">
                            <span class="ret">event ${e.type}</span>
                            <span class="name">${e.name}</span>
                        </div>
                    </div>`;
                });
            }

            if (c.enums && c.enums.length) {
                html += `<div class="section-title">Enums (${c.enums.length})</div>`;
                c.enums.forEach(en => {
                    html += `<div class="method-card">
                        <div class="sig"><span class="name">enum ${en.name}</span>: ${en.values.join(', ')}</div>
                    </div>`;
                });
            }

            contentDiv.innerHTML = html;
        }

        searchInput.addEventListener('input', (e) => renderList(e.target.value));
        renderList();
        if (API_DATA.length) selectClass(API_DATA[0], classList.children[0]);
    </script>
</body>
</html>
"""


class APIDocGenerator:
    def __init__(self, indexer: CodeIndexer = None):
        self.indexer = indexer or CodeIndexer()
        self.docs_dir = config.workspace_root / "docs" / "api"

    def generate(self) -> Path:
        """Generate a complete standalone HTML & JSON API reference in docs/api/."""
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.indexer._ensure_cache()

        classes_data: List[Dict[str, Any]] = []

        for stem, path in sorted(self.indexer._class_cache.items()):
            info = self.indexer.parse_class(path.stem)
            if not info:
                continue

            classes_data.append({
                "name": info.name,
                "base": info.base_class or "",
                "interfaces": info.interfaces,
                "methods": [
                    {
                        "name": m.name,
                        "return": m.return_type,
                        "params": m.parameters,
                        "access": m.access,
                        "line": m.line_number,
                    }
                    for m in info.methods
                ],
                "fields": [
                    {
                        "name": f.name,
                        "type": f.type_name,
                        "access": f.access,
                        "line": f.line_number,
                    }
                    for f in info.fields
                ],

                "events": [
                    {
                        "name": e.name,
                        "type": e.event_type,
                        "line": e.line_number,
                    }
                    for e in info.events
                ],
                "enums": [
                    {
                        "name": en.name,
                        "values": en.values,
                        "line": en.line_number,
                    }
                    for en in info.enums
                ],
            })

        # 1. Write JSON data file
        json_path = self.docs_dir / "api_reference.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(classes_data, f, indent=2)

        # 2. Write self-contained HTML explorer
        html_path = self.docs_dir / "index.html"
        json_escaped = json.dumps(classes_data).replace("<", "\\u003c")
        html_content = HTML_TEMPLATE.replace("__JSON_DATA__", json_escaped)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path

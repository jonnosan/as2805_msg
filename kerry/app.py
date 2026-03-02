"""Kerry — AS2805 message encode/decode web UI.

Usage:
    python kerry/app.py [--port PORT]

Opens a browser-based tool for encoding and decoding AS2805 messages.
"""

from __future__ import annotations

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# Ensure the parent directory is on the path so as2805_msg is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from as2805_msg import (
    AS2805Message,
    ELS_SCHEMA,
    Field47,
    Field55,
    Field111,
    DataSet,
    Field113,
)
from as2805_msg.constants import MTI, TransactionType, AccountType
from as2805_msg.fields.field111 import TAG_NAMES as F111_TAG_NAMES, DATASET_NAMES
from as2805_msg.validation import FIELD_RULES

# Fields that have composite TLV sub-structure
TAG_FIELDS = {47, 55, 111, 113}

# Known tags for each composite field
F47_TAGS = {
    "ARI": "Account Reference Indicator",
    "TCC": "Terminal Capability Code",
    "FCR": "Faulty Card Reader",
    "PCA": "Post Code - Card Acceptor",
    "FCA": "Format of Card Acceptor",
    "BAI": "Business Application Indicator",
    "CTP": "Cash Type Indicator",
    "FSC": "Fraud Score",
    "FCC": "Fraud Sub-classification Code",
    "ECM": "eCommerce Indicator",
    "DCP": "Deferred Card Present",
    "CAV": "Card Authentication Value",
    "OLT": "Online Token",
}

F55_TAGS = {
    "9F26": "Application Cryptogram",
    "9F27": "Cryptogram Information Data",
    "9F10": "Issuer Application Data",
    "9F37": "Unpredictable Number",
    "9F36": "Application Transaction Counter",
    "9F02": "Authorised Amount",
    "9F03": "Other Amount",
    "9F1A": "Terminal Country Code",
    "5F2A": "Transaction Currency Code",
    "9A": "Transaction Date",
    "9C": "Transaction Type",
    "9F33": "Terminal Capabilities",
    "9F34": "CVM Results",
    "9F35": "Terminal Type",
    "84": "DF Name",
    "9F09": "Application Version Number",
    "9F41": "Transaction Sequence Counter",
}

F113_TAGS = {
    "001": "Token Requestor ID",
    "002": "Token Reference ID",
    "003": "Token Assurance Level",
    "004": "Last 4 of PAN",
    "005": "Payment Account Reference",
}


def _build_schema_json() -> dict:
    """Build the JSON schema payload sent to the browser on page load."""
    fields = {}
    for fnum, spec in sorted(ELS_SCHEMA._specs.items()):
        if fnum == 1:
            continue  # secondary bitmap — auto-managed
        fields[str(fnum)] = {
            "name": spec.name,
            "type": spec.field_type,
            "max_length": spec.max_length,
            "length_type": spec.length_type,
        }

    mti_names = {code: name for code, name in MTI.NAMES.items()}

    rules = {}
    for mti, field_rules in FIELD_RULES.items():
        rules[mti] = {str(f): r for f, r in field_rules.items() if f != 1}

    # Tag metadata for composite fields
    tag_fields = {
        "47": {
            "format": "ascii3",
            "tags": F47_TAGS,
        },
        "55": {
            "format": "ber-tlv",
            "tags": F55_TAGS,
        },
        "111": {
            "format": "dataset",
            "datasets": {f"{k:02X}": v for k, v in DATASET_NAMES.items()},
            "tags": {f"{k:02X}": v for k, v in F111_TAG_NAMES.items()},
        },
        "113": {
            "format": "numeric3",
            "tags": F113_TAGS,
        },
    }

    # Processing code sub-field lookups
    processing_code = {
        "transaction_types": TransactionType.NAMES,
        "account_types": AccountType.NAMES,
    }

    return {"fields": fields, "mti_names": mti_names, "rules": rules, "tag_fields": tag_fields, "processing_code": processing_code}


SCHEMA_JSON = json.dumps(_build_schema_json())


def _decode_message(hex_str: str) -> dict:
    """Decode a hex string into a message dict."""
    cleaned = hex_str.replace(" ", "").replace("\n", "").replace("\r", "")
    # Strip any non-hex characters (punctuation etc.)
    cleaned = "".join(c for c in cleaned if c in "0123456789abcdefABCDEF")
    data = bytes.fromhex(cleaned)
    msg = AS2805Message.unpack(data)

    fields = {}
    for fnum, value in sorted(msg.fields.items()):
        raw = value if isinstance(value, (bytes, bytearray)) else None

        if fnum == 47:
            try:
                raw_bytes = value.encode("ascii") if isinstance(value, str) else value
                tags = Field47.unpack(raw_bytes)
                fields[str(fnum)] = {
                    "_type": "f47",
                    "tags": {k: v.decode("ascii", errors="replace") for k, v in tags.items()},
                }
                continue
            except Exception:
                pass

        if fnum == 55 and isinstance(value, (bytes, bytearray)):
            try:
                tags = Field55.unpack(value)
                fields[str(fnum)] = {
                    "_type": "f55",
                    "tags": {k.hex().upper(): v.hex().upper() for k, v in tags.items()},
                }
                continue
            except Exception:
                pass

        if fnum == 111 and isinstance(value, (bytes, bytearray)):
            try:
                datasets = Field111.unpack(value)
                ds_list = []
                for ds in datasets:
                    ds_list.append({
                        "id": f"{ds.dataset_id:02X}",
                        "tags": {f"{t:02X}": v.hex().upper() for t, v in ds.elements.items()},
                    })
                fields[str(fnum)] = {"_type": "f111", "datasets": ds_list}
                continue
            except Exception:
                pass

        if fnum == 113 and isinstance(value, (bytes, bytearray)):
            try:
                tags = Field113.unpack(value)
                fields[str(fnum)] = {
                    "_type": "f113",
                    "tags": {k: v.hex().upper() for k, v in tags.items()},
                }
                continue
            except Exception:
                pass

        # Default: string or hex
        if isinstance(value, (bytes, bytearray)):
            fields[str(fnum)] = value.hex().upper()
        else:
            fields[str(fnum)] = str(value)

    return {
        "mti": msg.mti,
        "fields": fields,
    }


def _encode_message(mti: str, fields: dict[str, object]) -> dict:
    """Encode an MTI + fields dict into a hex string."""
    msg = AS2805Message(mti=mti)
    for fnum_str, value in fields.items():
        fnum = int(fnum_str)
        if fnum == 1:
            continue
        spec = ELS_SCHEMA.get(fnum)

        # Structured tag data
        if isinstance(value, dict) and "_type" in value:
            vtype = value["_type"]
            if vtype == "f47":
                tag_dict = {k: v.encode("ascii") for k, v in value.get("tags", {}).items()}
                # Field 47 is ans (string), so decode the packed bytes
                msg[fnum] = Field47.pack(tag_dict).decode("ascii")
            elif vtype == "f55":
                tag_dict = {bytes.fromhex(k): bytes.fromhex(v) for k, v in value.get("tags", {}).items()}
                msg[fnum] = Field55.pack(tag_dict)
            elif vtype == "f111":
                datasets = []
                for ds_data in value.get("datasets", []):
                    ds_id = int(ds_data["id"], 16)
                    elements = {int(t, 16): bytes.fromhex(v) for t, v in ds_data.get("tags", {}).items()}
                    datasets.append(DataSet(dataset_id=ds_id, elements=elements))
                msg[fnum] = Field111.pack(datasets)
            elif vtype == "f113":
                tag_dict = {k: bytes.fromhex(v) for k, v in value.get("tags", {}).items()}
                msg[fnum] = Field113.pack(tag_dict)
            continue

        # Plain string value (backward compat)
        if isinstance(value, str):
            if spec.field_type == "b":
                msg[fnum] = bytes.fromhex(value)
            else:
                msg[fnum] = value

    raw = msg.pack()
    return {"hex": raw.hex().upper()}


class KerryHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Kerry app."""

    def log_message(self, format, *args):
        # Quieter logging
        pass

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length)

    def do_GET(self) -> None:
        if self.path == "/":
            self._send_html(HTML_PAGE)
        elif self.path == "/api/schema":
            self._send_json(json.loads(SCHEMA_JSON))
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        try:
            body = json.loads(self._read_body())
        except (json.JSONDecodeError, ValueError) as e:
            self._send_json({"error": str(e)}, 400)
            return

        if self.path == "/api/decode":
            try:
                result = _decode_message(body.get("hex", ""))
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, 400)

        elif self.path == "/api/encode":
            try:
                result = _encode_message(body.get("mti", ""), body.get("fields", {}))
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, 400)

        else:
            self.send_error(404)


# ---------------------------------------------------------------------------
# Embedded HTML page
# ---------------------------------------------------------------------------

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kerry — AS2805 Message Tool</title>
<style>
:root {
    --bg: #f5f6fa;
    --card: #ffffff;
    --border: #dcdde1;
    --accent: #2f3640;
    --blue: #0984e3;
    --red: #d63031;
    --green: #00b894;
    --muted: #636e72;
    --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --mono: "Cascadia Code", "Fira Code", "Consolas", monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font); background: var(--bg); color: var(--accent); padding: 20px; }
h1 { font-size: 1.5rem; margin-bottom: 4px; }
h1 span { color: var(--muted); font-weight: 400; font-size: 0.85rem; }
.container { max-width: 960px; margin: 0 auto; }

/* Top section */
.hex-section {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}
.hex-section label { font-weight: 600; display: block; margin-bottom: 6px; }
#hex-input {
    width: 100%;
    min-height: 80px;
    font-family: var(--mono);
    font-size: 0.85rem;
    padding: 10px;
    border: 1px solid var(--border);
    border-radius: 4px;
    resize: vertical;
    line-height: 1.5;
}
.btn-row { margin-top: 10px; display: flex; gap: 10px; align-items: center; }
.btn {
    padding: 8px 20px;
    border: none;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
}
.btn:hover { opacity: 0.85; }
.btn-decode { background: var(--blue); color: #fff; }
.btn-encode { background: var(--green); color: #fff; }
.btn-clear { background: var(--border); color: var(--accent); }
.btn-randomize { background: #6c5ce7; color: #fff; }
#error-msg { color: var(--red); font-size: 0.85rem; margin-left: 10px; }
#ascii-dump {
    width: 100%;
    font-family: var(--mono);
    font-size: 0.78rem;
    line-height: 1.4;
    padding: 8px 10px;
    margin-top: 8px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: #f8f9fa;
    color: var(--muted);
    white-space: pre;
    overflow-x: auto;
    max-height: 200px;
    overflow-y: auto;
}
#ascii-dump:empty { display: none; }

/* Bottom section */
.fields-section {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
}
.mti-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}
.mti-row label { font-weight: 600; }
#mti-select {
    padding: 6px 10px;
    font-size: 0.85rem;
    border: 1px solid var(--border);
    border-radius: 4px;
    min-width: 320px;
}
#mti-desc { color: var(--muted); font-size: 0.85rem; }

.field-table { width: 100%; border-collapse: collapse; }
.field-table th {
    text-align: left;
    padding: 6px 8px;
    border-bottom: 2px solid var(--border);
    font-size: 0.75rem;
    text-transform: uppercase;
    color: var(--muted);
}
.field-table td {
    padding: 4px 8px;
    border-bottom: 1px solid var(--border);
    font-size: 0.85rem;
    vertical-align: top;
}
.field-table tr.hidden { display: none; }
.field-table tr.mandatory td:first-child { font-weight: 700; }
.field-num { font-family: var(--mono); color: var(--muted); min-width: 36px; }
.field-name { min-width: 200px; }
.field-type { font-family: var(--mono); color: var(--muted); font-size: 0.75rem; min-width: 100px; }
.field-input {
    width: 100%;
    padding: 4px 6px;
    font-family: var(--mono);
    font-size: 0.82rem;
    border: 1px solid var(--border);
    border-radius: 3px;
}
.field-input:focus { outline: 2px solid var(--blue); border-color: transparent; }
.field-input.error { border-color: var(--red); }
.rule-badge {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 0.7rem;
    font-weight: 600;
}
.rule-M { background: #dfe6e9; color: var(--accent); }
.rule-C { background: #ffeaa7; color: #6c5200; }
.rule-O { background: #e8f8f5; color: #00695c; }

/* Tag sub-editor styles */
.tag-container {
    width: 100%;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 6px;
    background: #fafbfc;
}
.tag-row {
    display: flex;
    gap: 4px;
    align-items: center;
    margin-bottom: 3px;
}
.tag-row select {
    font-family: var(--mono);
    font-size: 0.78rem;
    padding: 3px 4px;
    border: 1px solid var(--border);
    border-radius: 3px;
    min-width: 100px;
}
.tag-row input {
    flex: 1;
    font-family: var(--mono);
    font-size: 0.78rem;
    padding: 3px 4px;
    border: 1px solid var(--border);
    border-radius: 3px;
}
.tag-row .tag-name-hint {
    font-size: 0.7rem;
    color: var(--muted);
    min-width: 120px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.btn-tag {
    padding: 2px 8px;
    border: 1px solid var(--border);
    border-radius: 3px;
    font-size: 0.75rem;
    cursor: pointer;
    background: #fff;
}
.btn-tag:hover { background: #eee; }
.btn-tag-remove { color: var(--red); }
.btn-tag-add { color: var(--green); margin-top: 3px; }
.dataset-group {
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 6px;
    margin-bottom: 4px;
    background: #fff;
}
.dataset-header {
    display: flex;
    gap: 6px;
    align-items: center;
    margin-bottom: 4px;
    font-size: 0.78rem;
    font-weight: 600;
}
.dataset-header select {
    font-family: var(--mono);
    font-size: 0.78rem;
    padding: 2px 4px;
    border: 1px solid var(--border);
    border-radius: 3px;
}

/* Processing code dropdowns */
.pc-container { display: flex; flex-direction: column; gap: 3px; }
.pc-row { display: flex; align-items: center; gap: 6px; }
.pc-row label { font-size: 0.78rem; color: var(--muted); min-width: 80px; }
.pc-row select {
    font-family: var(--mono);
    font-size: 0.78rem;
    padding: 3px 4px;
    border: 1px solid var(--border);
    border-radius: 3px;
    flex: 1;
}

.encode-row { margin-top: 12px; display: flex; gap: 10px; }
footer { text-align: center; margin-top: 20px; color: var(--muted); font-size: 0.75rem; }
</style>
</head>
<body>
<div class="container">
    <h1>Kerry <span>AS2805 Message Tool</span></h1>

    <div class="hex-section">
        <label for="hex-input">Raw Hex</label>
        <textarea id="hex-input" oninput="updateAsciiDump()" placeholder="Paste hex digits here (whitespace and punctuation ignored)..."></textarea>
        <div id="ascii-dump"></div>
        <div class="btn-row">
            <button class="btn btn-decode" onclick="doDecode()">DECODE</button>
            <button class="btn btn-clear" onclick="doClear()">CLEAR</button>
            <span id="error-msg"></span>
        </div>
    </div>

    <div class="fields-section">
        <div class="mti-row">
            <label for="mti-select">MTI</label>
            <select id="mti-select" onchange="onMtiChange()"></select>
            <span id="mti-desc"></span>
        </div>

        <table class="field-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Field</th>
                    <th>Type</th>
                    <th>Rule</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody id="field-tbody"></tbody>
        </table>

        <div class="encode-row">
            <button class="btn btn-encode" onclick="doEncode()">ENCODE</button>
            <button class="btn btn-randomize" onclick="doRandomize()">RANDOMIZE</button>
        </div>
    </div>

    <footer>Kerry &mdash; powered by as2805-msg</footer>
</div>

<script>
let SCHEMA = null; // {fields, mti_names, rules, tag_fields}
const TAG_FIELD_NUMS = new Set(["47", "55", "111", "113"]);

async function init() {
    const resp = await fetch("/api/schema");
    SCHEMA = await resp.json();
    buildMtiSelect();
    buildFieldRows();
    onMtiChange();
}

function buildMtiSelect() {
    const sel = document.getElementById("mti-select");
    const sorted = Object.entries(SCHEMA.mti_names).sort((a, b) => a[0].localeCompare(b[0]));
    for (const [code, name] of sorted) {
        const opt = document.createElement("option");
        opt.value = code;
        opt.textContent = code + " — " + name;
        sel.appendChild(opt);
    }
}

function buildFieldRows() {
    const tbody = document.getElementById("field-tbody");
    const sortedFields = Object.entries(SCHEMA.fields)
        .sort((a, b) => parseInt(a[0]) - parseInt(b[0]));

    for (const [fnum, spec] of sortedFields) {
        const tr = document.createElement("tr");
        tr.id = "field-row-" + fnum;
        tr.dataset.fnum = fnum;

        const typeStr = spec.type + " " + spec.max_length + " " + spec.length_type;

        // Build value cell content
        let valueCell;
        if (fnum === "3") {
            valueCell = '<td>' + buildProcessingCodeSelect() + '</td>';
        } else if (TAG_FIELD_NUMS.has(fnum)) {
            valueCell = '<td class="value-cell" id="value-cell-' + fnum + '">' + buildTagContainer(fnum) + '</td>';
        } else {
            let placeholder = "";
            if (spec.type === "b") placeholder = "hex bytes";
            else if (spec.type === "n") placeholder = "digits";
            else if (spec.type === "z") placeholder = "digits + D";
            else if (spec.type === "x+n" || spec.type === "x+n*") placeholder = "C or D + digits";
            else placeholder = "text";

            valueCell = '<td><input class="field-input" id="input-' + fnum + '" ' +
                'placeholder="' + placeholder + '" data-fnum="' + fnum + '"></td>';
        }

        tr.innerHTML =
            '<td class="field-num">' + fnum + '</td>' +
            '<td class="field-name">' + escHtml(spec.name) + '</td>' +
            '<td class="field-type">' + escHtml(typeStr) + '</td>' +
            '<td class="field-rule"><span class="rule-badge" id="rule-' + fnum + '"></span></td>' +
            valueCell;

        tbody.appendChild(tr);
    }
}

function buildProcessingCodeSelect() {
    const pc = SCHEMA.processing_code;
    let html = '<div class="pc-container" id="pc-container">';
    // Transaction type (positions 1-2)
    html += '<div class="pc-row"><label>Transaction:</label><select id="pc-txn-type">';
    for (const [code, name] of Object.entries(pc.transaction_types)) {
        html += '<option value="' + code + '">' + code + ' ' + escHtml(name) + '</option>';
    }
    html += '</select></div>';
    // Source account (positions 3-4)
    html += '<div class="pc-row"><label>From:</label><select id="pc-src-acct">';
    for (const [code, name] of Object.entries(pc.account_types)) {
        html += '<option value="' + code + '">' + code + ' ' + escHtml(name) + '</option>';
    }
    html += '</select></div>';
    // Destination account (positions 5-6)
    html += '<div class="pc-row"><label>To:</label><select id="pc-dst-acct">';
    for (const [code, name] of Object.entries(pc.account_types)) {
        html += '<option value="' + code + '">' + code + ' ' + escHtml(name) + '</option>';
    }
    html += '</select></div>';
    html += '</div>';
    return html;
}

function getProcessingCode() {
    const txn = document.getElementById("pc-txn-type");
    const src = document.getElementById("pc-src-acct");
    const dst = document.getElementById("pc-dst-acct");
    if (!txn || !src || !dst) return "";
    return txn.value + src.value + dst.value;
}

function setProcessingCode(value) {
    if (!value || value.length !== 6) return;
    const txn = document.getElementById("pc-txn-type");
    const src = document.getElementById("pc-src-acct");
    const dst = document.getElementById("pc-dst-acct");
    if (txn) txn.value = value.substring(0, 2);
    if (src) src.value = value.substring(2, 4);
    if (dst) dst.value = value.substring(4, 6);
}

function buildTagContainer(fnum) {
    const tf = SCHEMA.tag_fields[fnum];
    if (!tf) return '<input class="field-input" id="input-' + fnum + '" data-fnum="' + fnum + '">';

    if (fnum === "111") {
        return '<div class="tag-container" id="tag-container-' + fnum + '">' +
            '<button class="btn-tag btn-tag-add" onclick="addDatasetGroup(\'' + fnum + '\')">+ Data Set</button>' +
            '</div>';
    }

    return '<div class="tag-container" id="tag-container-' + fnum + '">' +
        '<button class="btn-tag btn-tag-add" onclick="addTagRow(\'' + fnum + '\')">+ Tag</button>' +
        '</div>';
}

function makeTagSelect(fnum, selectedTag) {
    const tf = SCHEMA.tag_fields[fnum];
    if (!tf) return '';
    const tags = tf.tags || {};
    let html = '<select onchange="onTagSelectChange(this)">';
    html += '<option value="">-- tag --</option>';
    for (const [k, v] of Object.entries(tags)) {
        const sel = (k === selectedTag) ? ' selected' : '';
        html += '<option value="' + escHtml(k) + '"' + sel + '>' + escHtml(k) + ' ' + escHtml(v) + '</option>';
    }
    html += '<option value="__custom__">Custom...</option>';
    html += '</select>';
    return html;
}

function addTagRow(fnum, tagKey, tagValue) {
    const container = document.getElementById("tag-container-" + fnum);
    const addBtn = container.querySelector(".btn-tag-add");

    const row = document.createElement("div");
    row.className = "tag-row";

    const tf = SCHEMA.tag_fields[fnum];
    const tagNames = tf ? tf.tags || {} : {};
    const nameHint = (tagKey && tagNames[tagKey]) ? tagNames[tagKey] : "";

    row.innerHTML =
        makeTagSelect(fnum, tagKey || "") +
        '<input class="tag-custom-key" placeholder="tag" style="width:60px;display:none;" value="' + escHtml(tagKey || "") + '">' +
        '<input class="tag-value" placeholder="value" value="' + escHtml(tagValue || "") + '">' +
        '<span class="tag-name-hint">' + escHtml(nameHint) + '</span>' +
        '<button class="btn-tag btn-tag-remove" onclick="this.parentElement.remove()">x</button>';

    container.insertBefore(row, addBtn);

    // If tagKey is custom (not in known list), show custom input
    const sel = row.querySelector("select");
    const customInput = row.querySelector(".tag-custom-key");
    if (tagKey && sel) {
        const found = Array.from(sel.options).some(o => o.value === tagKey);
        if (!found && tagKey) {
            sel.value = "__custom__";
            customInput.style.display = "";
            customInput.value = tagKey;
        }
    }
}

function onTagSelectChange(sel) {
    const row = sel.parentElement;
    const customInput = row.querySelector(".tag-custom-key");
    const hint = row.querySelector(".tag-name-hint");
    if (sel.value === "__custom__") {
        customInput.style.display = "";
        customInput.value = "";
        customInput.focus();
        hint.textContent = "";
    } else {
        customInput.style.display = "none";
        customInput.value = sel.value;
        // Update hint
        const fnum = sel.closest(".tag-container").id.replace("tag-container-", "");
        const tf = SCHEMA.tag_fields[fnum];
        hint.textContent = (tf && tf.tags && tf.tags[sel.value]) || "";
    }
}

function addDatasetGroup(fnum, dsId, tagsObj) {
    const container = document.getElementById("tag-container-" + fnum);
    const addBtn = container.querySelector(".btn-tag-add");

    const group = document.createElement("div");
    group.className = "dataset-group";

    const tf = SCHEMA.tag_fields[fnum];
    const dsNames = tf ? tf.datasets || {} : {};

    let dsSelectHtml = '<select class="ds-id-select">';
    for (const [k, v] of Object.entries(dsNames)) {
        const sel = (k === (dsId || "")) ? ' selected' : '';
        dsSelectHtml += '<option value="' + escHtml(k) + '"' + sel + '>' + escHtml(k) + ' ' + escHtml(v) + '</option>';
    }
    dsSelectHtml += '</select>';

    group.innerHTML =
        '<div class="dataset-header">' +
        'Data Set: ' + dsSelectHtml +
        '<button class="btn-tag btn-tag-remove" onclick="this.closest(\'.dataset-group\').remove()">x</button>' +
        '</div>' +
        '<div class="ds-tags"></div>' +
        '<button class="btn-tag btn-tag-add" onclick="addDsTagRow(this.parentElement)">+ Tag</button>';

    container.insertBefore(group, addBtn);

    // Add existing tags
    if (tagsObj) {
        for (const [k, v] of Object.entries(tagsObj)) {
            addDsTagRow(group, k, v);
        }
    }
}

function addDsTagRow(groupEl, tagKey, tagValue) {
    const tagsDiv = groupEl.querySelector(".ds-tags");
    const tf = SCHEMA.tag_fields["111"];
    const tagNames = tf ? tf.tags || {} : {};
    const nameHint = (tagKey && tagNames[tagKey]) ? tagNames[tagKey] : "";

    const row = document.createElement("div");
    row.className = "tag-row";

    // Build select for F111 tags
    let selHtml = '<select onchange="onF111TagSelectChange(this)">';
    selHtml += '<option value="">-- tag --</option>';
    for (const [k, v] of Object.entries(tagNames)) {
        const sel = (k === (tagKey || "")) ? ' selected' : '';
        selHtml += '<option value="' + escHtml(k) + '"' + sel + '>' + escHtml(k) + ' ' + escHtml(v) + '</option>';
    }
    selHtml += '<option value="__custom__">Custom...</option>';
    selHtml += '</select>';

    row.innerHTML =
        selHtml +
        '<input class="tag-custom-key" placeholder="tag" style="width:50px;display:none;" value="' + escHtml(tagKey || "") + '">' +
        '<input class="tag-value" placeholder="hex value" value="' + escHtml(tagValue || "") + '">' +
        '<span class="tag-name-hint">' + escHtml(nameHint) + '</span>' +
        '<button class="btn-tag btn-tag-remove" onclick="this.parentElement.remove()">x</button>';

    tagsDiv.appendChild(row);

    // If tagKey is custom, show custom input
    const sel = row.querySelector("select");
    const customInput = row.querySelector(".tag-custom-key");
    if (tagKey && sel) {
        const found = Array.from(sel.options).some(o => o.value === tagKey);
        if (!found && tagKey) {
            sel.value = "__custom__";
            customInput.style.display = "";
            customInput.value = tagKey;
        }
    }
}

function onF111TagSelectChange(sel) {
    const row = sel.parentElement;
    const customInput = row.querySelector(".tag-custom-key");
    const hint = row.querySelector(".tag-name-hint");
    if (sel.value === "__custom__") {
        customInput.style.display = "";
        customInput.value = "";
        customInput.focus();
        hint.textContent = "";
    } else {
        customInput.style.display = "none";
        customInput.value = sel.value;
        const tf = SCHEMA.tag_fields["111"];
        hint.textContent = (tf && tf.tags && tf.tags[sel.value]) || "";
    }
}

// Collect tag data from a tag container
function collectTagData(fnum) {
    const container = document.getElementById("tag-container-" + fnum);
    if (!container) return null;

    if (fnum === "111") {
        const groups = container.querySelectorAll(".dataset-group");
        if (groups.length === 0) return null;
        const datasets = [];
        groups.forEach(g => {
            const dsId = g.querySelector(".ds-id-select").value;
            const tags = {};
            g.querySelectorAll(".tag-row").forEach(row => {
                const sel = row.querySelector("select");
                const customInput = row.querySelector(".tag-custom-key");
                const valInput = row.querySelector(".tag-value");
                let key = sel.value === "__custom__" ? customInput.value.trim() : sel.value;
                const val = valInput.value.trim();
                if (key && val) tags[key.toUpperCase()] = val;
            });
            if (dsId && Object.keys(tags).length > 0) {
                datasets.push({id: dsId, tags: tags});
            }
        });
        if (datasets.length === 0) return null;
        return {_type: "f111", datasets: datasets};
    }

    // F47, F55, F113
    const rows = container.querySelectorAll(".tag-row");
    if (rows.length === 0) return null;
    const tags = {};
    rows.forEach(row => {
        const sel = row.querySelector("select");
        const customInput = row.querySelector(".tag-custom-key");
        const valInput = row.querySelector(".tag-value");
        let key = sel.value === "__custom__" ? customInput.value.trim() : sel.value;
        const val = valInput.value.trim();
        if (key && val) {
            if (fnum === "55") key = key.toUpperCase();
            tags[key] = val;
        }
    });
    if (Object.keys(tags).length === 0) return null;

    const typeMap = {"47": "f47", "55": "f55", "113": "f113"};
    return {_type: typeMap[fnum], tags: tags};
}

// Populate tag container from decoded structured data
function populateTagData(fnum, data) {
    clearTagContainer(fnum);

    if (fnum === "111" && data._type === "f111") {
        for (const ds of (data.datasets || [])) {
            addDatasetGroup("111", ds.id, ds.tags);
        }
        return;
    }

    if (data.tags) {
        for (const [k, v] of Object.entries(data.tags)) {
            addTagRow(fnum, k, v);
        }
    }
}

function clearTagContainer(fnum) {
    const container = document.getElementById("tag-container-" + fnum);
    if (!container) return;
    // Remove all tag rows and dataset groups, keep the add button
    const addBtn = container.querySelector(":scope > .btn-tag-add");
    while (container.firstChild) container.removeChild(container.firstChild);
    if (addBtn) container.appendChild(addBtn);
}

function onMtiChange() {
    const mti = document.getElementById("mti-select").value;
    const rules = SCHEMA.rules[mti] || {};

    for (const [fnum, spec] of Object.entries(SCHEMA.fields)) {
        const row = document.getElementById("field-row-" + fnum);
        const badge = document.getElementById("rule-" + fnum);
        const rule = rules[fnum];

        if (rule) {
            row.classList.remove("hidden");
            row.classList.toggle("mandatory", rule === "M");
            badge.textContent = rule;
            badge.className = "rule-badge rule-" + rule;
        } else {
            row.classList.add("hidden");
            badge.textContent = "";
        }
    }

    document.getElementById("mti-desc").textContent = SCHEMA.mti_names[mti] || "";
}

async function doDecode() {
    clearError();
    const hex = document.getElementById("hex-input").value.trim();
    if (!hex) { showError("No hex data to decode"); return; }

    try {
        const resp = await fetch("/api/decode", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({hex: hex}),
        });
        const data = await resp.json();
        if (data.error) { showError(data.error); return; }

        document.getElementById("mti-select").value = data.mti;
        onMtiChange();
        clearFieldInputs();

        for (const [fnum, value] of Object.entries(data.fields)) {
            if (fnum === "3" && typeof value === "string") {
                setProcessingCode(value);
                const row = document.getElementById("field-row-3");
                if (row) row.classList.remove("hidden");
            } else if (TAG_FIELD_NUMS.has(fnum) && typeof value === "object" && value._type) {
                populateTagData(fnum, value);
                const row = document.getElementById("field-row-" + fnum);
                if (row) row.classList.remove("hidden");
            } else {
                const input = document.getElementById("input-" + fnum);
                if (input) {
                    input.value = (typeof value === "string") ? value : JSON.stringify(value);
                    const row = document.getElementById("field-row-" + fnum);
                    if (row) row.classList.remove("hidden");
                }
            }
        }
    } catch (e) {
        showError("Decode failed: " + e.message);
    }
}

async function doEncode() {
    clearError();
    const mti = document.getElementById("mti-select").value;
    const fields = {};

    // Collect plain field inputs
    document.querySelectorAll(".field-input").forEach(input => {
        const fnum = input.dataset.fnum;
        const row = document.getElementById("field-row-" + fnum);
        if (!row || row.classList.contains("hidden")) return;
        if (input.value.trim() !== "") {
            fields[fnum] = input.value.trim();
        }
    });

    // Collect processing code from dropdowns
    const pcRow = document.getElementById("field-row-3");
    if (pcRow && !pcRow.classList.contains("hidden")) {
        const pc = getProcessingCode();
        if (pc) fields["3"] = pc;
    }

    // Collect tag field data
    for (const fnum of TAG_FIELD_NUMS) {
        const row = document.getElementById("field-row-" + fnum);
        if (!row || row.classList.contains("hidden")) continue;
        const tagData = collectTagData(fnum);
        if (tagData) fields[fnum] = tagData;
    }

    try {
        const resp = await fetch("/api/encode", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({mti: mti, fields: fields}),
        });
        const data = await resp.json();
        if (data.error) { showError(data.error); return; }

        document.getElementById("hex-input").value = data.hex;
        updateAsciiDump();
    } catch (e) {
        showError("Encode failed: " + e.message);
    }
}

function doClear() {
    document.getElementById("hex-input").value = "";
    clearFieldInputs();
    clearError();
    updateAsciiDump();
}

function clearFieldInputs() {
    document.querySelectorAll(".field-input").forEach(input => { input.value = ""; });
    // Clear tag containers
    for (const fnum of TAG_FIELD_NUMS) {
        clearTagContainer(fnum);
    }
    // Reset processing code dropdowns
    setProcessingCode("000000");
}

function showError(msg) { document.getElementById("error-msg").textContent = msg; }
function clearError() { document.getElementById("error-msg").textContent = ""; }

function escHtml(s) {
    if (!s) return "";
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}

function updateAsciiDump() {
    const el = document.getElementById("ascii-dump");
    const inp = document.getElementById("hex-input");
    // Uppercase hex digits in the textarea
    const cursorPos = inp.selectionStart;
    const upper = inp.value.toUpperCase();
    if (inp.value !== upper) { inp.value = upper; inp.selectionStart = inp.selectionEnd = cursorPos; }
    const hex = upper.replace(/[^0-9A-F]/g, "");
    if (!hex || hex.length < 2) { el.textContent = ""; return; }
    // Convert hex pairs to bytes, show as hex + ASCII side by side (16 bytes per line)
    const bytes = [];
    for (let i = 0; i + 1 < hex.length; i += 2) {
        bytes.push(parseInt(hex.substr(i, 2), 16));
    }
    const lines = [];
    for (let off = 0; off < bytes.length; off += 16) {
        const chunk = bytes.slice(off, off + 16);
        // Offset
        const addr = off.toString(16).toUpperCase().padStart(4, "0");
        // Hex part: groups of 2 bytes separated by spaces, extra space at byte 8
        let hexPart = "";
        for (let i = 0; i < 16; i++) {
            if (i === 8) hexPart += " ";
            if (i < chunk.length) hexPart += chunk[i].toString(16).toUpperCase().padStart(2, "0") + " ";
            else hexPart += "   ";
        }
        // ASCII part
        let asciiPart = "";
        for (let i = 0; i < chunk.length; i++) {
            const b = chunk[i];
            asciiPart += (b >= 0x20 && b <= 0x7E) ? String.fromCharCode(b) : ".";
        }
        lines.push(addr + "  " + hexPart + " " + asciiPart);
    }
    el.textContent = lines.join("\n");
}

// --- Randomize ---

function doRandomize() {
    clearError();
    clearFieldInputs();
    const mti = document.getElementById("mti-select").value;
    const rules = SCHEMA.rules[mti] || {};

    const now = new Date();
    const pad = (n, w) => String(n).padStart(w, "0");
    const MM = pad(now.getMonth() + 1, 2);
    const DD = pad(now.getDate(), 2);
    const hh = pad(now.getHours(), 2);
    const mm = pad(now.getMinutes(), 2);
    const ss = pad(now.getSeconds(), 2);
    const stan = pad(Math.floor(Math.random() * 999999) + 1, 6);
    const randDigits = (n) => Array.from({length: n}, () => Math.floor(Math.random() * 10)).join("");
    const randHex = (nBytes) => Array.from({length: nBytes}, () => pad(Math.floor(Math.random() * 256).toString(16), 2)).join("");
    const randAlpha = (n) => Array.from({length: n}, () => "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"[Math.floor(Math.random() * 36)]).join("");

    // Tag randomizers for composite fields
    const tagRandomizers = {
        "47": () => {
            const allTags = [
                {tag: "ARI", type: "an", maxLen: 3},
                {tag: "TCC", type: "an", maxLen: 2},
                {tag: "FCR", type: "an", maxLen: 1},
                {tag: "PCA", type: "n",  maxLen: 4},
                {tag: "FCA", type: "an", maxLen: 2},
                {tag: "BAI", type: "an", maxLen: 2},
                {tag: "CTP", type: "an", maxLen: 2},
                {tag: "FSC", type: "n",  maxLen: 4},
                {tag: "FCC", type: "an", maxLen: 4},
                {tag: "ECM", type: "an", maxLen: 2},
                {tag: "DCP", type: "an", maxLen: 2},
            ];
            const shuffled = allTags.sort(() => Math.random() - 0.5);
            const count = 2 + Math.floor(Math.random() * 3);
            const chosen = shuffled.slice(0, count);
            for (const t of chosen) {
                let value;
                if (t.type === "n") {
                    value = randDigits(t.maxLen);
                } else {
                    value = randAlpha(t.maxLen);
                }
                addTagRow("47", t.tag, value);
            }
        },
        "55": () => {
            const emvTags = [
                {tag: "9F26", len: 8},
                {tag: "9F27", len: 1},
                {tag: "9F10", len: 7},
                {tag: "9F37", len: 4},
                {tag: "9F36", len: 2},
                {tag: "9F02", len: 6},
                {tag: "9F03", len: 6},
                {tag: "9F1A", len: 2},
                {tag: "5F2A", len: 2},
                {tag: "9A",   len: 3},
                {tag: "9C",   len: 1},
            ];
            for (const t of emvTags) {
                addTagRow("55", t.tag, randHex(t.len));
            }
        },
        "111": () => {
            // MAC data set (02) with a few tags
            addDatasetGroup("111", "02", {
                "80": "02",
                "81": "00000000",
                "83": "06",
            });
        },
        "113": () => {
            addTagRow("113", "001", randHex(11));
            addTagRow("113", "002", randHex(24));
        },
    };

    // Sensible per-field random data generators for non-tag fields
    const generators = {
        "2":  () => "4" + randDigits(15),
        "4":  () => pad(Math.floor(Math.random() * 100000) + 100, 12),
        "7":  () => MM + DD + hh + mm + ss,
        "11": () => stan,
        "12": () => hh + mm + ss,
        "13": () => MM + DD,
        "14": () => pad(now.getFullYear() % 100 + 2, 2) + MM,
        "15": () => MM + DD,
        "18": () => "5411",
        "22": () => "051",
        "23": () => "001",
        "25": () => "00",
        "28": () => "C" + pad(0, 8),
        "30": () => "C" + pad(0, 8),
        "32": () => randDigits(6),
        "33": () => randDigits(6),
        "35": () => "4" + randDigits(15) + "D" + pad(now.getFullYear() % 100 + 2, 2) + MM + "101" + randDigits(8),
        "37": () => randAlpha(12),
        "38": () => randAlpha(6),
        "39": () => "00",
        "41": () => "TERM" + randDigits(4),
        "42": () => randAlpha(15),
        "43": () => ("STORE " + randDigits(4)).padEnd(25) + "SYDNEY".padEnd(13) + "AU",
        "44": () => randAlpha(6),
        "48": () => randAlpha(10),
        "52": () => randHex(8),
        "53": () => "2600000000000000",
        "54": () => randAlpha(12),
        "57": () => pad(Math.floor(Math.random() * 50000) + 100, 12),
        "58": () => "C" + pad(Math.floor(Math.random() * 1000000), 12),
        "59": () => "C" + pad(Math.floor(Math.random() * 1000000), 12),
        "64": () => randHex(8),
        "66": () => "1",
        "70": () => "001",
        "90": () => "0200" + stan + MM + DD + hh + mm + ss + pad(randDigits(6), 11) + pad(randDigits(6), 11),
        "95": () => randAlpha(42),
        "100": () => randDigits(6),
        "128": () => randHex(8),
    };

    for (const [fnum, rule] of Object.entries(rules)) {
        const row = document.getElementById("field-row-" + fnum);
        if (!row || row.classList.contains("hidden")) continue;

        if (rule === "M" || rule === "C") {
            // Processing code: set dropdowns directly
            if (fnum === "3") {
                const txnTypes = Object.keys(SCHEMA.processing_code.transaction_types);
                const acctTypes = Object.keys(SCHEMA.processing_code.account_types);
                const rndTxn = txnTypes[Math.floor(Math.random() * txnTypes.length)];
                const rndSrc = acctTypes[Math.floor(Math.random() * acctTypes.length)];
                const rndDst = acctTypes[Math.floor(Math.random() * acctTypes.length)];
                setProcessingCode(rndTxn + rndSrc + rndDst);
                continue;
            }

            // Tag fields use tag randomizers
            if (TAG_FIELD_NUMS.has(fnum) && tagRandomizers[fnum]) {
                tagRandomizers[fnum]();
                continue;
            }

            const input = document.getElementById("input-" + fnum);
            if (!input) continue;

            const gen = generators[fnum];
            if (gen) {
                input.value = gen();
            } else {
                const spec = SCHEMA.fields[fnum];
                if (spec) input.value = fallbackRandom(spec);
            }
        }
    }
}

function fallbackRandom(spec) {
    const n = spec.max_length;
    const randDigits = (len) => Array.from({length: len}, () => Math.floor(Math.random() * 10)).join("");
    const randHex = (nBytes) => Array.from({length: nBytes}, () => Math.floor(Math.random() * 256).toString(16).padStart(2, "0")).join("");

    if (spec.type === "n") return randDigits(n);
    if (spec.type === "b") return randHex(n);
    if (spec.type === "z") return randDigits(Math.min(n, 16)) + "D" + randDigits(4);
    if (spec.type === "x+n" || spec.type === "x+n*") return "C" + randDigits(n);
    return Array.from({length: Math.min(n, 12)}, () => "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"[Math.floor(Math.random() * 36)]).join("");
}

init();
</script>
</body>
</html>
"""


def main():
    port = 8080
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:]):
            if arg == "--port" and i + 2 < len(sys.argv):
                port = int(sys.argv[i + 2])
            elif arg.isdigit():
                port = int(arg)

    server = HTTPServer(("127.0.0.1", port), KerryHandler)
    print(f"Kerry running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()

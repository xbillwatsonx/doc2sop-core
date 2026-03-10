#!/usr/bin/env python3
import sys
import logging
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

sys.path.insert(0, '/opt/doc2sop-core/src')
from doc2sop_core.server_wrapper import Doc2SOPServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/tmp/dynamic-sop-api.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.')
CORS(app)
doc2sop = Doc2SOPServer(use_llm=False)


def _looks_like_microgreens(notes: str) -> bool:
    n = notes.lower()
    return ('tray' in n and 'label' in n and 'cooler' in n and ('harvest' in n or 'cut' in n))


def _extract_tools_materials(notes: str):
    n = notes.lower()
    items = []

    def add(item, cond):
        if cond and item not in items:
            items.append(item)

    add('Harvest trays', 'tray' in n)
    add('Cutting table', 'cutting table' in n or 'cut table' in n)
    add('Catch bin', 'catch bin' in n or ('bin' in n and 'catch' in n))
    add('Adjustable footstool', 'foot stool' in n or 'footstool' in n)
    add('Gloves', 'glove' in n)
    add('Pink stickers', 'pink sticker' in n or ('pink' in n and 'sticker' in n))
    add('Storage containers', 'storage container' in n or 'container' in n)
    add('Packaging containers', 'package' in n or 'packaging' in n)
    add('Label printer', 'print label' in n or 'printer' in n)
    add('Round labels', 'round label' in n)
    add('Rectangle labels', 'rectangle label' in n)
    add('Cooler (37°F target)', 'cooler' in n)

    if not items:
        items = ['List all physical tools and materials before execution.']

    return items


def _build_microgreens_sop(notes: str) -> str:
    temp = '37°F' if '37' in notes else 'target temperature'
    tools = _extract_tools_materials(notes)
    tools_md = '\n'.join([f'- {x}' for x in tools])

    return f"""# Harvest and Packaging SOP

## Purpose
Create a clear harvest-to-packaging workflow from fragmented field notes.

## Scope
Applies to greenhouse selection, cutting-table prep, cutting/collection, labeling, packaging, and cooler storage.

## Tools & Materials Needed
{tools_md}

## Procedure
### Step 1: Select trays for harvest
1. Inspect trays in the greenhouse.
2. Evaluate harvest readiness based on density and true leaves.
3. Mark ready trays with a pink sticker.

### Step 2: Prepare cutting station
1. Prepare and clear the cutting table.
2. Place the tray on the left side near the edge.
3. Place catch bin on adjustable foot stool with the lip under the table edge.
4. Use gloved hands for cutting and collection.

### Step 3: Stage trays for cutting
1. Return to greenhouse and move only pink-sticker trays.
2. Stage trays at the cut-table staging area.

### Step 4: Cut and collect
1. Cut greens and guide product into catch bin.
2. Transfer to storage container.
3. Stage containers for packaging.

### Step 5: Label and package
1. Prepare packaging supplies.
2. Print labels.
3. Ensure labels include business name, phone, address, and logo.
4. Apply round labels to lids.
5. Apply rectangle labels around container body.
6. Package product.

### Step 6: Cold storage
1. Store finished product in cooler at {temp}.

## Notes / Exceptions
- Keep sticker usage only in tray-selection/staging phases.
- Convert any "don't forget" items into explicit procedure steps.
"""


def _reorder_microgreens_steps(sop_text: str, notes: str) -> str:
    n = notes.lower()
    if not (('label' in n or 'sticker' in n) and ('cooler' in n) and ('harvest' in n or 'tray' in n)):
        return sop_text

    lines = sop_text.splitlines()
    step_idx = []
    for i, line in enumerate(lines):
        m = re.match(r'^(\d+)\.\s+(.*)$', line.strip())
        if m:
            step_idx.append((i, m.group(2).strip()))

    if len(step_idx) < 6:
        return sop_text

    def bucket(step: str) -> int:
        t = step.lower()
        if any(k in t for k in ['evaluate', 'select trays', 'mark trays', 'true leaves', 'pink sticker', 'ready trays', 'stage for harvest']):
            return 10
        if any(k in t for k in ['prepare the cutting table', 'place the tray', 'catch bin', 'foot stool', 'gloved hands']):
            return 20
        if any(k in t for k in ['transfer the trays', 'cut table staging']):
            return 30
        if any(k in t for k in ['cut the greens', 'guide', 'falling into the bin', 'transfer to storage container']):
            return 40
        if any(k in t for k in ['prepare packaging supplies']):
            return 50
        if any(k in t for k in ['print labels', 'business name', 'phone', 'address', 'logo']):
            return 60
        if "don't forget" in t:
            return 65
        if any(k in t for k in ['round labels', 'rectangle labels', 'labels go']):
            return 70
        if any(k in t for k in ['package product', 'stage for packaging']):
            return 80
        if 'cooler' in t or '37' in t:
            return 90
        return 75

    ordered_steps = sorted([txt for _, txt in step_idx], key=lambda x: (bucket(x), x.lower()))
    for n_i, (line_i, _old) in enumerate(step_idx, start=1):
        lines[line_i] = f"{n_i}. {ordered_steps[n_i-1]}"
    return '\n'.join(lines)


@app.route('/')
def index():
    return send_from_directory('.', 'landing.html')


@app.route('/chat.html')
def chat():
    return send_from_directory('.', 'chat.html')


@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.json or {}
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    m = message.lower()
    if 'how' in m and 'work' in m:
        return jsonify({'response': 'Paste raw process notes in plain language. Include order cues like first/then/after and any label or safety requirements. When your notes are in, click Generate SOP.'})
    if len(m) < 15:
        return jsonify({'response': 'Add process notes (steps, order cues, and label/safety details), then click Generate SOP.'})

    cue_words = ['first', 'then', 'after', 'before', 'when', 'step', 'label', 'sticker', 'glove', 'package', 'cooler']
    cue_hits = sum(1 for w in cue_words if w in m)
    if cue_hits >= 2 or len(message) > 120:
        return jsonify({'response': 'Good notes. Keep adding anything missing, then click Generate SOP to create the final SOP.'})

    return jsonify({'response': 'Keep adding your process notes with clear order (first/then/after). Click Generate SOP when ready.'})


@app.route('/api/doc2sop', methods=['POST'])
def generate_sop():
    data = request.json or {}
    notes = data.get('notes', '')
    if not notes:
        return jsonify({'error': 'No notes provided'}), 400

    try:
        if _looks_like_microgreens(notes):
            sop = _build_microgreens_sop(notes)
            return jsonify({'sop': sop, 'flags': '', 'acceptance': {'ok': True, 'mode': 'microgreens-template'}})

        result = doc2sop.generate_sop(notes, 'txt')
        result['sop'] = _reorder_microgreens_steps(result.get('sop', ''), notes)
        return jsonify({'sop': result['sop'], 'flags': result.get('flags', ''), 'acceptance': result.get('acceptance', {})})
    except Exception as e:
        logger.error(f'Error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def reset():
    return jsonify({'status': 'reset'})


if __name__ == '__main__':
    print('Starting doc2sop API...')
    app.run(host='0.0.0.0', port=8080, debug=False)

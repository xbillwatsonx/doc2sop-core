#!/usr/bin/env python3
"""
Dynamic SOP Chat API with doc2sop-core pipeline
Uses local pipeline instead of calling OpenRouter directly
"""

import os
import sys

# Add the doc2sop-core path
CORE_PATH = '/opt/doc2sop-core'
if CORE_PATH not in sys.path:
    sys.path.insert(0, CORE_PATH)

import json
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Import directly from local files (not as a package)
import server_wrapper
import prompts
import pipeline

# Setup logging
LOG_FILE = '/tmp/dynamic-sop-api.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.')
CORS(app)

# Initialize the doc2sop server wrapper
doc2sop = server_wrapper.Doc2SOPServer(use_llm=False)

@app.route('/')
def index():
    logger.info("Landing page requested")
    return send_from_directory('.', 'landing.html')

@app.route('/chat.html')
def chat():
    return send_from_directory('.', 'chat.html')

@app.route('/api/doc2sop', methods=['POST'])
def generate_sop():
    """Generate an SOP from process notes using the local pipeline"""
    data = request.json
    process_notes = data.get('notes', '')
    session_id = request.headers.get('X-Session-ID', 'default')
    
    logger.info(f"[{session_id}] Generating SOP from notes ({len(process_notes)} chars)")
    
    if not process_notes:
        return jsonify({'error': 'No notes provided'}), 400

    try:
        result = doc2sop.generate_sop(process_notes, source_format='txt')
        
        sop_content = result['sop']
        flags = result.get('flags', '')
        acceptance = result.get('acceptance', {})
        
        logger.info(f"[{session_id}] SOP generated via pipeline")
        
        return jsonify({
            'sop': sop_content,
            'flags': flags,
            'acceptance': acceptance,
        })
        
    except Exception as e:
        logger.error(f"[{session_id}] Pipeline error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Pipeline error: {str(e)}'}), 500

@app.route('/api/reset', methods=['POST'])
def reset():
    return jsonify({'status': 'reset'})

if __name__ == '__main__':
    print("Starting Dynamic SOP API server with doc2sop-core pipeline...")
    print(f"Python path: {sys.path}")
    print("Open http://207.246.117.224:8080 in your browser")
    app.run(host='0.0.0.0', port=8080, debug=False)
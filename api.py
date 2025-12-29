"""
Autonomous Agent API
Production HTTP wrapper for the core agent system.
"""

from flask import Flask, request, jsonify
import logging
from cli import run_agent, load_config, setup_logging

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "autonomous-agent"})

@app.route('/execute', methods=['POST'])
def execute_task():
    """Execute a task via API"""
    try:
        data = request.get_json()
        
        if not data or 'task' not in data:
            return jsonify({"error": "Task is required"}), 400
        
        task = data['task']
        config = load_config()
        
        logging.info(f"API request: {task}")
        result = run_agent(task, config)
        
        return jsonify({
            "status": "success",
            "task": task,
            "result": result['observation'],
            "steps_completed": result['step_count'],
            "plan_executed": result['plan']
        })
        
    except Exception as e:
        logging.error(f"API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Get agent status"""
    return jsonify({
        "service": "autonomous-agent",
        "version": "1.0.0",
        "capabilities": [
            "file_operations",
            "directory_exploration", 
            "plan_revision",
            "memory_persistence"
        ]
    })

if __name__ == '__main__':
    setup_logging()
    app.run(host='0.0.0.0', port=8080, debug=False)

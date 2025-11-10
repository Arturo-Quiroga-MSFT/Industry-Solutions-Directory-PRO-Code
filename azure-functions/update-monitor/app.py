"""
Flask wrapper for ISD Update Monitor to run in Container Apps.
Wraps the function_app.py logic in a simple HTTP server.
"""
from flask import Flask, jsonify
import logging
from function_app import ISDUpdateMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/api/update-check", methods=["GET", "POST"])
def update_check():
    """HTTP endpoint to trigger update check."""
    logger.info('HTTP trigger - ISD Update Check requested')
    
    try:
        monitor = ISDUpdateMonitor()
        result = monitor.run_check()
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Update check failed: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Container Apps."""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

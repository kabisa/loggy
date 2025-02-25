"""
Logger Service - A simple Flask application for logging and debugging.

This service provides HTTP endpoints to emit logs at various levels and
a periodic logging mechanism for system status monitoring.
"""


from flask import Flask
import logging
import sys
import os
import time
import threading
from settipy import settipy

app = Flask(__name__)

# Configure logging (keep this outside as it's general logging setup)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

log_levels = {
    "debug": logger.debug,
    "info": logger.info,
    "warning": logger.warning,
    "error": logger.error,
    "critical": logger.critical
}


# Define periodic_logger and routes outside, as they are part of the app's structure
def periodic_logger():
    while True:
        time.sleep(settipy["PERIODIC_LOG_INTERVAL"]) # Access directly using settipy["VAR_NAME"]
        log_function = log_levels.get(settipy["PERIODIC_LOG_LEVEL"].lower(), logger.info) # Access directly
        log_function(settipy["PERIODIC_LOG_MESSAGE"]) # Access directly


@app.route('/<level>/<message>/')
@app.route('/<level>/<message>/<int:count>')
def log_message_route(level, message, count=1):
    """
    Endpoint to emit logs via HTTP requests.
    
    Parameters:
        level (str): The log level to use (debug, info, warning, error, critical)
        message (str): The message to log
        count (int, optional): Number of times to emit the log. Defaults to 1.
        
    Returns:
        tuple: A response message and HTTP status code
        
    Example:
        GET /info/system-startup/ - Logs "system-startup" at INFO level once
        GET /error/database-connection-failed/5 - Logs error message 5 times
    """
    if level.lower() not in log_levels:
        return f"Invalid log level: {level}. Must be one of: {', '.join(log_levels.keys())}", 400
    log_function = log_levels[level.lower()]
    for _ in range(count):
        log_function(message)
    return f"Emitted {count} logs at level {level.upper()} with message: {message}"


@app.route('/crash/')
@app.route('/crash/<handle>')
def crash_route(handle=""):
    """
    Debug endpoint that triggers a division by zero error.
    
    Used for testing error handling and logging in production/staging environments.
    
    Parameters:
        handle (str, optional): If set to 'false', 'f', 'no', 'n', or 'fail', 
                               the exception will be propagated instead of caught.
                               Default is to catch the exception.
    
    Returns:
        tuple: A response message and HTTP status code
        
    Raises:
        ZeroDivisionError: When handle parameter indicates the error should not be caught
    """
    try:
        result = 1 / 0
    except ZeroDivisionError:
        logger.critical("Application crash initiated due to division by zero!")
        if handle.lower() in {"false", "f", "no", "n", "fail"}:
            raise
        return "Crash endpoint triggered! Check server logs for division by zero error.", 500
    return "This should not be returned as crash is intended", 200


@app.route('/')
def default_route():
    """
    Default route that serves as the application's homepage.
    
    Returns information about the available endpoints and their usage.
    
    Returns:
        str: HTML content describing the API endpoints
    """
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Logger Service</title>
    <style>
        :root {
            --primary: #4f46e5;
            --primary-hover: #4338ca;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --critical: #b91c1c;
            --debug: #6b7280;
            --info: #3b82f6;
            --bg-color: #f9fafb;
            --card-bg: #ffffff;
            --text-color: #1f2937;
            --border-color: #e5e7eb;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
        }

        header {
            background-color: var(--primary);
            color: white;
            padding: 1.5rem 2rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        header h1 {
            font-size: 1.75rem;
        }

        .container {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
            padding: 1.5rem;
            max-width: 1200px;
            margin: 0 auto;
        }

        @media (min-width: 768px) {
            .container {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        .card {
            background-color: var(--card-bg);
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            padding: 1.5rem;
        }

        .card h2 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: var(--primary);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
        }

        .form-group {
            margin-bottom: 1rem;
        }

        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }

        select, input, button {
            width: 100%;
            padding: 0.75rem;
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            font-size: 1rem;
        }

        select:focus, input:focus {
            outline: 2px solid var(--primary-hover);
            border-color: var(--primary);
        }

        button {
            background-color: var(--primary);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            transition: background-color 0.2s;
        }

        button:hover {
            background-color: var(--primary-hover);
        }

        button.danger {
            background-color: var(--error);
        }

        button.danger:hover {
            background-color: #dc2626;
        }

        .result {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 0.375rem;
            border: 1px solid var(--border-color);
            background-color: #f8fafc;
            display: none;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            color: white;
        }

        .badge.debug {
            background-color: var(--debug);
        }

        .badge.info {
            background-color: var(--info);
        }

        .badge.warning {
            background-color: var(--warning);
        }

        .badge.error {
            background-color: var(--error);
        }

        .badge.critical {
            background-color: var(--critical);
        }

        .full-width {
            grid-column: 1 / -1;
        }

        pre {
            background-color: #f1f5f9;
            padding: 1rem;
            border-radius: 0.375rem;
            overflow-x: auto;
            font-family: 'Courier New', Courier, monospace;
            margin: 1rem 0;
        }

        .activity-log {
            margin-top: 1rem;
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 0.375rem;
            background-color: #f8fafc;
        }

        .activity-entry {
            padding: 0.5rem 1rem;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.875rem;
        }

        .activity-entry:last-child {
            border-bottom: none;
        }

        .docs-badges {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin: 1rem 0;
        }

        footer {
            text-align: center;
            padding: 2rem;
            background-color: #f1f5f9;
            margin-top: 2rem;
            border-top: 1px solid var(--border-color);
        }
    </style>
</head>
<body>
    <header>
        <h1>Logger Service</h1>
    </header>

    <div class="container">
        <div class="card">
            <h2>Generate Logs</h2>
            <form id="logForm">
                <div class="form-group">
                    <label for="level">Log Level:</label>
                    <select id="level" name="level">
                        <option value="debug">Debug</option>
                        <option value="info" selected>Info</option>
                        <option value="warning">Warning</option>
                        <option value="error">Error</option>
                        <option value="critical">Critical</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="message">Log Message:</label>
                    <input type="text" id="message" name="message" value="Test log message" required>
                </div>

                <div class="form-group">
                    <label for="count">Count:</label>
                    <input type="number" id="count" name="count" value="1" min="1" max="100">
                </div>

                <button type="submit">Emit Log(s)</button>
            </form>
            <div id="logResult" class="result"></div>
        </div>

        <div class="card">
            <h2>System Operations</h2>
            <p>Trigger a controlled crash to test error handling and logging in the system.</p>
            
            <div class="form-group">
                <label for="handle">Error Handling:</label>
                <select id="handle" name="handle">
                    <option value="">Catch Error (Default)</option>
                    <option value="fail">Propagate Error</option>
                </select>
            </div>
            
            <button type="button" id="crashButton" class="danger">Trigger Crash</button>
            <div id="crashResult" class="result"></div>
        </div>

        <div class="card full-width">
            <h2>Activity Log</h2>
            <p>Record of actions taken during this session:</p>
            <div class="activity-log" id="activityLog">
                <div class="activity-entry">Session started</div>
            </div>
        </div>

        <div class="card full-width">
            <h2>API Documentation</h2>
            
            <h3>HTTP Endpoints</h3>
            <pre>GET /{level}/{message}/             - Emit a log with specified level and message
GET /{level}/{message}/{count}      - Emit multiple logs with specified parameters
GET /crash/                         - Trigger a controlled crash (caught by default)
GET /crash/{handle}                 - Trigger crash with handle option (use 'fail' to propagate)</pre>
            
            <h3>Valid Log Levels</h3>
            <div class="docs-badges">
                <span class="badge debug">debug</span>
                <span class="badge info">info</span>
                <span class="badge warning">warning</span>
                <span class="badge error">error</span>
                <span class="badge critical">critical</span>
            </div>
            
            <h3>Configuration Parameters</h3>
            <pre>--PERIODIC_LOG_LEVEL     Severity level for periodic logs (default: INFO)
--PERIODIC_LOG_MESSAGE   Message for periodic logs (default: System heartbeat)
--PERIODIC_LOG_INTERVAL  Interval in seconds between periodic logs (default: 10)
--HOST                   Host for the Flask webserver (default: 0.0.0.0)
--PORT                   Port for the Flask webserver (default: 5000)
--DEBUG                  Enable/Disable Flask debug mode (default: True)</pre>
        </div>
    </div>

    <footer>
        <p>Logger Service &copy; 2025</p>
    </footer>

    <script>
        // Track user actions
        function logActivity(message) {
            const activityLog = document.getElementById('activityLog');
            const entry = document.createElement('div');
            entry.className = 'activity-entry';
            entry.textContent = message;
            activityLog.appendChild(entry);
            activityLog.scrollTop = activityLog.scrollHeight;
        }

        // Form submission for emitting logs
        document.getElementById('logForm').addEventListener('submit', function(event) {
            event.preventDefault();
            
            const level = document.getElementById('level').value;
            const message = document.getElementById('message').value;
            const count = document.getElementById('count').value;
            
            let url = `/${level}/${encodeURIComponent(message)}/`;
            if (count > 1) {
                url += count;
            }
            
            logActivity(`Requesting: ${url}`);
            
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.text();
                })
                .then(data => {
                    const resultElement = document.getElementById('logResult');
                    resultElement.textContent = data;
                    resultElement.style.display = 'block';
                    
                    logActivity(`Success: ${data}`);
                })
                .catch(error => {
                    const resultElement = document.getElementById('logResult');
                    resultElement.textContent = `Error: ${error.message}`;
                    resultElement.style.display = 'block';
                    
                    logActivity(`Error: ${error.message}`);
                });
        });
        
        // Crash button functionality
        document.getElementById('crashButton').addEventListener('click', function() {
            const handle = document.getElementById('handle').value;
            let url = '/crash/';
            if (handle) {
                url += handle;
            }
            
            logActivity(`Requesting crash: ${url}`);
            
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.text();
                })
                .then(data => {
                    const resultElement = document.getElementById('crashResult');
                    resultElement.textContent = data;
                    resultElement.style.display = 'block';
                    
                    logActivity(`Crash initiated: ${data}`);
                })
                .catch(error => {
                    const resultElement = document.getElementById('crashResult');
                    resultElement.textContent = `Error: ${error.message}`;
                    resultElement.style.display = 'block';
                    
                    if (handle === 'fail') {
                        resultElement.textContent += ' (Error propagated as requested)';
                        logActivity(`Crash with propagated error: ${error.message}`);
                    } else {
                        logActivity(`Error during crash request: ${error.message}`);
                    }
                });
        });
    </script>
</body>
</html>
    """#.format(settipy["PERIODIC_LOG_INTERVAL"], settipy["PERIODIC_LOG_LEVEL"], settipy["PERIODIC_LOG_MESSAGE"])



if __name__ == '__main__':
    # --- Settipy Configuration (Corrected and Super Simple) ---
    settipy.set("PERIODIC_LOG_LEVEL", "INFO", "Severity level for periodic logs (INFO, WARNING, ERROR, etc.)")
    settipy.set("PERIODIC_LOG_MESSAGE", "System heartbeat", "Message for periodic logs")
    settipy.set_int("PERIODIC_LOG_INTERVAL", 10, "Interval in seconds between periodic logs")
    settipy.set("HOST", "0.0.0.0", "Host for the Flask webserver")
    settipy.set_int("PORT", 5000, "Port for the Flask webserver")
    settipy.set_bool("DEBUG", False, "Enable/Disable Flask debug mode")

    settipy.parse() # Parse command-line and env vars

    startup_vars = {
        "script_name": os.path.basename(__file__),
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "periodic_log_level": settipy["PERIODIC_LOG_LEVEL"],
        "periodic_log_message": settipy["PERIODIC_LOG_MESSAGE"],
        "periodic_log_interval": settipy["PERIODIC_LOG_INTERVAL"],
        "flask_host": settipy["HOST"],
        "flask_port": settipy["PORT"],
        "flask_debug": settipy["DEBUG"]
    }
    logger.info(f"Project started with these vars: {startup_vars}")

    # Start the periodic logger in a background thread
    periodic_log_thread = threading.Thread(target=periodic_logger, daemon=True)
    periodic_log_thread.start()

    app.run(debug=settipy["DEBUG"], host=settipy["HOST"], port=settipy["PORT"]) # Use settipy-configured values for app.run

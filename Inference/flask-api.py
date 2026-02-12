from flask import Flask, request, jsonify
import requests
import os
import subprocess

app = Flask(__name__)

# Public sentiment analysis endpoint (legitimate)
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    # Forward to Ray cluster
    try:
        response = requests.post(
            'http://raycluster-sample-head-svc.default.svc.cluster.local:8000/analyze',
            json=data,
            timeout=5
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# VULNERABILITY 1: SSRF - can reach internal services (POST only)
@app.route('/proxy', methods=['POST'])
def proxy_request():
    target_url = request.json.get('url')
    payload = request.json.get('data', {})
    
    # NO VALIDATION - accepts any URL!
    try:
        response = requests.post(
            target_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return jsonify({
            'status': response.status_code,
            'data': response.json() if 'application/json' in response.headers.get('content-type', '') else response.text
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# VULNERABILITY 1b: SSRF with GET support
@app.route('/proxy-get', methods=['POST'])
def proxy_get_request():
    target_url = request.json.get('url')
    
    # VULNERABLE: GET request passthrough
    try:
        response = requests.get(
            target_url,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return jsonify({
            'status': response.status_code,
            'data': response.json() if 'application/json' in response.headers.get('content-type', '') else response.text
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# VULNERABILITY 2: Information disclosure
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'internal_services': {
            'ray_head': 'http://raycluster-sample-head-svc.default.svc.cluster.local:8000',
            'ray_dashboard': 'http://raycluster-sample-head-svc.default.svc.cluster.local:8265',
            'ray_gcs': 'raycluster-sample-head-svc.default.svc.cluster.local:6379'
        },
        'environment': dict(os.environ)
    })

# VULNERABILITY 3: RCE via eval
@app.route('/debug/eval', methods=['POST'])
def debug_eval():
    code = request.json.get('code', '')
    try:
        result = eval(code)  # CRITICAL: Remote Code Execution
        return jsonify({'result': str(result)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# VULNERABILITY 4: Command injection
@app.route('/debug/ping', methods=['POST'])
def debug_ping():
    host = request.json.get('host', 'localhost')
    # NO SANITIZATION
    result = subprocess.run(f'ping -c 1 {host}', shell=True, capture_output=True, text=True)
    return jsonify({
        'stdout': result.stdout,
        'stderr': result.stderr,
        'returncode': result.returncode
    })

# VULNERABILITY 5: Admin panel without auth
@app.route('/admin', methods=['GET'])
def admin_panel():
    return jsonify({
        'message': 'Admin panel',
        'actions': {
            'restart_service': '/admin/restart',
            'view_logs': '/admin/logs',
            'execute_command': '/admin/exec'
        }
    })

@app.route('/admin/exec', methods=['POST'])
def admin_exec():
    cmd = request.json.get('command', '')
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return jsonify({
        'output': result.stdout,
        'error': result.stderr
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

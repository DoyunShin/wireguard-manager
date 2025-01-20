import settings
import wg

from flask import Flask, request, redirect, session, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from pathlib import Path
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import google.auth.transport.requests
import base64
import time

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.secret_key = settings.SECRET_KEY

def check_logged_in() -> bool:
    return 'email' in session

def get_flow():
    return Flow.from_client_config(
        settings.GOOGLE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile", "openid"],
        redirect_uri=settings.CALLBACK_URL,
    )

@app.before_request
def before_request():
    if 'email' in session:
        if 'act_time' in session and session['act_time'] < time.time() - settings.LOGIN_TIME:
            session.pop('email')
            session.pop('idinfo')
            session.pop('login_time')
            session.pop('act_time')
        else:
            session['act_time'] = time.time()

@app.get("/")
def root():
    return "It Works!"

@app.route('/auth/google', methods=['GET'])
def google_auth():
    flow = get_flow()
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    session['login_start_time'] = time.time()

    return redirect(authorization_url)

@app.route('/auth/callback', methods=['GET'])
def google_auth_callback():
    state = session.pop('state', None)
    if state is None:
        return jsonify({"status": 400, "message": "State not found"}), 400
    
    login_start_time = session.pop('login_start_time', None)
    if login_start_time is None:
        return jsonify({"status": 400, "message": "Login start time not found"}), 400
    elif login_start_time < time.time() - settings.FLOW_TIME:
        return jsonify({"status": 400, "message": "Login flow time expired"}), 400
    
    if state != request.args.get('state'):
        return jsonify({"status": 400, "message": "State mismatch"}), 400
    
    try:
        flow = get_flow()
        flow.fetch_token(authorization_response=request.url)
        idinfo = id_token.verify_oauth2_token(flow.credentials.id_token, google.auth.transport.requests.Request(), flow.client_config['client_id'])
        email = idinfo.get('email')
    except Exception as e:
        return jsonify({"status": 400, "message": str(e)}), 400

    if email in settings.ALLOWED_EMAILS or email.split('@')[-1] in settings.ALLOWED_DOMAINS:
        session['email'] = email
        session['idinfo'] = idinfo
        session['login_time'] = time.time()
        session['act_time'] = time.time()
        return redirect('/manage')
    else:
        return jsonify({"status": 403, "message": "Forbidden"}), 403
        

@app.route('/wg/get_list', methods=['GET'])
def wg_get_list():
    """
    Get list of WireGuard peers

    Requires: Logged in

    Returns:
        dict: List of WireGuard peers
    
    """
    if not check_logged_in():
        return jsonify({"status": 403, "message": "Forbidden"}), 403

    user = session['email']

    return jsonify(wg.get_wireguard_list(user))
    
@app.route('/wg/get_config', methods=['GET'])
def wg_get_config():
    """
    Get WireGuard configuration

    Requires: Logged in

    Args:
        address (str): Peer address

    Returns:
        dict: WireGuard configuration
    
    """
    if not check_logged_in():
        return jsonify({"status": 403, "message": "Forbidden"}), 403

    user = session['email']
    address = request.args.get('address')

    return wg.generate_wireguard_config(user, address)

@app.route('/wg/add', methods=['POST'])
def wg_add():
    """
    Add WireGuard peer

    Requires: Logged in

    Returns:
        None (client need to reload the page)
    
    """
    if not check_logged_in():
        return jsonify({"status": 403, "message": "Forbidden"}), 403

    user = session['email']

    wgpair = wg.generate_wireguard_pair(user)
    if wg.add_client(wgpair):
        return jsonify({"status": 200, "message": "OK"})
    else:
        return jsonify({"status": 500, "message": "Internal Server Error. Server might have conflicted ip with generated ip"}), 500

@app.route('/wg/remove', methods=['POST'])
def wg_remove():
    """
    Remove WireGuard peer

    Requires: Logged in

    Args:
        address (str): Peer address

    Returns:
        None (client need to reload the page)
    
    """
    if not check_logged_in():
        return jsonify({"status": 403, "message": "Forbidden"}), 403

    user = session['email']
    address = request.args.get('address')

    if wg.remove_client(user, address):
        return jsonify({"status": 200, "message": "OK"})
    else:
        return jsonify({"status": 404, "message": "Associated Addess Not Found"}), 404

if __name__ == "__main__":
    settings.load_config()
    wg.load_config()

    app.run(host="0.0.0.0", port=5000, debug=settings.DEBUG, threaded=True)

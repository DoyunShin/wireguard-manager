import settings
import wg

from flask import Flask, request, redirect, session, jsonify, send_file
from werkzeug.middleware.proxy_fix import ProxyFix

from pathlib import Path
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import google.auth.transport.requests
from io import BytesIO
import argparse
import time
import json

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.secret_key = settings.SECRET_KEY

def _logged_in() -> bool:
    return 'email' in session

def _add_status(data: dict, status: int, message: str) -> dict:
    data['status'] = status
    data['message'] = message
    return data

def get_flow():
    return Flow.from_client_config(
        settings.GOOGLE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile", "openid"],
        redirect_uri=f"{settings.BASE_URL}/auth/callback",
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
    login_redirect = request.args.get('redirect', '/')
    session['redirect'] = "/" if "http://" in login_redirect or "https://" in login_redirect else login_redirect

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
        return redirect(session.pop('redirect', '/'))
    else:
        return jsonify({"status": 403, "message": "Forbidden"}), 403

@app.route('/profile', methods=['GET'])
def profile():
    """
    Get profile information

    Requires: Logged in

    Returns:
        dict: Profile information
    """
    
    if not _logged_in():
        return jsonify({"status": 403, "message": "Forbidden"}), 403
    
    data = {
        "email": session['email'],
    }

    return jsonify(_add_status(data, 200, "OK"))

@app.route('/wg/list', methods=['GET'])
def wg_list():
    """
    Get list of WireGuard peers

    Requires: Logged in

    Returns:
        dict: List of WireGuard peers
    
    """
    if not _logged_in():
        return jsonify({"status": 403, "message": "Forbidden"}), 403

    user = session['email']

    return jsonify(_add_status({"data": wg.get_wireguard_list(user)}, 200, "OK"))
    
@app.route('/wg/download', methods=['GET'])
def wg_config():
    """
    Get WireGuard configuration

    Requires: Logged in

    Args:
        address (str): Peer address

    Returns:
        dict: WireGuard configuration
    
    """
    if not _logged_in():
        return jsonify({"status": 403, "message": "Forbidden"}), 403

    user = session['email']
    ipid = request.args.get('id')

    wgconfig = wg.generate_wireguard_config(user, ipid)

    if not wgconfig:
        return jsonify({"status": 404, "message": "Associated ID Not Found"}), 404

    config_file = BytesIO(wgconfig.encode('utf-8'))
    config_file.seek(0)
    return send_file(config_file, as_attachment=True, attachment_filename=f"{wg.get_wireguard_name(user, ipid)}.conf", mimetype='text/plain')

@app.route('/wg/add', methods=['POST'])
def wg_add():
    """
    Add WireGuard peer

    Requires: Logged in

    Returns:
        None (client need to reload the page)
    
    """
    if not _logged_in():
        return jsonify({"status": 403, "message": "Forbidden"}), 403

    user = session['email']
    name = request.json.get('name', None)

    wgpair = wg.generate_wireguard_pair(user, name)
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
    if not _logged_in():
        return jsonify({"status": 403, "message": "Forbidden"}), 403

    user = session['email']
    ipid = request.json.get('id')

    if not ipid:
        return jsonify({"status": 400, "message": "ID is required"}), 400
    elif wg.remove_client(user, ipid):
        return jsonify({"status": 200, "message": "OK"})
    else:
        return jsonify({"status": 404, "message": "Associated Addess Not Found"}), 404

@app.route('/wg/edit', methods=['POST'])
def wg_edit():
    """
    Edit WireGuard peer

    Requires: Logged in

    Args:
        address (str): Peer address
        name (str): Peer name

    Returns:
        None (client need to reload the page)
    
    """
    if not _logged_in():
        return jsonify({"status": 403, "message": "Forbidden"}), 403

    user = session['email']
    ipid = request.json.get('id')
    name = request.json.get('name', None)

    if not ipid:
        return jsonify({"status": 400, "message": "ID is required"}), 400
    elif wg.fix_wireguard_pair(user, ipid, name):
        return jsonify({"status": 200, "message": "OK"})
    else:
        return jsonify({"status": 404, "message": "Associated Addess Not Found"}), 404

@app.route('/test', methods=['GET'])
def test():
    wg.load_config()
    wg.reload()
    return jsonify({"status": 200, "message": "OK"})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WireGuard Manager")
    parser.add_argument('-s', '--server', action='store_true', help="Start the WireGuard Manager server")
    parser.add_argument('-c', '--config', action='store_true', help="Open Config Manager")

    args = parser.parse_args()

    if args.server:
        settings.load_config()
        wg.load_config()
        wg.start()

        app.run(host="0.0.0.0", port=5000, debug=settings.DEBUG, threaded=True)
    elif args.config:
        user = None
        confdir = Path(input("RootConfigPath: "))
        confpath = confdir / "config.json"
        wgconfpath = confdir / "wg.json"
        if not confdir.exists():
            raise FileNotFoundError("Config file not found.\n> data/")
        if not confpath.exists():
            raise FileNotFoundError("Config file not found.\n> data/config.json")
        if not wgconfpath.exists():
            raise FileNotFoundError("Config file not found.\n> data/wg.json")
        
        settings.load_config()
        wg.load_config()

        while True:
            print(f"Now User: {user}")
            print("1. List User")
            print("2. Set User")
            if user:
                print("3. List WireGuard")
                print("4. Add WireGuard")
                print("5. Remove WireGuard")
                print("6. Edit WireGuard")
                print("7. Show WireGuard Config")
            print("8. Exit")
            choice = input("> ")

            matched = False

            match choice:
                case "1":
                    users = wg.list_users()
                    print("\n".join(users))
                case "2":
                    user = input("Enter user email: ")
                case "8":
                    exit(0)

            if user:
                match choice:
                    case "3":
                        print(json.dumps(wg.get_wireguard_list(user), indent=4))
                    case "4":
                        name = input("Enter peer name: ")
                        wgpair = wg.generate_wireguard_pair(user, name)
                        if wg.add_client(wgpair):
                            print("Peer added successfully")
                        else:
                            print("Failed to add peer")
                    case "5":
                            ipid = input("Enter peer ID: ")
                            if wg.remove_client(user, ipid):
                                print("Peer removed successfully")
                            else:
                                print("Failed to remove peer")
                    case "6":
                        ipid = input("Enter peer ID: ")
                        name = input("Enter new peer name: ")
                        if wg.fix_wireguard_pair(user, ipid, name):
                            print("Peer edited successfully")
                        else:
                            print("Failed to edit peer")
                    case "7":
                        ipid = input("Enter ID: ")
                        print(wg.generate_wireguard_config(user, ipid))
                    case _:
                        print("Invalid choice")
            else:
                print("Invalid choice")

import os
import flask
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import time
import threading

from script import script
from utils.api_utils import credentials_to_dict

app = flask.Flask(__name__)
app.secret_key = 'eaf44ba87ca2b7dc6f0e0d34eb392f7fb819fb2e9ec200399873245ce4089ea2'

CLIENT_SECRETS_FILE = "auth/client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/gmail.readonly']
SCRIPT_PERIOD = 15 * 60  # every 15 minutes


@app.route('/')
def index():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')
    credentials = Credentials(**flask.session['credentials'])

    @flask.copy_current_request_context
    def run_script(creds):
        while True:
            start_time = time.time()
            print('Script started')
            log = script(creds)
            flask.session['credentials'] = credentials_to_dict(creds)
            print(log)
            end_time = time.time()
            elapsed_time = end_time - start_time
            sleep_time = SCRIPT_PERIOD - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)

    script_thread = threading.Thread(target=run_script, args=(credentials,))
    script_thread.start()

    return 'Script started.'


@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    flask.session['state'] = state
    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    state = flask.session['state']
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect(flask.url_for('index'))


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run('localhost', 8080, debug=True)

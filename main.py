import os
import flask
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import time
import threading
from flask_sse import ServerSentEventsBlueprint

from script import script
from utils.api_utils import credentials_to_dict

app = flask.Flask(__name__)
sse = ServerSentEventsBlueprint('sse', app.name)
app.register_blueprint(sse)
app.secret_key = 'eaf44ba87ca2b7dc6f0e0d34eb392f7fb819fb2e9ec200399873245ce4089ea2'
app.template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))

CLIENT_SECRETS_FILE = "auth/client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/gmail.readonly']


@app.route('/')
def index():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')
    credentials = Credentials(**flask.session['credentials'])

    def run_script():
        while True:
            log = script(credentials)
            flask.session['credentials'] = credentials_to_dict(credentials)
            event = {'data': log, 'type': 'log'}
            flask.session.modified = True
            sse.publish(event, type='log')
            time.sleep(30)

    script_tread = threading.Thread(target=run_script)
    script_tread.start()

    return flask.render_template('index.html')


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

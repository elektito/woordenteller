from woordenteller import get_words
from flask import (
    Flask, request, render_template, redirect, session, url_for, jsonify
)
from flask_login import (
    LoginManager, login_required, login_user, logout_user, current_user
)
from werkzeug.middleware.proxy_fix import ProxyFix
from redis import Redis
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
import os


GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = (
    'https://accounts.google.com/.well-known/openid-configuration'
)
if not GOOGLE_CLIENT_ID:
    raise RuntimeError('GOOGLE_CLIENT_ID environment variable not set.')
if not GOOGLE_CLIENT_SECRET:
    raise RuntimeError('GOOGLE_CLIENT_SECRET environment variable not set.')

app = Flask(__name__)

# Add middleware for running behind a reverse proxy with https
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

if os.environ.get('SECRET_KEY'):
    app.config.update(SECRET_KEY=os.environ['SECRET_KEY'])
else:
    raise RuntimeError('Environment variable SECRET_KEY not set.')

app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')

redis_host = os.environ.get('REDIS_HOST', 'redis')
redis = Redis(host=redis_host, decode_responses=True)

client = WebApplicationClient(GOOGLE_CLIENT_ID)

login_manager = LoginManager()
login_manager.init_app(app)


class User:
    def __init__(self, id, name, email, picture):
        self.id = id
        self.name = name
        self.email = email
        self.picture = picture

        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False


    def get_id(self):
        return self.id


    @staticmethod
    def get(id):
        user_data = redis.get(f'user:{id}')
        if user_data == None:
            return None
        else:
            user_data = json.loads(user_data)
            user = User(user_data['id'],
                        user_data['name'],
                        user_data['email'],
                        user_data['picture'])
            return user


    @staticmethod
    def create(id, name, email, picture):
        user_data = {
            'id': id,
            'name': name,
            'email': email,
            'picture': picture,
        }
        redis.set(f'user:{id}', json.dumps(user_data))


def get_debug_user():
    return User('DEBUG_USER', 'DEBUG USER', 'debuguser@example.com', '')


@login_manager.user_loader
def load_user(user_id):
    if os.environ.get('DEBUG_USER'):
        return get_debug_user()
    return User.get(user_id)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route('/')
def index():
    words_key = f'words:{current_user.get_id()}'
    if 'params' in session:
        params = session['params']
        del session['params']
    else:
        params = {
            'nwords': redis.scard(words_key),
        }
    return render_template('home.html', **params)


@app.route('/login')
def login():
    if os.environ.get('DEBUG_USER'):
        login_user(get_debug_user())
        return redirect(url_for('index'))

    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg['authorization_endpoint']

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + '/callback',
        scope=['openid', 'email', 'profile'],
    )
    return redirect(request_uri)


@app.route('/login/callback')
def login_callback():
    # Get authorization code Google sent back to you
    code = request.args.get('code')

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL from
    # Google that gives you the user's profile information, including
    # their Google profile image and email
    userinfo_endpoint = google_provider_cfg['userinfo_endpoint']
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.  The user
    # authenticated with Google, authorized your app, and now you've
    # verified their email through Google!
    if userinfo_response.json().get('email_verified'):
        unique_id = userinfo_response.json()['sub']
        users_email = userinfo_response.json()['email']
        picture = userinfo_response.json()['picture']
        users_name = userinfo_response.json()['given_name']
    else:
        return 'User email not available or not verified by Google.', 400

    # Create a user in your db with the information provided by Google
    user = User(
        id=unique_id, name=users_name, email=users_email, picture=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/add', methods=['POST'])
@login_required
def add_words():
    input_text = request.form['input-text']
    kept, thrown = get_words(input_text)

    words_key = f'words:{current_user.get_id()}'
    current = redis.smembers(words_key)
    new = kept - current
    existing = kept & current

    for new_word in new:
        redis.sadd(words_key, new_word)

    params = {
        'new_words': list(new),
        'existing_words': list(existing),
        'thrown_words': list(thrown),
        'nwords': redis.scard(words_key),
    }

    session['params'] = params
    return redirect('/', code=303)


@app.route('/remove', methods=['POST'])
@login_required
def remove_word():
    word = request.args.get('word');
    words_key = f'words:{current_user.get_id()}'
    redis.srem(words_key, word)
    return jsonify({
        'description': f'"{word} removed from database.',
        'nwords': redis.scard(words_key),
    })


if __name__ == '__main__':
    # By declaring a non-empty environment variable named ADHOC_SSL
    # the user can ask for adhoc ssl to be enabled, so they can access
    # localhost over SSL. Could be useful for testing OAuth login
    # locally.
    if os.environ.get('ADHOC_SSL'):
        ssl_context = 'adhoc'
    else:
        # disable adhoc ssl
        ssl_context = None
    app.run(port=8000, ssl_context=ssl_context)

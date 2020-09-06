from woordteller import get_words
from flask import Flask, request, render_template, redirect, session
from redis import Redis
import os


app = Flask(__name__)

if os.environ.get('SECRET_KEY'):
    app.config.update(SECRET_KEY=os.environ['SECRET_KEY'])
else:
    raise RuntimeError('Environment variable SECRET_KEY not set.')

redis_host = os.environ.get('REDIS_HOST', 'redis')
redis = Redis(host=redis_host, decode_responses=True)

user = 'foouser'


@app.route('/')
def get_root():
    words_key = f'{user}:words'
    if 'params' in session:
        params = session['params']
        del session['params']
    else:
        params = {
            'nwords': redis.scard(words_key),
        }
    return render_template('home.html', **params)


@app.route('/add', methods=['POST'])
def post_add():
    input_text = request.form['input-text']
    kept, thrown = get_words(input_text)

    words_key = f'{user}:words'
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


if __name__ == '__main__':
    app.run(port=8000)

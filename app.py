from woordteller import get_words
from flask import Flask, request, render_template
from redis import Redis


app = Flask(__name__)
redis = Redis(host='redis', decode_responses=True)

user = 'foouser'


@app.route('/')
def get_root():
    words_key = f'{user}:words'
    params = {
        'nwords': redis.scard(words_key),
    }
    return render_template('home.html', **params)


@app.route('/', methods=['POST'])
def post_root():
    input_text = request.form['input-text']
    kept, thrown = get_words(input_text)

    words_key = f'{user}:words'
    current = redis.smembers(words_key)
    new = kept - current
    existing = kept & current

    for new_word in new:
        redis.sadd(words_key, new_word)

    params = {
        'new_words': new,
        'existing_words': existing,
        'thrown_words': thrown,
        'nwords': redis.scard(words_key),
    }
    return render_template('home.html', **params)


if __name__ == '__main__':
    app.run(port=8000)

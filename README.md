# Nederlandse Woordenteller

The _Nederlandse Woordenteller_ (Dutch Word Counter) is a tiny web
application to help you keep track of the words you've learned. Simply
enter words, phrases or sentences you know and it will keep track of
the new words. [Frog][1] is used to extract the word roots, so for
example "boeken" and "boek" are not counted as separate words.

## Running the app

The easiest way to run the app is using docker-compose. You need to
provide an appropriate `.env` file populated with the needed
information (Flask secret key, Google client ID, etc). An example
file, named `.env.example` is included.

After the `.env` file is ready, simply run:

    docker-compose up

To enable debug user, you can run:

    docker-compose -f docker-compose.yml -f docker-compose.debug.yml up

The app should be available at `http://localhost:8000`.

[1]: https://languagemachines.github.io/frog/

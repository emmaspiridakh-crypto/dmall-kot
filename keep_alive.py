from flask import Flask
from threading import Thread

app = Flask(__name__)

PORT = 1000


@app.route("/")
def home():
    return "Bot is alive."


def run():
    app.run(host="0.0.0.0", port=PORT)


def keep_alive():
    t = Thread(target=run)
    t.start()

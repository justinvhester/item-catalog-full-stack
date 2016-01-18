from application import app
app.config.from_pyfile('config.py')
app.run(host="0.0.0.0", port=8000)

from flask import Flask, render_template, request, jsonify

from create_stories import create_stories

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create", methods=["GET"])
def create():
    if request.method == "GET":
        site = request.args.get('option')
        create_stories(site)
        return jsonify({'result': 'success'})
    

if __name__ == "__main__":
    app.run(debug=True)
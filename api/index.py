import os

from flask import Flask, g, render_template
from flask_cors import CORS
from supabase import Client, create_client


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": os.environ.get("FRONTEND_URL", "*")}})

    app.config["SUPABASE_URL"] = os.environ["SUPABASE_URL"]
    app.config["SUPABASE_KEY"] = os.environ["SUPABASE_KEY"]
    app.config["BASE_URL"] = os.environ["BASE_URL"]

    app.config["SUPABASE_CLIENT"] = create_client(
        app.config["SUPABASE_URL"], app.config["SUPABASE_KEY"]
    )
    return app


app = create_app()


@app.before_request
def before_request():
    g.supabase = app.config["SUPABASE_CLIENT"]


@app.route("/")
def health_check():
    return "ok"


@app.route("/likes/<post>")
def likes(post: str):
    supabase: Client = g.supabase
    likes = get_likes(supabase, post)
    return render_template(
        "likes.html", num_likes=likes, post_name=post, base_url=app.config["BASE_URL"]
    )


@app.route("/like/<post>", methods=["POST"])
def like(post: str):
    supabase: Client = g.supabase
    supabase.rpc("increment_likes", {"post_name": post}).execute()

    likes = get_likes(supabase, post)
    return render_template("liked.html", num_likes=likes)


def get_likes(supabase: Client, post: str) -> int:
    response = supabase.table("content").select("likes").eq("name", post).execute()
    if not response.data:
        supabase.table("content").insert({"name": post, "likes": 0}).execute()
        return 0
    return response.data[0]["likes"]

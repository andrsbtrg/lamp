import os

from datetime import datetime
from flask import Flask, g, render_template, request
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


@app.route("/comments/<post>", methods=["GET"])
def get_comments(post: str):
    supabase: Client = g.supabase
    try:
        response = (
            supabase.table("comments")
            .select("id, author, content, created_at")
            .eq("post", post)
            .order("id", desc=False)
            .execute()
        )

        print(response)
    except Exception as e:
        return render_template("error.html", message="Error loading comments")

    return render_template("comments.html", comments=response.data)


@app.route("/comments/<post>", methods=["POST"])
def add_comment(post: str):
    supabase: Client = g.supabase
    author = request.form.get("author", "Anonymous").strip()
    content = request.form.get("content", "").strip()

    if not content:
        return render_template("error.html", message="Comment cannot be empty."), 400

    try:
        response = (
            supabase.table("comments")
            .insert({"post": post, "author": author, "content": content})
            .execute()
        )
        new_comment = response.data[0]
    except Exception as e:
        return render_template("error.html", message=str(e))

    return render_template("comment.html", comment=new_comment)


@app.template_filter("format_datetime")
def format_datetime(value):
    dt = datetime.fromisoformat(value)
    return dt.strftime("%b %d, %Y at %I:%M %p")

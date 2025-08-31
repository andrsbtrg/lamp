from flask import Flask, render_template
from flask_cors import CORS

import os
from supabase import create_client, Client

app = Flask(__name__)
# CORS(app)
CORS(app, resources={r"/*": {"origins": "https://andrsbtrg.vercel.app"}})

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
if not url or not key:
    raise Exception("Missing env variables")

supabase: Client = create_client(url, key)


@app.route("/health")
def health_check():
    return "ok"


@app.route("/likes/<post>")
def likes(post: str):
    response = (
        supabase.table("content").select("name", "likes").eq("name", post).execute()
    )
    if len(response.data) == 0:
        supabase.table("content").insert({"name": post, "likes": 0}).execute()
        likes = 0
    else:
        likes = response.data[0]["likes"]
    return render_template("likes.html", num_likes=likes, post_name=post)


@app.route("/like/<post>", methods=["POST"])
def like(post: str):
    response = (
        supabase.table("content").select("id", "likes").eq("name", post).execute()
    )
    row = response.data[0]
    print(row)
    likes = int(response.data[0]["likes"])
    likes += 1

    upd = (
        supabase.table("content").update({"likes": likes}).eq("id", row["id"]).execute()
    )
    print(upd)
    return render_template("liked.html", num_likes=likes)

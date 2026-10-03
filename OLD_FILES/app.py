from flask import Flask, render_template, request, jsonify

from adaptive_context.adaptive_context_engine import AdaptiveContextEngine
from scripts.llm import warmup

app = Flask(
    __name__,
    template_folder="UI/templates",
    static_folder="UI/static"
)

# Load the model into memory once, at server startup, so the panel never
# sees the slow "cold load" delay during the actual demo.
warmup()

engine = AdaptiveContextEngine()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat_api():

    data = request.get_json()

    persona = {

        "role": data.get("role", "Assistant"),

        "tone": data.get("tone", "Professional"),

        "goal": data.get("goal", "Help the user")

    }

    result = engine.process(

        persona,

        data.get("message", "")

    )

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
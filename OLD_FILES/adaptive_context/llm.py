import requests

MODEL = "qwen2.5:3b"


def generate(prompt, num_predict=300):

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "30m",   # keep the model loaded in RAM/VRAM between
                                    # requests so a pause in the demo doesn't
                                    # trigger a slow reload on the next message
            "options": {
                "temperature": 0.2,
                "num_predict": num_predict,  # hard cap on output length
                "num_ctx": 2048,             # don't process against the
                                              # model's full (often huge)
                                              # default context window
            }
        },
        timeout=120
    )

    return response.json()["response"]


def warmup():
    """
    Call this once when the server starts (before the panel sees anything)
    so the model is already loaded into memory and the first real message
    doesn't pay the cold-load cost during the demo.
    """
    try:
        generate("Say OK.", num_predict=5)
        print(">>> LLM warmup complete, model loaded and ready <<<")
    except Exception as e:
        print(">>> LLM warmup failed:", e)
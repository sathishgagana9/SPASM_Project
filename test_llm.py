from scripts.llm import generate

print("Testing Ollama...")

response = generate("Say hello in one sentence.")

print(response)
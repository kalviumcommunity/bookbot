import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key from backend/.env (same directory as this file)
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError(f"GEMINI_API_KEY is not set (looked in {env_path})")

# Configure Gemini client
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# --- Example for one-shot (teaching AI before query) ---
one_shot_example = """
You are a helpful assistant.

Example:
User: Convert 'Hello World' to Python print statement.
AI: print("Hello World")

Now answer the following query in the same way.
"""

def ai_chat():
    print("🤖 AI Chatbot (Zero-Shot + One-Shot Hybrid Mode) (type 'exit' to quit)\n")

    while True:
        query = input("You: ")
        if query.lower() == "exit":
            print("Goodbye 👋")
            break

        try:
            # Decide when to use one-shot:
            # e.g., if the user asks for "convert", "example", or "code"
            if any(word in query.lower() for word in ["convert", "example", "code", "format"]):
                prompt = one_shot_example + "\nUser: " + query + "\nAI:"
                print("🟢 Using One-Shot Prompting")
            else:
                prompt = query
                print("🔵 Using Zero-Shot Prompting")

            response = model.generate_content(prompt)
            print("AI:", response.text.strip(), "\n")

        except Exception as e:
            print("Error:", e, "\n")

if __name__ == "__main__":
    ai_chat()

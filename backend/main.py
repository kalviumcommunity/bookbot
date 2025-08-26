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

# --- Multi-shot examples (teaching AI with multiple Q&A before real query) ---
multi_shot_examples = """
You are a helpful assistant.

Examples:
User: What is the capital of France?
AI: Paris

User: What is 5 + 7?
AI: 12

User: Convert 'Hello' to Python print statement.
AI: print("Hello")

Now answer the following query in the same way.
"""

def ai_chat():
    print("🤖 AI Chatbot (Zero-Shot + One-Shot + Multi-Shot Mode) (type 'exit' to quit)\n")

    while True:
        query = input("You: ")
        if query.lower() == "exit":
            print("Goodbye 👋")
            break

        try:
            # Logic to decide which prompting style to use
            if any(word in query.lower() for word in ["convert", "example", "code", "format"]):
                prompt = multi_shot_examples + "\nUser: " + query + "\nAI:"
                print("🟣 Using Multi-Shot Prompting")
            else:
                prompt = query
                print("🔵 Using Zero-Shot Prompting")

            # Send request
            response = model.generate_content(prompt)
            print("AI:", response.text.strip(), "\n")

        except Exception as e:
            print("Error:", e, "\n")

if __name__ == "__main__":
    ai_chat()

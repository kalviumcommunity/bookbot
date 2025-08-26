import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key from backend/.env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError(f"GEMINI_API_KEY is not set (looked in {env_path})")

# Configure Gemini client
genai.configure(api_key=api_key)

# Create model with temperature parameter
# You can change temperature between 0.0 (deterministic) to 1.0 (creative)
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    generation_config={"temperature": 0.7}   # 👈 added temperature here
)

# One-shot example
one_shot_example = """
You are a helpful assistant.

Example:
User: What is the capital of Germany?
AI: Berlin

Now answer the following query in the same way.
"""

# Multi-shot examples
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
    print("🤖 AI Chatbot (Dynamic Prompting: Zero-Shot | One-Shot | Multi-Shot) (type 'exit' to quit)\n")

    while True:
        query = input("You: ")
        if query.lower() == "exit":
            print("Goodbye 👋")
            break

        try:
            # Decide prompting strategy
            if "capital" in query.lower():   # One-shot for factual Q&A
                prompt = one_shot_example + "\nUser: " + query + "\nAI:"
                print("🟢 Using One-Shot Prompting")

            elif any(word in query.lower() for word in ["convert", "example", "code", "format"]):
                prompt = multi_shot_examples + "\nUser: " + query + "\nAI:"
                print("🟣 Using Multi-Shot Prompting")

            else:
                prompt = query
                print("🔵 Using Zero-Shot Prompting")

            # Generate AI response
            response = model.generate_content(prompt)
            print("AI:", response.text.strip(), "\n")

        except Exception as e:
            print("Error:", e, "\n")

if __name__ == "__main__":
    ai_chat()

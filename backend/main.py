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

# ----------------- Structured Output Schema -----------------
BOOK_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "The title of the book"},
        "author": {"type": "string", "description": "The author of the book"},
        "summary": {"type": "string", "description": "Concise summary of the book"},
        "key_points": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Important key takeaways from the book"
        },
        "difficulty": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced"],
            "description": "Reading difficulty level"
        }
    },
    "required": ["title", "author", "summary", "key_points"]
}

structured_model = genai.GenerativeModel(
    "gemini-1.5-flash",
    generation_config={
        "temperature": 0.7,
        "response_mime_type": "application/json",
        "response_schema": BOOK_SCHEMA
    }
)

def ai_structured_summary(book_name: str, author_name: str):
    prompt = f"""
    You are BookBot. Summarize the book clearly.

    Book Title: {book_name}
    Author: {author_name}
    
    Return structured JSON with:
    - title
    - author
    - summary
    - key_points
    - difficulty
    """
    response = structured_model.generate_content(prompt)
    return response.text  # Already JSON

# ----------------- Function Calling Model -----------------
model = genai.GenerativeModel(
    "gemini-1.5-flash",
    generation_config={"temperature": 0.7},
    tools=[
        {
            "function_declarations": [
                {
                    "name": "get_weather",
                    "description": "Get the current weather for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "The name of the city"}
                        },
                        "required": ["city"]
                    }
                }
            ]
        }
    ]
)

# Example function the AI can call
def get_weather(city: str):
    """Mock weather function — replace with real API if you want"""
    fake_weather_data = {
        "Berlin": "Cloudy, 18°C",
        "Paris": "Sunny, 22°C",
        "New York": "Rainy, 25°C"
    }
    return fake_weather_data.get(city, f"Sorry, I don't have weather data for {city}.")

# ---- Prompt templates ----
one_shot_example = """
You are a helpful assistant.

Example:
User: What is the capital of Germany?
AI: Berlin

Now answer the following query in the same way.
"""

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

# Safe Chain-of-Thought (CoT) prompting
def build_cot_prompt(user_query: str) -> str:
    return f"""
You are a careful reasoning assistant.
Think through the problem step-by-step in your private scratchpad, but DO NOT reveal those internal steps.
Only return:
1) Final answer
2) A brief high-level rationale (2–4 short bullets, no detailed step-by-step math or hidden chain-of-thought).

Question: {user_query}

Return format:
Final: <final answer>
Why (brief):
- <bullet 1>
- <bullet 2>
- <bullet 3>
"""

def extract_function_call(response):
    """Safely find a function_call (if any) in the response."""
    try:
        for cand in response.candidates:
            for part in cand.content.parts:
                fc = getattr(part, "function_call", None)
                if fc:
                    return fc
    except Exception:
        pass
    return None

# ----------------- Main Chat Loop -----------------
def ai_chat():
    print("🤖 AI Chatbot (Dynamic Prompting + Function Calling + Safe CoT + Structured Output)  — type 'exit' to quit\n")
    print("Tips:")
    print(" • Type '/cot <your question>' to force Chain-of-Thought mode")
    print(" • Ask 'why/how/solve/explain' to auto-trigger CoT")
    print(" • Ask 'convert/code/format' to trigger multi-shot")
    print(" • Type '/book <book name> by <author>' to get a structured JSON summary\n")

    while True:
        query = input("You: ")
        if query.lower() == "exit":
            print("Goodbye 👋")
            break

        try:
            # -------- Structured Output Mode --------
            if query.strip().lower().startswith("/book "):
                try:
                    book_query = query[6:].strip()
                    if " by " in book_query:
                        book_name, author_name = book_query.split(" by ", 1)
                    else:
                        book_name, author_name = book_query, "Unknown"

                    result = ai_structured_summary(book_name, author_name)
                    print("\n📖 Structured Book Summary (JSON):\n", result, "\n")

                except Exception as e:
                    print("Error in structured summary:", e, "\n")
                continue

            # -------- CoT, One-shot, Multi-shot --------
            use_cot = False
            raw_query = query

            if query.strip().lower().startswith("/cot "):
                use_cot = True
                raw_query = query.strip()[5:]

            reasoning_triggers = ["why", "how", "explain", "prove", "derive", "solve", "estimate", "plan"]
            if any(w in raw_query.lower() for w in reasoning_triggers):
                use_cot = True

            if use_cot:
                prompt = build_cot_prompt(raw_query)
                print("🧠 Using Chain-of-Thought (safe) Prompting")
            elif "capital" in raw_query.lower():
                prompt = one_shot_example + "\nUser: " + raw_query + "\nAI:"
                print("🟢 Using One-Shot Prompting")
            elif any(word in raw_query.lower() for word in ["convert", "example", "code", "format"]):
                prompt = multi_shot_examples + "\nUser: " + raw_query + "\nAI:"
                print("🟣 Using Multi-Shot Prompting")
            else:
                prompt = raw_query
                print("🔵 Using Zero-Shot Prompting")

            # Generate response
            response = model.generate_content(prompt)

            # Function call handling
            fn_call = extract_function_call(response)
            if fn_call:
                fn_name = fn_call.name
                args = fn_call.args or {}
                if fn_name == "get_weather":
                    result = get_weather(args.get("city", ""))
                    print(f"🌦️ Weather result: {result}\n")
                else:
                    print(f"⚠️ Function {fn_name} not implemented.\n")
            else:
                print("AI:", response.text.strip(), "\n")

        except Exception as e:
            print("Error:", e, "\n")


if __name__ == "__main__":
    ai_chat()

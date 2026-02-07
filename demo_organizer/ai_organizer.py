import os
import openai

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_KEY

def ask_ai_to_sort(files):
    """
    Dă lista de fișiere PDF și primește un plan de organizare (JSON)
    """
    prompt = f"""
    You are LibraryAI. You can only reason about these PDF files:
    {files}

    Organize them into folders by topic. Respond ONLY in JSON with this format:
    {{
        "actions": [
            {{"action": "create_folder", "name": "..."}},
            {{"action": "move_file", "file": "...", "target": "..."}}
        ]
    }}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a LibraryAI assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    text = response['choices'][0]['message']['content']
    import json
    return json.loads(text)

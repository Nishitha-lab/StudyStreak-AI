import requests
import json
from groq import Groq, RateLimitError, AuthenticationError
# Note: base64, re, and html imports are removed.

# --- !!! PASTE YOUR GROQ API KEY HERE !!! ---
GROQ_API_KEY = "ADD_YOUR_GROQ_API_KEY_HERE" 
# ---

# Set up the Groq client
if not GROQ_API_KEY.startswith("gsk_"):
    print("WARNING: Groq API key is not set or is invalid in ai_helper.py.")
client = Groq(api_key=GROQ_API_KEY)

# --- Model Selection (All image models removed) ---
MODEL_ID_QA = "llama-3.1-8b-instant"
MODEL_ID_NOTES = "llama-3.3-70b-versatile"
MODEL_ID_QUIZ = "llama-3.3-70b-versatile" 
MODEL_ID_FEEDBACK = "llama-3.1-8b-instant" 
MODEL_ID_FLASHCARDS = "llama-3.1-8b-instant"
MODEL_ID_INTERVIEW = "llama-3.3-70b-versatile"
MODEL_ID_EVALUATION = "llama-3.3-70b-versatile"
MODEL_ID_VISUALIZER = "llama-3.3-70b-versatile"



def query_groq_api(system_prompt, user_prompt, model_id, max_tokens=1024):
    """
    Generic function to query the Groq Chat API for single-turn Q&A.
    """
    if GROQ_API_KEY == "PASTE_YOUR_GROQ_API_KEY_HERE" or not GROQ_API_KEY.startswith("gsk_"):
        return {"error": "Groq API Key is not set in ai_helper.py. Please get a free key."}
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7, 
            max_tokens=max_tokens
        )
        answer = response.choices[0].message.content
        return answer.strip()
    except AuthenticationError:
        return {"error": "Groq Authentication failed. Is your API key correct?"}
    except RateLimitError:
        return {"error": "Groq API rate limit exceeded. Please try again in a moment."}
    except Exception as e:
        return {"error": f"An unknown error occurred with the AI. ({e})"}


# --- *** ALL YOUR FUNCTIONS (RESTORED) *** ---

def get_ai_doubt_response(question):
    """ Calls the Groq API to answer a student's question. """
    system_prompt = "You are an expert study assistant and tutor. Answer the student's question clearly, concisely, and accurately. Behave like a helpful teacher."
    response = query_groq_api(system_prompt, question, MODEL_ID_QA, max_tokens=250)
    
    if isinstance(response, dict) and "error" in response:
        return response["error"]
    return response

def generate_ai_notes(topic_text):
    """ Calls the Groq API to summarize text into notes. """
    system_prompt = "You are a world-class note-taking assistant. Summarize the following text into key bullet points or a concise paragraph for a student's review. Focus on the main ideas and important definitions."
    response = query_groq_api(system_prompt, topic_text, MODEL_ID_NOTES, max_tokens=400)
    
    if isinstance(response, dict) and "error" in response:
        return response["error"]
    return response

def generate_ai_quiz(topic, num_questions=5, difficulty="Medium", is_late_night=False, is_distracted=False):
    """ 
    Calls the Groq API to generate a quiz as a JSON object,
    accounting for the user's focus state.
    """
    
    if is_late_night:
        system_prompt = f"""
You are an expert quiz creator. The user is studying late at night and is tired.
Your task is to generate a gentle, encouraging quiz.
**You MUST IGNORE the requested difficulty and ONLY generate 'Easy' questions.**
Focus on simple definitions and key concept recall to help them revise.
"""
    elif is_distracted:
        system_prompt = f"""
You are an expert quiz creator. The user has lost focus.
Your task is to re-engage them with a single, interesting "micro-task" question.
**You MUST IGNORE the requested number of questions and difficulty.**
Generate ONLY ONE (1) "Easy" or "Medium" question that is engaging or a simple problem.
"""
    else:
        system_prompt = f"""
You are an expert quiz creator for students. You will be given a topic, a number of questions, and a difficulty level.
Your task is to generate a multiple-choice quiz.
The difficulty of the questions MUST match the requested level: {difficulty}.
- Easy: Basic recall, definitions, simple concepts.
- Medium: Application of concepts, simple analysis.
- Hard: Complex analysis, synthesis of ideas, challenging problems.
"""
    
    if is_distracted:
        num_questions = 1
    
    system_prompt_full = f"""
{system_prompt}

You MUST return your response as a single, valid JSON object. Do NOT include any text before or after the JSON.
The JSON object must follow this exact structure:
{{
  "quiz": [
    {{
      "question": "The question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer_index": 0 
    }}
  ]
}}
"""
    
    user_prompt = f"Topic: {topic}\nNumber of Questions: {num_questions}\nDifficulty: {difficulty}"
    max_quiz_tokens = 200 * num_questions 
    
    response_string = query_groq_api(system_prompt_full, user_prompt, MODEL_ID_QUIZ, max_tokens=max_quiz_tokens)
    
    if isinstance(response_string, dict) and "error" in response_string:
        return response_string

    try:
        json_string = response_string.strip().lstrip("```json").lstrip("```").rstrip("```")
        json_start = json_string.find('{')
        if json_start == -1:
            raise json.JSONDecodeError("No JSON object found in AI response.", response_string, 0)
        json_end = json_string.rfind('}')
        if json_end == -1:
             raise json.JSONDecodeError("No closing brace for JSON found.", response_string, 0)

        json_string_cleaned = json_string[json_start:json_end+1]
        quiz_data = json.loads(json_string_cleaned)
        if "quiz" not in quiz_data or not isinstance(quiz_data["quiz"], list):
             raise ValueError("JSON response is missing 'quiz' list.")
        return quiz_data
        
    except Exception as e:
        print(f"Failed to decode AI's JSON response: {e}")
        print(f"AI returned: {response_string}")
        return {"error": "The AI failed to generate a valid quiz. Please try again."}

def get_ai_coach_feedback(quiz_history_text):
    """ Generates personalized coaching feedback based on quiz history. """
    system_prompt = """
You are an AI Study Coach. Analyze the student's quiz history.
Provide short, motivational, personalized feedback including:
- Strengths
- Weak areas
- Recent improvement
- Suggested next topics
- One short motivational message
Be friendly and supportive.
"""
    prompt = f"Here is the student's quiz history:\n\n{quiz_history_text}\n\nGive your analysis."
    response = query_groq_api(system_prompt, prompt, MODEL_ID_FEEDBACK, max_tokens=250)
    if isinstance(response, dict) and "error" in response:
        return f"AI Coach Error: {response['error']}"
    return response.strip()

def generate_ai_flashcards(topic, num_cards=10):
    """ Calls the Groq API to generate flashcards as a JSON object. """
    system_prompt = f"""
You are an expert flashcard creator. You will be given a topic and a number of cards.
Your task is to generate key-term/definition pairs or question/answer pairs suitable for flashcards.
The 'front' should be a term or a short question.
The 'back' should be the concise definition or answer.
You MUST return your response as a single, valid JSON object. Do NOT include any text before or after the JSON.
The JSON object must follow this exact structure:
{{
  "flashcards": [
    {{"front": "Term 1", "back": "Definition 1"}},
    {{"front": "Term 2", "back": "Definition 2"}}
  ]
}}
"""
    user_prompt = f"Topic: {topic}\nNumber of Flashcards: {num_cards}"
    max_flashcard_tokens = 75 * num_cards 
    response_string = query_groq_api(system_prompt, user_prompt, MODEL_ID_FLASHCARDS, max_tokens=max_flashcard_tokens)
    if isinstance(response_string, dict) and "error" in response_string:
        return response_string
    try:
        json_string = response_string.strip().lstrip("```json").lstrip("```").rstrip("```")
        json_start = json_string.find('{')
        if json_start == -1:
            raise json.JSONDecodeError("No JSON object found in AI response.", json_string, 0)
        json_end = json_string.rfind('}')
        if json_end == -1:
             raise json.JSONDecodeError("No closing brace for JSON found.", response_string, 0)
        json_string_cleaned = json_string[json_start:json_end+1]
        flashcard_data = json.loads(json_string_cleaned)
        if "flashcards" not in flashcard_data or not isinstance(flashcard_data["flashcards"], list):
             raise ValueError("JSON response is missing 'flashcards' list.")
        return flashcard_data
    except Exception as e:
        print(f"Failed to decode AI's JSON response for flashcards: {e}")
        print(f"AI returned: {response_string}")
        return {"error": "The AI failed to generate valid flashcards. Please try again."}

# --- *** INTERVIEW BOT FUNCTIONS *** ---

def query_groq_api_chat(messages_list, model_id, max_tokens=1024):
    """
    Generic function to query the Groq Chat API with a full message history.
    """
    if GROQ_API_KEY == "PASTE_YOUR_GROQ_API_KEY_HERE" or not GROQ_API_KEY.startswith("gsk_"):
        return {"error": "Groq API Key is not set in ai_helper.py. Please get a free key."}

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=messages_list, # Pass the entire chat history
            temperature=0.7, 
            max_tokens=max_tokens
        )
        answer = response.choices[0].message.content
        return answer.strip()
    except AuthenticationError:
        return {"error": "Groq Authentication failed. Is your API key correct?"}
    except RateLimitError:
        return {"error": "Groq API rate limit exceeded. Please try again in a moment."}
    except Exception as e:
        return {"error": f"An unknown error occurred with the AI. ({e})"}

def get_interview_response(chat_history):
    """
    Acts as the AI Interviewer.
    Takes the full chat history and returns the next question/comment.
    """
    system_prompt = """
You are an expert, stern, and professional interview panelist. 
Your name is "Dr. Sharma." You are conducting a high-pressure mock interview.
- NEVER break character. Do not be overly friendly.
- Ask a mix of subject-based, current affairs, hypothetical, and pressure-test questions.
- Analyze the user's last answer. If it's weak, challenge it with a follow-up.
- If it's strong, pivot to a new topic.
- Keep your questions concise.
- **FOR UPSC:** Start the interview by introducing yourself and asking the user to begin.
- **FOR 'Other' streams:** If the user's first message is "Start the interview.", you MUST ask them what interview they are preparing for (e.g., "Google SWE", "Medical School").
- **Once they specify the topic (e.g., "Google SWE"),** you must acknowledge it and begin the interview *for that specific topic*. (e.g., "Very well. We will begin the Google SWE interview now...").
"""
    messages_list = [{"role": "system", "content": system_prompt}] + chat_history
    response = query_groq_api_chat(messages_list, MODEL_ID_INTERVIEW, max_tokens=300)
    if isinstance(response, dict) and "error" in response:
        return response["error"]
    return response

def get_interview_evaluation(full_transcript_text):
    """
    Acts as the AI Evaluator.
    Takes the full transcript and returns a JSON score.
    """
    system_prompt = """
You are an expert interview evaluator.
Based on the interview transcript provided by the user, you will:
1.  Identify the main topic of the interview (e.g., "UPSC", "Google SWE", "Medical School").
2.  Provide a "Confidence Score" from 0 to 100 based on that topic.
3.  Provide a "Clarity Score" from 0 to 100 based on that topic.
4.  Provide 3 concise bullet points of constructive feedback.
5.  Provide 2 bullet points on strong points.
You MUST return your response as a single, valid JSON object. Do NOT include any text before or after the JSON.
The JSON object must follow this exact structure:
{
  "topic": "UPSC",
  "score_confidence": 85,
  "score_clarity": 75,
  "feedback": [
    "Feedback point 1...",
    "Feedback point 2...",
    "Feedback point 3..."
  ],
  "strengths": [
    "Strength point 1...",
    "Strength point 2..."
  ]
}
"""
    user_prompt = f"Please evaluate this interview transcript:\n\n{full_transcript_text}"
    response_string = query_groq_api(system_prompt, user_prompt, MODEL_ID_EVALUATION, max_tokens=500)
    if isinstance(response_string, dict) and "error" in response_string:
        return response_string
    try:
        json_string = response_string.strip().lstrip("```json").lstrip("```").rstrip("```")
        json_start = json_string.find('{')
        if json_start == -1:
            raise json.JSONDecodeError("No JSON object found in AI response.", response_string, 0)
        json_end = json_string.rfind('}')
        if json_end == -1:
             raise json.JSONDecodeError("No closing brace for JSON found.", response_string, 0)
        json_string_cleaned = json_string[json_start:json_end+1]
        evaluation_data = json.loads(json_string_cleaned)
        if "score_confidence" not in evaluation_data or "feedback" not in evaluation_data:
             raise ValueError("JSON response is missing required keys.")
        return evaluation_data
    except Exception as e:
        print(f"Failed to decode AI's JSON response for evaluation: {e}")
        print(f"AI returned: {response_string}")
        return {"error": "The AI failed to generate a valid evaluation. Please try again."}

# --- *** VISUALIZER FUNCTION (FLOWCHART-ONLY) *** ---
def generate_ai_diagram(topic):
    """
    Asks the AI to generate a text-based diagram in Mermaid.js syntax.
    """
    
    # This system prompt has been updated with stricter rules
    system_prompt = """
You are an expert AI Concept Visualizer. Your ONLY job is to convert complex user topics into a clean, simple, and valid Mermaid.js flowchart syntax.
- You MUST respond with ONLY the Mermaid.js code block.
- Do NOT include "Here is your diagram:", "```mermaid", "```", or any other text, explanation, or markdown.
- The diagram must be "Top-Down" (graph TD).
- Keep node labels short and concise.
- **RULE 1:** All relationship lines MUST end with a node ID (e.g., `A --> B`).
- **RULE 2:** All node definitions MUST be complete with matching parentheses or brackets (e.g., `A(Label)`, `B[Label]`, `C{Decision}`).
- **RULE 3:** NEVER write an incomplete node definition (e.g., `A(` or `B[`).
- **RULE 4:** When adding text to a link, the syntax MUST be `A -->|text| B` or `A -- text --> B`. NEVER add an extra `>` before the final node, like `A -->|text|> B`.
- **RULE 5:** Do NOT use HTML entities (like `&apos;` or `&quot;`). Use standard characters (like ' or ").

Example 1: User asks for "The Water Cycle".
Your response:
graph TD
    A(Evaporation) --> B(Condensation);
    B --> C(Precipitation);
    C --> D(Collection);
    D --> A;

Example 2: User asks for "Ohm's Law".
Your response:
graph TD
    A(Ohm's Law) --> B(V = I * R);
    A --> C(I = V / R);
    A --> D(R = V / I);
"""
    
    user_prompt = f"Convert the following topic into Mermaid.js flowchart syntax: {topic}"
    
    response = query_groq_api(system_prompt, user_prompt, MODEL_ID_VISUALIZER, max_tokens=1024)
    
    if isinstance(response, dict) and "error" in response:
        return response

    # Basic validation to ensure it looks like Mermaid code
    if "graph TD" not in response and "flowchart TD" not in response:
        print(f"AI returned invalid diagram code: {response}")
        return {"error": "The AI failed to generate a valid diagram. It may be too complex."}

    # Success! Return the raw Mermaid code.
    return {"mermaid_code": response}

# --- *** NEW MUSIC FUNCTION (RESTORED) *** ---
# --- *** REPLACE THIS FUNCTION IN ai_helper.py *** ---

# --- *** REPLACE THIS FUNCTION IN ai_helper.py *** ---

# --- *** REPLACE THIS FUNCTION IN ai_helper.py *** ---


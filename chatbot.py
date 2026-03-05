import os
import google.generativeai as genai
from fastapi.responses import StreamingResponse

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

async def get_ai_response(question: str, log_data: str, stream: bool = True):
    prompt = f"""
    You are an AI assistant for a multi-tenant organization management system.
    The admin is asking a question about today's activity logs.
    
    Logs:
    {log_data}
    
    Question: {question}
    
    Provide a concise and helpful summary based ONLY on the provided logs.
    """
    
    if not model:
        # Fallback if no API key is provided
        msg = "AI Chatbot is currently in mock mode (GEMINI_API_KEY not set). Logs summarized: " + str(len(log_data.split('\n'))) + " entries found."
        if stream:
            async def mock_stream():
                yield msg
            return StreamingResponse(mock_stream(), media_type="text/plain")
        return {"answer": msg}

    if stream:
        def generate_stream():
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                yield chunk.text
        return StreamingResponse(generate_stream(), media_type="text/plain")
    else:
        response = await model.generate_content_async(prompt)
        return {"answer": response.text}

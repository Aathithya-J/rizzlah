from fastapi import FastAPI, Form, Path, Request
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from doctr.models import ocr_predictor
from doctr.io import DocumentFile
import os
import json
from fastapi.staticfiles import StaticFiles
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

help_model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction="""
If you see text that resembles a conversation: 
Give me a comment on how well the person rizzed up the other in Singlish. Your comment for the "how well did the person rizz up the other" should be at max 2 sentences long and must be as SINGLISH as possible and should also be as exaggerated as possible. For example, if it was really bad, it should be insulting, but if it is really good, it should give a lot of good compliments.

Give me a Rizz rating which can range from 0-100, just give the number, no need to add /100. For example, just give the number 49, 48 etc.

Generate a message that the person mentioned in the conversation can directly paste into their messages app to continue to rizz up the other person in the current conversation in the best possible way. The next message should be as rizzler as possible, and it must fit perfectly into the conversation that I give you and not be awkward. Make sure that the comments are phrased such that they are in first person. STRICTLY Do NOT include any other comments of your own such as "Try this instead", or anything similar.

Give your response in JSON format, like so:
{
  "comments": "",
  "score": "",
  "generated_msg": ""
}

Make sure it is not too explicit.

Anyway, if it does not look like text from a chatting platform or emailing platform, give them a rizzing score of 0 and insult them for it in Singlish too!

You must always provide a generated message, no matter the score or the comments.
                                   
Please be a bit more lenient with your grading and comments
""")
challenge_model = genai.GenerativeModel(model_name="gemini-1.5-flash",
  system_instruction="Generate a challenge JSON, in which there is a conversation occuring over a text messaging platform such as Instagram or Whatsapp, and the user needs to guess a following response to rizz up the other party well. Please generate the json using the specified JSON Schema when I tell you the \"Generate\" word. Do not include any placeholders, just include them in for me. DO NOT INCLUDE evaluation criteria. Try to make it at least 5 messages long, and allow the user of our app the opportunity to show off their full rizzing power. Make sure that the last message sent is NOT from the user themself. Do not format the JSON in any way, and pin the challenged user's name to \"You\". Make sure that you keep the root dictionary's key name to \"messages\". \n\nFOLLOW MY JSON SCHEMA:\nMessage = {\"user\": str, \"message\": str}\nReturn List[Message]\n\nDO NOT INCLUDE ANY PLACEHOLDERS. JUST PUT IN EXAMPLE SCENARIOS\n\nDO NOT INCLUDE THE EVALUATION CRITERIA.",
)

challenge_evaluate_model = genai.GenerativeModel(model_name="gemini-1.5-flash",
  system_instruction="I will provide you with an input JSON in the following format:\nMessage = {\"user\": str, \"message\": str}\nInput: List[Message]\n\nGive me a comment on how well the person rizzed up the other in Singlish. Your comment for the \"how well did the person rizz up the other\" should be at max 2 sentences long and must be as SINGLISH as possible and should also be as exaggerated as possible. This must be mostly based on the very last message as thats the message that the user guessed\n\nGive me a Rizz rating which can range from 0-100, just give the number, no need to add /100. For example, just give the number 49, 48 etc. This must be mostly based on the very last message as thats the message that the user guessed\n\ngive your response in json format, like so:\n{\n\"comments\": \"\",\n\"score\": \"\",\n}\n\nMake sure it is not too explicit.",
)

class ChallengeResponse(BaseModel):
    response: str = None

origins = "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_challenges = {
    # "IP": "TEXT",
}

# Serve index.html for the root route
# @app.get("/")
# async def serve_root():
#     return FileResponse(Path("rizzlah/index.html"))

# @app.get("/")
# def serve_website():
#     html_file_path = "./rizzlah/index.html"
#     with open(html_file_path, "r") as f:
#         content = f.read()
#     return HTMLResponse(content)

@app.get("/")
def serve_website():
    return RedirectResponse(url="/static/index.html")

# @app.get("/index.html")
# def serve_website():
#     html_file_path = "./rizzlah/index.html"
#     with open(html_file_path, "r") as f:
#         content = f.read()
#     return HTMLResponse(content)

# @app.get("/challenge.html")
# def serve_challenge():
#     html_file_path = "./rizzlah/challenge.html"
#     with open(html_file_path, "r") as f:
#         content = f.read()
#     return HTMLResponse(content)

# , age: str = Form(...), gender: str = Form(...),interests: str = Form(...)
@app.post("/api/upload")
async def upload(file: UploadFile=File(...)):
    try:
        contents = file.file.read()
        with open(file.filename, 'wb') as f:
            f.write(contents) 
    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()
    
    image_path = file.filename

    # Create an OCR predictor
    predictor = ocr_predictor(pretrained=True)

    # Perform OCR on the image
    result = predictor(DocumentFile.from_images(image_path))

    extracted_text = ""

    for page in result.pages:
        for block in page.blocks:
            for line in block.lines:
                line_text = " ".join(word.value for word in line.words)
                extracted_text += line_text + "\n"
    
    # extracted_text = f"age={age}\ngenderofotherparty={gender}\ninterests={interests}\n" + extracted_text
    
    # Text has been extracted
    print(extracted_text)

    os.remove(file.filename)

    response = help_model.generate_content(extracted_text)
    response = response.text.replace("json\n{\n  ", "{").replace("\n}", "}").replace("```", "")

    print(response)

    response_json = json.loads(response)

    with open("log.txt", "a") as f:
        f.write("===== REQUEST =====\n")
        f.write(f"Extracted text: {extracted_text}\n")
        f.write(f"Response: {response}\n")
        f.write("Score: " + str(response_json["score"]) + "\n")
        f.write("Comments: " + response_json["comments"] + "\n")
        f.write("Generated message: " + response_json["generated_msg"] + "\n")
        f.write("===== END REQUEST =====\n")
        f.write("\n")

    return {
        "extracted_text": extracted_text,
        "comments": response_json["comments"],
        "score": int(str(response_json["score"]).replace("/100", "")),
        "generated_msg": response_json["generated_msg"]
    }

@app.post("/api/challenge_generate")
def generate_challenge(request: Request):
    response = challenge_model.generate_content("Generate")
    response = response.text.replace("json\n{\n  ", "{").replace("\n}", "}").replace("```", "")

    response_json = json.loads(response)

    with open("log.txt", "a") as f:
        f.write("===== CHALLENGE GENERATE REQUEST =====\n")
        f.write("Generated message: " + response)
        f.write("===== CHALLENGE GENERATE END REQUEST =====\n")
        f.write("\n")
    
    current_challenges[request.client.host] = response

    print(current_challenges)

    return response_json

@app.post("/api/challenge_evaluate")
def evaluate_challenge(response: ChallengeResponse, request: Request):
    print(current_challenges)
    current_convo_json = json.loads(current_challenges[request.client.host])

    print(current_convo_json)

    current_convo_json["messages"].append({"user": "You", "message": response.response})

    response = challenge_evaluate_model.generate_content(json.dumps(current_convo_json))
    response = response.text.replace("json\n{\n  ", "{").replace("\n}", "}").replace("```", "")
    response = json.loads(response)
    
    # Reset Global Challenge
    del current_challenges[request.client.host]

    print(current_challenges)

    return {
        "comments": response["comments"],
        "score": int(str(response["score"]).replace("/100", ""))
    }

app.mount("/static", StaticFiles(directory="rizzlah", html=True), name="rizzlah")
# from doctr.models import ocr_predictor
# from doctr.io import DocumentFile

# # Load an image
# image_path = 'test.png'

# # Create an OCR predictor
# predictor = ocr_predictor(pretrained=True)

# # Perform OCR on the image
# result = predictor(DocumentFile.from_images(image_path))

# extracted_text = ""

# for page in result.pages:
#     for block in page.blocks:
#         for line in block.lines:
#             line_text = " ".join(word.value for word in line.words)
#             extracted_text += line_text + "\n"

# print(extracted_text)

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel('gemini-1.5-flash', model_name="gemini-1.5-flash",
  system_instruction="If you see text that resembles a conversation: \nGive me a comment on how well the person rizzed up the other in Singlish. Your comment for the \"how well did the person rizz up the other\" should be at max 2 sentences long and must be as SINGLISH as possible and should also be as insulting as possible.\n\nGive me a Rizz rating which can range from 0-100, just give the number, no need to add /100. For example, just give the number 49, 48 etc.\n\nGenerate a message that the person mentioned in the conversation can directly paste into their messages app continue to rizz up the other person in the current conversation in the best possible way.  The next message should be as rizzler as possible, and it must fit perfectly into the conversation that I give you and not be awkward. STRICTLY Do NOT include any other comments of your own such as \"Try this instead\", or anything similar.\n\ngive your response in json format, like so:\n{\n\"comments\": \"\",\n\"score\": \"\",\n\"generated_msg\": \"\",\n}",
)


response = model.generate_content("The opposite of hot is")
print(response.text)
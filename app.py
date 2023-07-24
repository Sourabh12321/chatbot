import os
from flask import Flask, request, jsonify
import openai
from dotenv import load_dotenv
from pymongo import MongoClient
import bcrypt
import jwt
from datetime import datetime, timedelta
from middleware.middlewares import check_login_status 
from config.db import get_mongo_client
from flask_cors import CORS



# Load environment variables from .env file
load_dotenv()


app = Flask(__name__)
CORS(app)
openai.api_key = os.getenv("OPENAI_API_KEY")


client = get_mongo_client()
db = client["Chatbot"]  # Replace "your_database_name" with your actual database name
users = db["user"]
chats = db['chats']
prompts = db['prompt']  # Replace "your_collection_name" with your actual collection name




@app.route("/register", methods=["POST"])
def register():
    # Get the registration data from the request
    registration_data = request.get_json()
    name = registration_data.get("name")
    email = registration_data.get("email")
    password = registration_data.get("password")

    print(name, email, password)
    # Check if the required fields are provided
    if not name or not email or not password:
        return jsonify({"message": "Missing required fields"}), 400

    # Check if the user already exists in the database
    existing_user = users.find_one({"email": email})
    if existing_user:
        return jsonify({"message": "User already exists"}), 409

    # Hash the password before storing it in the database
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    # Create a new user document
    new_user = {
        "name": name,
        "email": email,
        "password": hashed_password
    }

    # Insert the new user into the database
    users.insert_one(new_user)

    return jsonify({"message": "Registration successful"}), 200



@app.route("/login", methods=["POST"])
def login():
    # Get the login data from the request
    login_data = request.get_json()
    email = login_data.get("email")
    password = login_data.get("password")

    # Check if the required fields are provided
    if not email or not password:
        return jsonify({"message": "Missing required fields"}), 400

    # Check if the user exists in the database
    user = users.find_one({"email": email})
    if not user:
        return jsonify({"message": "Invalid email or password"}), 401

    # Check if the password is correct
    if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return jsonify({"message": "Invalid email or password"}), 401

    # Generate a JWT token with the user's email and an expiration time
    token_payload = {
        "email": user["email"],
        "exp": datetime.utcnow() + timedelta(days=1)  # Token expiration time (1 day in this example)
    }
    token = jwt.encode(token_payload, "chatbot", algorithm="HS256")

    # Get the user's id
    user_id = str(user["_id"])

    # Return the response with the id and token included
    return jsonify({"message": "Login successful", "name": user["name"], "id": user_id, "token": token}), 200




@app.route("/")
def home():
    return jsonify({"msg": "Home page"})



@app.route('/parent/<id>', methods=['GET', 'POST'])
@check_login_status
def parent(id):
    if request.method == 'GET':
        user_chats = chats.find_one({"userid": id})
        if user_chats is not None:
            response_data = user_chats["chat"]
            return jsonify({'response': response_data})
        else:
            return jsonify({'response': []})

    if request.method == 'POST':
        keyword = request.json.get('keyword')
        print(keyword)
        print(id)
        prom = prompts.find_one({"userid": id})
        user_chats = chats.find_one({"userid": id})
        
        if prom is None:
            obj = {
                    "userid": id,
                    "prompt":"Act as parenting influencer. You provide solutions to all parenting problems, you have to answer in the language in which the user asks you the question. While answering to them reply as human not machine try to replicate the tone of user.\n\nPrompt: My daughter is 19 months. But usko me koi bhi chiz nahi deti hu na hi uski koi zid Puri karti hu tou wo mujhe hit karti hai She is just 19 months. how can I control this behaviour Ya kabhi kabhi wo masti me bhi muihe hit kar deti hai.\nAnswer: Aapki beti choti hai. Is umar mein kuch na milne pe kaise behave karna hai bachon ko pata nahin hota. Emotion pe kaabu nahin hota. Lekin bachon ka bhi maarna rok sakte hai. Thoda time laga ke. Kabhi bhi jiss cheez ke live bacha hit kar raha hai woh puri nahin karni kyonki phir bachey ko lagta hai ke maarne se cheez milegi. So no means no. But pyaar se. Aap calm aawaaz mein usko bol sakti hai - No using hands and feet. Mujhe lagti hai. Same line hi humein baar baar use karni hai. Phir Aap ski feeling ko acknowledge karo. Ke aapko woh chahiye. Haan? Mujhe pata hai. Mujhe pata hai aapko aacha lagta hai. Lekin maarne se kabhi nahin milega. Ya kabhi kabhi wo Bachon ke nervous system ko touch karke se calmness milti hai. Unko touch karke pyaar se mana karenge to baat samajne ka chance zada hai. Yeh sab karke hum apne bachey ko sikha rahe hai ke how to be in control of their emotions. Yeh important learning sabse pehle maa baap se hi aati hai :-). Lots of love to your family.\n\n Prompt:My 2yr old son is troubling a lot while feeding him, we tried everything, we used to slow meal and eat with him, mobile/TV but after 1-2 spoon he doesn't accept it.We even asked doctor but he said keep trying, we literally wait 30-40min for 2 spoon and get frustrated 🥴.What do you suggest, how to handle it? Some time we think kuchh medicine aani chahie jo ek bar khilade to pira din chal jaye \n\n Answer:'It's ok na if he doesn't eat.So four things- there is a family food time. we sit together and eat. Small kids can't sit and eat so he might just roam around. And may be eat and may be not eat- you can put some healthy food at his eye level so that he can pick anytime and take it - fruits etc- ensure that he does not get junk food later if he asks- finally involve him in the process of cooking, cutting (wooden knife etc)And trust his animal instinct. We are animals, we will eat when we are hungry. There is no way to go without it. Don't let your anxiety of mera beta nahin kha raha come into pictureand don't use mobile/TV :-)\'\n\n Prompt:  \'I hav found that u understand d subconscious mind of d child .\nI hav a request pls can u tell when to start preschool or play school for kids - i mean what age n everyone tells it's normal if they cry for first few days .\nI want to kno how does psychology works of a child ....\nI couldn't see my child crying her heart out bcoz she dint wanted to go n everyone told me I'm over pampering her n let her cry ....\nIt will b gr8 if u could spare some time n answer my query\'\n\n Answer:kids cry for a lot of reasons.- first few days, they can have separation anxiety. If you have it when you go to drop her, she will sense it. So imp for you to be calm- say you are leaving from your house for school and she says mumma i dont want to go, starts to cry a bit and to keep her calm you say we are not going to school but then you do go to school, she starts crying again. So our lying is contributing to her crying. We should 100% stop lying.It is imp to see that the school has the right environment for the child. That means - place to play, free play, to run around, loving teachers. A good play school can help a child make friends and be comfortable in the company of others apart from parents.What is most imp for your child to know is that you are there for her. And that you will come back to pick her. Once she feels secure she will be ok",
                }
            prompts.insert_one(obj)
        
        main = prompts.find_one({"userid":id})
        passing_data = main['prompt']+"\n" + "prompt:"+" "+ keyword+"Try to give the response in the same language as asked"
        print(passing_data)

        try:
            def run_prompt():
                # prompt = passing_data
                response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=passing_data,
                max_tokens=300,
                temperature=0.9
                )
                generated_response = response.choices[0].text.strip()
                # ... (rest of the code for the run_prompt function)
                return generated_response

            response = run_prompt()
            savedata = passing_data+"response:"+" "+response
            # print(savedata)
            prompts.update_one(
                {"userid": id},
                {"$set": {"prompt": savedata}}
            )
            # print(response)
            if user_chats is None:
                obj = {
                    "userid": id,
                    "chat": [
                        {"text": keyword, "fromuser": True},
                        {"text": response, "fromuser": False}
                    ]
                }
                chats.insert_one(obj)
                

            else:
                chat1 = {"text": keyword, "fromuser": True}
                chat2 = {"text": response, "fromuser": False}
                chats.update_one(
                    {"userid": id},
                    {"$push": {"chat": chat1}}
                )
                chats.update_one(
                    {"userid": id},
                    {"$push": {"chat": chat2}}
                )

            user_chat_array = chats.find_one({"userid": id})
            response_data = user_chat_array["chat"]
            print(response_data)
            return jsonify({'response': response_data})

        except Exception as e:
            print("Error:", str(e))
            return jsonify({'error': str(e)})


# Remove any duplicate @app.route decorators if present

@app.route("/clearchat/<id>", methods=['DELETE'])
def clearchat(id):
    result = chats.delete_one({"userid": id})
    result2 = prompts.delete_one({"userid": id})
    
    # Check if the delete operation was successful
    if result.deleted_count == 1 and result2.deleted_count == 1:
        return jsonify({"List": "Chat deleted successfully."})
    else:
        return jsonify({"List": "Chat with the given id not found."})



@app.route("/tune")
def tune_list():
    openai.api_key = os.getenv('OPENAI_API_KEY')
    response = openai.FineTune.list()
    return jsonify({"List":response})

if __name__ == '__main__':
    app.run(port=4000)

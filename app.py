from flask import Flask, render_template, redirect, url_for, request
import random
import pandas as pd
from time import sleep
import os
import base64
import json, requests
import jwt

is_msa_account = True
config_file = "config.json"
if config_file:
    with open(config_file, "r") as f:
        config_data = f.read()
    config = json.loads(config_data)
else:
    raise ValueError("Please provide config.json file with account information.")

client_id = config["client_id"]  
redirect_uri = config["redirect_uri"]
scopes = config["scopes"]

def refreshAuthzToken(client_id, refresh_token, redirect_uri, scopes, is_msa_account):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {
        # Request parameters
    }
    url = f"https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": f"{client_id}",
        "scope": f"{scopes}",
        "refresh_token": f"{refresh_token}",
        "redirect_uri": f"{redirect_uri}",
        "grant_type": "refresh_token",
    }
    if is_msa_account == True:
        url = "https://login.live.com/oauth20_token.srf"
    req = requests.post(url, params=params, data=data, headers=headers)
    content = json.loads(req.content)
    access_token = content["access_token"]
    id_token = content["id_token"]
    refresh_token = content["refresh_token"]
    return id_token, access_token, refresh_token


def callGraphApi(url, user_token, method="get", payload=""):
    params = {}
    headers = {"Authorization": f"{user_token}", "Content-Type": "text/plain"}
    if method == "put":
        r = requests.put(url=url, headers=headers, params=params, data=payload)
    else:
        r = requests.get(url=url, headers=headers, params=params)
    return json.loads(r.content)


def getAuthDetails(is_msa_account=is_msa_account):
    if os.path.exists("refresh.txt") == False:
        print(
            "I couldn't find a refresh token cache file. Running cache_refresh_token.py to try and get one."
        )
        os.system("start python cache_refresh_token.py")
        while os.path.exists("refresh.txt") == False:
            sleep(1)
        print("Found refresh.txt!")

    with open("refresh.txt", "r") as cached_refresh_token:
        code = cached_refresh_token.read()

    # print(code)
    try:
        if len(code.split(".")[2]) == 37:
            is_msa_account = True
    except Exception as e:
        pass

    id_token, access_token, refresh_token = refreshAuthzToken(
        client_id, code, redirect_uri, scopes, is_msa_account
    )
    # print(access_token)

    decoded_id_token = jwt.decode(id_token, verify=False)
    # print(json.dumps(decoded_id_token, indent=2, sort_keys=True))
    user = decoded_id_token["preferred_username"]
    return user, access_token


def sendBuddyMail(token, user, drawer_mail, drawer_name, encoded_buddy, scenario):
    mail_json = {
      "message": {
        "subject": f"You did it! {scenario}",
        "body": {
          "contentType": "HTML",
          "content": f"""
          <body>
          <img src="https://cdn.costumewall.com/wp-content/uploads/2016/09/buddy-the-elf-costume.jpg?w=640" alt="img" />
          <h1>It's Christmas Time {drawer_name} !!!</h1> 
          <p>You drew the following buddy for {scenario}: </p>
          <h2>{encoded_buddy}</h2>
          <a href="https://www.bing.com/search?q=base64+decode">Click here to decode your Christmas Buddy!</a>
          </body>
          """
        },
        "toRecipients": [
          {
            "emailAddress": {
              "address": f"{drawer_mail}"
            }
          }
        ],
        "internetMessageHeaders":[
          {
            "name":"x-custom-header-group-name",
            "value":"Christmas"
          },
          {
            "name":"x-custom-header-group-id",
            "value":"NV001"
          }
        ]
      }
    }  
    verbs = ["excitedly", "with trepadation", "jauntily", "softly", "pensively", "happily", "with an abundance of caution", "full of joy", "while sighing wistfully", "in a state of panic", "with a chicken under their arm", "with a wink", "dramatically"]
    sleep(3)
    verb = random.randint(0,len(verbs)-1)
    print(f"\n{drawer_name} approaches the hat {verbs[verb]}...")
    sleep(2)
    print(f"\n{drawer_name} pauses and then pulls out a name!")
    sleep(1)
    print(f"Sending mail to {drawer_mail}!")
    url = f"https://graph.microsoft.com/v1.0/users/{user}/sendMail"
    params = {}
    headers = {"Authorization": f"{token}",
              "Content-type": "application/json"}
    r = requests.post(url, params=params, data=json.dumps(mail_json), headers=headers)
    print(r.text)
    return r



family = [
    {"Name":"Alice", "email":"alice@example.com"},
    {"Name":"Bob", "email":"bob@example.com"},
    {"Name":"Charlie", "email":"charlie@example.com"},
    {"Name":"Diana", "email":"diana@example.com"},
    {"Name":"Eve", "email":"eve@example.com"},
    {"Name":"Frank", "email":"frank@example.com"},
    {"Name":"Grace", "email":"grace@example.com"},
    {"Name":"Harry", "email":"harry@example.com"}
]

nameslips = []
[nameslips.append(member[1]['Name']) for member in enumerate(family)]



import random

def do_the_stuff(family):
    hat = [member['Name'] for member in family]
    result = []
    for member in family:
        # add conditions for cases where you want to avoid certain people getting each other
        choices = [name for name in hat if name != member['Name'] and not (member['Name'] == "Harry" and name == "Alice") and not (member['Name'] == "Alice" and name == "Harry")
                   and not (member['Name'] == "Alice" and name == "Bob") and not (member['Name'] == "Bob" and name == "Alice")]
        if not choices:
            return do_the_stuff(family)
        picked = random.choice(choices)
        result.append({member['Name']: picked})
        hat.remove(picked)
    return result



app = Flask(__name__)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
      result = do_the_stuff(family)
      for i in range(len(result)):
        for key, value in result[i].items():
          for member in family:
            if member['Name'] == key:
              buddy_data = f"========== {value} =========="
              buddy_bytes = buddy_data.encode('ascii')
              base64_bytes = base64.b64encode(buddy_bytes)
              base64_message = base64_bytes.decode('ascii')
              auth = getAuthDetails()
              sendBuddyMail(auth[1], auth[0], member['email'], member['Name'], base64_message, scenario="Christmas Morning Elf Gift" )
      sleep(1)
      return render_template("run.html", content="All the names were drawn and sent, Merry Christmas!")           
    else:
      return render_template("index.html")

@app.route("/ping")
def ping():
  return(f"Let's go")

@app.context_processor
def utility_processor():
    def sleeper(numsec):
      sleep (numsec)
      return 
    return dict(sleeper=sleeper)


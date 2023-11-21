#!/usr/bin/env python
# if we don't have a refresh token cached on disk, go get one.
# spin up a simple Web server that will listen for auth code, then exchange that for a token and cache it locally in a file.
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, requests

config_file = "config.json"
if config_file:
    with open(config_file, "r") as f:
        config_data = f.read()
    config = json.loads(config_data)
else:
    raise ValueError("Please provide config.json file with account information.")

client_id = config["client_id"]  # Multi-tenant DriveReader App
redirect_uri = config["redirect_uri"]
scopes = config["scopes"]


def getAuthzToken(client_id, code, redirect_uri, scopes, is_msa_account):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {
        # Request parameters
    }
    url = f"https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": f"{client_id}",
        "scope": f"{scopes}",
        "code": f"{code}",
        "redirect_uri": f"{redirect_uri}",
        "grant_type": "authorization_code",
    }
    if is_msa_account == True:
        url = "https://login.live.com/oauth20_token.srf"
    req = requests.post(url, params=params, data=data, headers=headers)
    content = json.loads(req.content)
    refresh_token = content["refresh_token"]
    return refresh_token


# TODO: spinning up a web server might be overkill. Consider doing something simpler like straight up socket connection.
class HTTPServer_RequestHandler(BaseHTTPRequestHandler):
    # GET
    def do_GET(self):
        is_msa_account = False
        # Send response status code
        self.send_response(200)
        # Send headers
        self.send_header("Content-type", "text/html")
        self.end_headers()
        x = str.split(self.path, "=")
        print(f"\nGet string: split on '=': {x}")
        if len(x) >= 2:
            raw_code = x[1]
            if len(x) == 2:
                code = raw_code
            else:
                code = raw_code.split("&")[0]
            print(code)
            try:
                if len(code.split(".")[2]) == 37:
                    is_msa_account = True
            except Exception as e:
                print(e)
                pass
            refresh_token = getAuthzToken(
                client_id, code, redirect_uri, scopes, is_msa_account
            )
            with open("refresh.txt", "w") as token_file:
                token_file.write(refresh_token)
                self.wfile.write(
                    bytes(
                        "Cached refresh token locally. You can close this window and shutdown the server script.",
                        "utf8",
                    )
                )
        return


def run():
    import webbrowser

    print("starting server...")

    server_address = ("127.0.0.1", 8076)
    httpd = HTTPServer(server_address, HTTPServer_RequestHandler)

    print("running server...")

    httpd.serve_forever()


import webbrowser

auth_site = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}"
# Open url in a new window of the default browser, if possible
webbrowser.open_new(auth_site)

run()

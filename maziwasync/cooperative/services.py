import os

import requests  


class MpesaPayment:

    def __init__(self):

        # Safaricom app credentials used to generate access token
        self.consumer_key = "GTWADFxIpUfDoNikNGqq1C3023evM6UH"
        self.consumer_secret = "amFbAoUByPV2rM5A"

        # Daraja B2C credentials
        self.initiator = "testapi"
        self.security_credential = "oQZ1PBWzZOhfHAxDsWS5ezea4pD2ENa2tGuSNz8UZxZuFF1LBBDhqChGwkBTa1kUYArw0y5t/r532kVPTbocNp9LLTyW5dQsP/2EM4nBUzmnZaJxOPtjzMZ/oWLuo1dRBOLgIuNZ/hiGNGAFHzLCl2g3Ya/5S0bcgjPT4rcTyltdWAsXV+IRVVlRbiHJBmi0u8p0crtcoY1bWAvcLIWkp0FcVY2DXcLqDQTksuSZ2APBy8a+7s32shQbooR9xCIqqko51Ng80fFCcyjXfzggX/nz1SDJwe1PFANo+33eFG+SAyaE409P31pw2Q1LKRUyF9hseGTcauGTWHZTFR8UBQ=="
        # Daraja endpoints
        self.token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        self.payment_url = "https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest"

        # Public HTTPS endpoint where Safaricom sends transaction results (Generated via ngrok)
        self.callback_url = "https://klaus.alwaysdata.net/api/cooperative/Callback/"

    def get_token(self):
        # Requests an OAuth2 temporary access token from Safaricom
        response = requests.get( self.token_url, auth=requests.auth.HTTPBasicAuth( self.consumer_key, self.consumer_secret))

        # Return only the token
        return response.json()["access_token"]
def pay_farmer(self, phone, amount):
    token = self.get_token()

    payload = {
        "Initiator": self.initiator,
        "SecurityCredential": self.security_credential,
        "CommandID": "BusinessPayToBulk",
        "Amount": amount,
        "PartyA": "600977",
        "PartyB": "600000",
        "SenderIdentifierType": "4",
        "RecieverIdentifierType": "4",
        "AccountReference": "MILK",
        "Requester": phone,
        "Remarks": "Milk payment",
        "QueueTimeOutURL": self.callback_url,
        "ResultURL": self.callback_url
    }

    response = requests.post(self.payment_url, json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )

    result = response.json()
    print("=====Safaricom response=====")
    print("Status:", response.status_code)
    print("Body:", result)

    return result
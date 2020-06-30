#!/usr/bin/env python3
import json
import os

import requests
import base64
from datetime import datetime
import argparse

## hand-made jwt ...
def extractJwtTokenBody(jwtToken):
    jwtParts = jwtToken.split(".")
    bodyEncoded = jwtParts[1]
    return json.loads(base64.b64decode(bodyEncoded + "==="))  ## add === to avoid padding errors

def dumpAsTimestamp(timeInMs):
    asDatetime=datetime.fromtimestamp(timeInMs)
    return asDatetime.isoformat()
claimFormatter= {
    'exp': dumpAsTimestamp,
    'iat': dumpAsTimestamp,
}

def formatJwtClaim(key,value):
     extrFmt=claimFormatter.get(key)
     extraInfo = ' # ' + extrFmt(value) if (extrFmt) else ''
     return key + ':' + str(value)  + extraInfo


#### keycloak functions

def login(loginData):
    token_ep_url = keycloakBase + '/realms/master/protocol/openid-connect/token'

    response = requests.post(token_ep_url, loginData)
    response_json = json.loads(response.content)

    return response_json


### simple helper ...
## env or userInput
def envOrAsk(envVar,prompt):
    res = os.getenv(envVar)
    if res is None:
        return input(prompt)
    else:
        return res
##
def valOrAsk(optionName,args,prompt):
    val=args.__getattribute__(optionName)
    if val is not None:
      return val
    else:
        return input(prompt)


###  define the args
def defineMainParser():
    parser = argparse.ArgumentParser(description='keycloak tiny admin')
    parser.add_argument('--base', help='Base url of keycloak', default='http://localhost:8080/auth')
    parser.add_argument('cmd', help='the command to use')
    parser.add_argument('--realm', help='id of the realm to use')
    parser.add_argument('--displayName', help='used when creating a realm')
    parser.add_argument('--client', help='id of the client to use')
    parser.add_argument('--url', help='used as redirectUrl when cmd=addRedirect')

    return parser

### main logic
args = defineMainParser().parse_args()

## extract args ..
keycloakBase= args.base
## build login info
keycloakAdminLogin = {
    'client_id': 'admin-cli',
    'grant_type': 'password',
    'username': envOrAsk('KEYCLOAK_USER','Keycloak user:'),
    'password': envOrAsk('KEYCLOAK_PWD','Keycloak password:'),
    'scope': 'openid'
}
### global var ...
loginData=login(keycloakAdminLogin)
headers = {
    'content-type': 'application/json',
    'Authorization': 'Bearer ' + loginData['access_token']
}

## dump id token

###
class CmdHandler:
    def callCmd(self, args):
        method = getattr(self, args.cmd, lambda: "Unknown cmd")
        return method(args)

    def dumpIdToken(self,args):
            jwtToken = extractJwtTokenBody(loginData['id_token'])
            print('id_token:')
            for claim in sorted(jwtToken.items()):
                print('  ' + formatJwtClaim(claim[0], claim[1]))
    def createRealm(self,args):
        payload={
             'id': args.realm,
            'realm': args.realm,
            'displayName': valOrAsk('displayName',args,'Display name:')
        }
        resp=requests.post(keycloakBase + '/admin/realms', headers=headers, json=payload)
        resp.raise_for_status()
    def deleteRealm(self,args):
        resp=requests.delete(keycloakBase + '/admin/realms/' + args.realm, headers=headers)
        resp.raise_for_status()
    def listClients(self, args):

        resp = requests.get(keycloakBase + '/admin/realms/' + args.realm + "/clients", headers=headers,
                            params={'clientId':args.client})
        resp.raise_for_status()
        clientsFound=json.loads(resp.content)
        if not clientsFound:
            print("# No client(s) found")
            exit(-1)
        else:
            for cc in json.loads(resp.content):
                print(cc)

    def createClient(self,args):
        payload = {
            'id': args.client,
            'publicClient': False
        }
        resp=requests.post(keycloakBase + '/admin/realms/' + args.realm + "/clients", headers=headers, json=payload )
        resp.raise_for_status()
    def deleteClient(self,args):
        resp=requests.delete(keycloakBase + '/admin/realms/' + args.realm + "/clients/" + args.client, headers=headers )
        resp.raise_for_status()

    def dumpClient(self, args):
        resp = requests.get(keycloakBase + '/admin/realms/' + args.realm + "/clients/" + args.client,
                               headers=headers)
        resp.raise_for_status()
        print(resp.content)

    def addRedirect(self,args):
        clientUrl=keycloakBase + '/admin/realms/' + args.realm + "/clients/" + args.client
        resp = requests.get(clientUrl, headers=headers)
        resp.raise_for_status()
        ## do the merge
        oldRedirects=set(json.loads(resp.content).get('redirectUris'))
        newRedirect=valOrAsk('url',args,'RedirectURL:')
        if newRedirect not in oldRedirects:
            newRedirects=set(oldRedirects)
            newRedirects.add(newRedirect)
            payload = {
                'redirectUris': list(newRedirects)
            }
            resp=requests.put(clientUrl, headers=headers ,json=payload )
            resp.raise_for_status()

    def listRealms(self, args):
        resp = requests.get(keycloakBase + '/admin/realms', headers=headers)
        resp.raise_for_status()
        for realm in json.loads(resp.content):
            print(realm['realm'])



CmdHandler().callCmd(args)

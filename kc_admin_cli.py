#!/usr/bin/env python3
import argparse
import base64
import getpass
import json
import os
from datetime import datetime

import requests


## hand-made jwt ...
def extractJwtTokenBody(jwtToken):
    jwtParts = jwtToken.split(".")
    bodyEncoded = jwtParts[1]
    return json.loads(base64.b64decode(bodyEncoded + "==="))  ## add === to avoid padding errors


def dumpAsTimestamp(timeInMs):
    asDatetime = datetime.fromtimestamp(timeInMs)
    return asDatetime.isoformat()


claimFormatter = {
    'exp': dumpAsTimestamp,
    'iat': dumpAsTimestamp,
}


def formatJwtClaim(key, value):
    extrFmt = claimFormatter.get(key)
    extraInfo = ' # ' + extrFmt(value) if (extrFmt) else ''
    return key + ':' + str(value) + extraInfo


#### keycloak functions

def login(loginData):
    token_ep_url = keycloakBase + '/realms/master/protocol/openid-connect/token'

    response = requests.post(token_ep_url, loginData)
    response_json = json.loads(response.content)

    return response_json


### simple helper ...
## env or userInput
def envOrAsk(envVar, prompt, hidden=False):
    res = os.getenv(envVar)
    if res is None:
        if hidden:
            return getpass.getpass(prompt)
        else:
            return input(prompt)
    else:
        return res
##
def valOrAsk(optionName, args, prompt):
    val = args.__getattribute__(optionName)
    if val is not None:
        return val
    else:
        return input(prompt)


###  define the args
def defineMainParser():
    parser = argparse.ArgumentParser(description='keycloak tiny admin')
    parser.add_argument('--base', help='Base url of keycloak',
                        default=os.getenv('KEYCLOAK_BASE', 'http://localhost:8080/auth'))
    parser.add_argument('--repo', help='Path to the local repo', default='./repo')
    parser.add_argument('cmd', help='the command to use')
    parser.add_argument('--realm', help='id of the realm to use')
    parser.add_argument('--displayName', help='used when creating a realm')
    parser.add_argument('--client', help='id of the client to use')
    parser.add_argument('--url', help='used as redirectUrl when cmd=addRedirect')
    parser.add_argument('--override', help='flag, on create, to override the state in the repo')

    return parser


### main logic
args = defineMainParser().parse_args()

## extract args ..
keycloakBase = args.base
## build login info
keycloakAdminLogin = {
    'client_id': 'admin-cli',
    'grant_type': 'password',
    'username': envOrAsk('KEYCLOAK_USER', 'Keycloak user:'),
    'password': envOrAsk('KEYCLOAK_PWD', 'Keycloak password:', hidden=True),
    'scope': 'openid'
}
### global var ...
loginData = login(keycloakAdminLogin)
headers = {
    'content-type': 'application/json',
    'Authorization': 'Bearer ' + loginData['access_token']
}


##


class RepoStorage:
    def __init__(self, baseDir):
        # TODO: add the baseURL as a subdirectory
        self.baseDir = baseDir

    def getClientDir(self, realm):
        return self.baseDir + "/" + realm + "/clients/"

    def getClientFile(self, realm, client):
        return self.getClientDir(realm) + client + ".json"

    def saveClient(self, realm, clientData):
        """Store the clientData at realm/clientData[clientId]"""
        filename = self.getClientFile(realm, clientData['clientId'])
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as db:
            json.dump(clientData, fp=db, sort_keys=True, indent=2)

    def clientExists(self, realm, client):
        filename = self.getClientFile(realm, client)
        return os.path.exists(filename)

    def loadClient(self, realm, client):
        filename = self.getClientFile(realm, client)
        with open(filename, 'r') as db:
            return json.load(db)

    def loadClients(self, realm):
        dirname = self.getClientDir(realm)
        if os.path.exists(dirname):
            clientFiles = [f for f in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, f))]
            for cf in clientFiles:
                with open(os.path.join(dirname, cf), 'r') as db:
                    yield json.load(db)


###
class CmdHandler:
    def __init__(self, repo):
        self.repo = repo

    def callCmd(self, args):
        method = getattr(self, args.cmd, lambda: "Unknown cmd")
        return method(args)

    def dumpIdToken(self, args):
        jwtToken = extractJwtTokenBody(loginData['id_token'])
        print('id_token:')
        for claim in sorted(jwtToken.items()):
            print('  ' + formatJwtClaim(claim[0], claim[1]))

    def createRealm(self, args):
        payload = {
            'id': args.realm,
            'realm': args.realm,
            'displayName': valOrAsk('displayName', args, 'Display name:')
        }
        resp = requests.post(keycloakBase + '/admin/realms', headers=headers, json=payload)
        resp.raise_for_status()
        print('# realm created:' + args.realm)

    def deleteRealm(self, args):
        resp = requests.delete(keycloakBase + '/admin/realms/' + args.realm, headers=headers)
        resp.raise_for_status()
        print('# realm deleted:' + args.realm)

    def checkClients(self, args):
        resp = requests.get(keycloakBase + '/admin/realms/' + args.realm + "/clients", headers=headers,
                            params={'clientId': args.client})
        resp.raise_for_status()
        byId = lambda obj: [obj['id'], obj]
        keycloakClientsById = dict(map(byId, json.loads(resp.content)))
        repoClientsById = dict(map(byId, self.repo.loadClients(args.realm)))
        allClients = set(keycloakClientsById.keys()) | set(repoClientsById.keys())
        print("Clients of realm: " + args.realm + " compared to local repo")
        for client in sorted(allClients):
            inRepo = repoClientsById.get(client)
            inKeycloak = keycloakClientsById.get(client)
            status = None
            if inRepo and not inKeycloak: status = 'missing'
            if not inRepo and inKeycloak: status = 'stale'
            if inRepo and inKeycloak:
                status = 'equals' if inRepo == inKeycloak else 'differs'
            print(client + " : " + status)

    def createClient(self, args):

        # TODO: Use a template, like in ansible??
        payload = {
            'id': args.client,
            'publicClient': False
        }
        if self.repo.clientExists(args.realm, args.client) and not args.override:
            print('# client ' + args.client + ' exists in local repo.')
            exit(-1)

        resp = requests.post(keycloakBase + '/admin/realms/' + args.realm + "/clients", headers=headers, json=payload)
        resp.raise_for_status()
        self.fetchAndStoreClient(args.realm, args.client)
        print('# client created:' + args.realm + '/' + args.client)

    def restoreClient(self, args):
        if not self.repo.clientExists(args.realm, args.client):
            print('# client ' + args.client + ' does not exists in local repo.')
            exit(-1)
        clientUrl = keycloakBase + '/admin/realms/' + args.realm + "/clients/"
        clientData = self.repo.loadClient(args.realm, args.client)
        resp = requests.post(clientUrl, headers=headers, json=clientData)
        resp.raise_for_status()
        self.fetchAndStoreClient(args.realm, args.client)
        print('# client:' + args.realm + '/' + args.client + ': restored from repo')

    def fetchAndStoreClient(self, realm, client):
        resp = requests.get(keycloakBase + '/admin/realms/' + realm + "/clients/" + client, headers=headers)
        resp.raise_for_status()
        self.repo.saveClient(realm, json.loads(resp.content))

    def deleteClient(self, args):
        resp = requests.delete(keycloakBase + '/admin/realms/' + args.realm + "/clients/" + args.client,
                               headers=headers)
        resp.raise_for_status()
        print('# client deleted:' + args.realm + '/' + args.client)

    def dumpClient(self, args):
        resp = requests.get(keycloakBase + '/admin/realms/' + args.realm + "/clients/" + args.client,
                            headers=headers)
        resp.raise_for_status()
        print(json.dumps(json.loads(resp.content), indent=2, sort_keys=True))

    def dumpClientSecret(self, args):
        resp = requests.get(keycloakBase + '/admin/realms/' + args.realm + "/clients/" + args.client + "/client-secret",
                            headers=headers)
        resp.raise_for_status()
        clientSecret = json.loads(resp.content)
        print('# client secret:' + args.realm + '/' + args.client + ': ' + clientSecret.get('value'))

    def addRedirect(self, args):
        clientUrl = keycloakBase + '/admin/realms/' + args.realm + "/clients/" + args.client
        resp = requests.get(clientUrl, headers=headers)
        resp.raise_for_status()
        ## do the merge
        oldRedirects = set(json.loads(resp.content).get('redirectUris'))
        newRedirect = valOrAsk('url', args, 'RedirectURL:')
        if newRedirect not in oldRedirects:
            newRedirects = set(oldRedirects)
            newRedirects.add(newRedirect)
            payload = {
                'redirectUris': list(newRedirects)
            }
            resp = requests.put(clientUrl, headers=headers, json=payload)
            resp.raise_for_status()
            self.fetchAndStoreClient(args.realm, args.client)
            print('# client updated:' + args.realm + '/' + args.client + ': redirect added:' + newRedirect)

    def listRealms(self, args):
        resp = requests.get(keycloakBase + '/admin/realms', headers=headers)
        resp.raise_for_status()
        for realm in json.loads(resp.content):
            print(realm['realm'])


repo = RepoStorage(args.repo)

CmdHandler(repo).callCmd(args)

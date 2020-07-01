## Usage 

This uses no external libs. 
all tasks are done, by calling the kc_admin_cli.py with some parameters:

### Credentials
As I won't store credentials, the programm will accept them via environment variables:
```shell script
export KEYCLOAK_USER=admin
export KEYCLOAK_PWD=admin
```
As a fallback, they are asked from  the user.

Also the base url could be set via environment.
```shell script
export KEYCLOAK_BASE=http://localhost:8080/auth 
``` 

#### 1. dump the id token

`kc_admin_cli.py dumpIdToken`

#### 2. create three realms and a client in each

```
./kc_admin_cli.py createRealm --realm one   
./kc_admin_cli.py  --realm one createClient --client=myClient

./kc_admin_cli.py createRealm --realm two --displayName "Second demo realm"
./kc_admin_cli.py  --realm two createClient --client=anotherClient

./kc_admin_cli.py createRealm --realm three --displayName "Third demo realm"  
./kc_admin_cli.py  --realm three createClient --client=yac
```

To get the clientSecret of a client call
`./kc_admin_cli.py --realm one dumpClientSecret --client myClient`

#### 3. add a redirect URL to one client

`./kc_admin_cli.py  --realm one addRedirect --client myClient  --url http://over.the.rainbow`

#### 4. delete one client

`./kc_admin_cli.py --realm one deleteClient --client=myClient`
 
#### 5a. manual check the clients

Query for the client:
`./kc_admin_cli.py --realm one listClients --client=myClient`

If "# No client(s) found", than the client is gone.

To recreate, all the calls, eg. like
```shell script
./kc_admin_cli.py  --realm one createClient --client=myClient
./kc_admin_cli.py addRedirect --realm one --client myClient  --url http://over.the.rainbow
``` 

needs to be performed. 
 
#### 5b. keep a state (of clients only)

The task "Detect that one of the clients is missing", could mean, that we should be able 
to detect the absence of a client in keycloak, that has been deleted by accident **without** providing 
the clientName as parameter. 
 
`./kc_admin_cli.py --realm one checkClients `

All clients with status: missing are in our local repo (could be used as a git repo) but not in 
keycloak. To "and add it again" recreate the client, with the last know status:

`./kc_admin_cli.py --realm one --client myClient restoreClient`

Note: some infos of the client are currently missing, eg. the client-roles, as they are not returned 
(directly) from the keycloak-admin-api.
   
BUT at least the clientSecret has to be treated special.


### Leftovers

The current design, all in one file, is not a good idea. It should be split in python modules.
The hand-crafted access on the keycloak-admi-api should be replaced by the usage of an existing
module for that. 

Error handling is currently not done at all. At least some more checks on user input should be added.

Complete all the infos of clients, like roles, and add a way to store the clientCredentials, especially 
the clientSecret (Maybe encrypted with the 'KEYCLOAK_PWD')

And of course: no tests included. 


Martin Harm 
  
   




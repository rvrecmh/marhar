## 
I implemented two variants:

### hand-crafted keycloak  
This uses no external libs. I 


I assume, that it is allowed to use 3rd-party python-modules, to handle the 
calls to the keycloak admin rest-api.

This script requires as a setup with eg pip:

`pip3 install python-keycloak`


The last task "detect a missing .." assumes, that we have target state to compare to.

--Therefore all the iterative commands will be implemented as a two step
:   


all tasks are done, by calling the kc_admin_cli.py with some parameters:

### Credentials
As I won't store credentials, the programm will accept them via environment variables:
```shell script
KEYCLOAK_USER=admin
KEYCLOAK_PWD=admin
```
As a fallback, they are asked from  the user.

 

#### 1. dump the id token

`kc_admin_cli.py dumpIdToken`

#### 2. create three realms and a client in each

```
kc_admin_cli.py createRealm --realm one   
kc_admin_cli.py  --realm one createClient --client=myClient

kc_admin_cli.py createRealm --realm two --displayName "Second demo realm"
kc_admin_cli.py  --realm two createClient --client=anotherClient

kc_admin_cli.py createRealm --realm three --displayName "Third demo realm"  
kc_admin_cli.py  --realm three createClient --client=yac

```

#### 3. add a redirect URL to one client

`kc_admin_cli.py addRedirect --realm one --client myClient  --url http://over.the.rainbow`

#### 4. delete one client

`kc_admin_cli.py --realm one --deleteClient myClient`
 
#### 5. syncing ??
The task "Detect that one of the clients is missing" , could mean, that we should be able 
to detect that we need to know the expected clients **without** providing this as parameter. 
 
`kc_admin_cli.py --realm one --checkClients `

To "and add it again" than should mean, that we recreate the client, with the initial provided infos:

`kc_admin_cli.py --realm one --client myClient --restoreClient`
  

 

 




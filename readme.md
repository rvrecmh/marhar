# Keycloak Python Recruiting Challenge

This challenge affects the [Keycloak Admin REST API](https://www.keycloak.org/docs-api/10.0/rest-api/index.html). You can use the documentation or capture the requests using the development tools of your browser, that uses the same API.

The repository only contains a ugly, quick and dirty python script, that lists the names of all existing realms on your Keycloak server. 

For the tasks below you can use this script to get on board or you can start by your own. You can use for your solution, one or several scripts, classes and modules or whatever you want. Do it the way you want.

There is no right solution and we do not expect a solution that is ready for production. We want to see how you act and solve the tasks.

If it takes to much time, do not complete all tasks.


## Preparation

### Keycloak
- Download Keycloak Server from https://www.keycloak.org/downloads. It is your choise, whether you prefer the zip or the docker image.
- Run the server and open the web GUI.
- As username and password for the initial admin user use `admin:admin`

### Github
- Fork this repository
- Clone your repository

### Python
- Download and install python 3.6.x or higher
- Install the requests module `python -m pip install requests`
  - Please install no other modules


## Tasks
1. The response of the authentication request includes an access, id and refresh token. All three of them are Json Web Tokens (JWT). We are intrested in the id token. Please show the body of the token in a human readable way (sorted as list)

2. Create three realms and whithin each realm a confidential client with any configuration.

3. Add another redirect URI to one of the clients.

4. Delete one of the clients.

5. Detect that one of the clients is missing and add it again.


## Final

Make a PULL request with your code.
import sys
from google.cloud import secretmanager

client_secret_manager = secretmanager.SecretManagerServiceClient()


def download(file, secret_name, project_number):
    # Create GCP managed secret: https://console.cloud.google.com/security/secret-manager
    # Make sure to select upload file option, and upload your local copy of settings.toml
    name_medium_secret = "projects/{}/secrets/{}/versions/latest".format(project_number, secret_name)
    response = client_secret_manager.access_secret_version(name=name_medium_secret)
    pwd = response.payload.data.decode("UTF-8")
    with open(file, 'w') as outfile:
        outfile.write(pwd)

# Make sure to create the secret first from the GCP console: https://cloud.google.com/secret-manager/docs/create-secret-quickstart#secretmanager-quickstart-console
# The below upload function only updates the secret, not create.
def upload(file, secret_name, project_number):
    # Build the resource name of the parent secret.
    parent = client_secret_manager.secret_path(project_number, secret_name)
    with open(file, 'r') as outfile:
        payload = outfile.read().encode("UTF-8")
        response = client_secret_manager.add_secret_version(request={"parent": parent, "payload": {"data": payload}})
        if response.state == response.State.ENABLED:
            return 'Settings.toml file was updated under GCP Secret Manager'
        else:
            return 'May have been an issue updating Settings.toml file under GCP Secret Manager'

if __name__ == "__main__":
    method = sys.argv[1]
    file = sys.argv[2]
    secret_name = sys.argv[3]
    project_number = sys.argv[4]
    if str(method) == 'download' and file and secret_name and project_number:
        download(str(file), str(secret_name), str(project_number))
    elif str(method) == 'upload' and file and secret_name and project_number:
        upload(str(file), str(secret_name), str(project_number))


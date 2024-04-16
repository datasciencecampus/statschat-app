gcloud config set project statschat
gcloud auth application-default login

cd flask-app

gcloud builds submit --tag europe-west2-docker.pkg.dev/statschat/statschat-docker-repo/statschat-app-image:<date> .
gcloud run deploy statschat --image europe-west2-docker.pkg.dev/statschat/statschat-docker-repo/statschat-app-image:<date> --min-instances=0 --max-instances=10 --region=europe-west2 --allow-unauthenticated --memory=1G --cpu=1

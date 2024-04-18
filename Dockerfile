# Set base image (this loads the Debian Linux operating system)
FROM python:3.10.4-buster
ENV PYTHONUNBUFFERED True

WORKDIR /Statschat

# copy subset of files as specified by dockerignore
COPY . ./
RUN mv notebooks/load_llm_models_docker.py ./load_llm_models_docker.py

RUN python -m pip install --upgrade pip
RUN python -m pip install ".[backend]"

RUN python load_llm_models_docker.py

EXPOSE 8080
CMD ["uvicorn", "fast-api.main_api:app", "--host", "0.0.0.0", "--port", "8080"]

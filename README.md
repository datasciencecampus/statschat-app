<img src="https://github.com/datasciencecampus/awesome-campus/blob/master/ons_dsc_logo.png">

# `StatsChat`
[![Stability](https://img.shields.io/badge/stability-experimental-orange.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#experimental)
[![Twitter](https://img.shields.io/twitter/url?label=Follow%20%40DataSciCampus&style=social&url=https%3A%2F%2Ftwitter.com%2FDataSciCampus)](https://twitter.com/DataSciCampus)
[![Shared under the MIT License](https://img.shields.io/badge/license-MIT-green)](https://github.com/datasciencecampus/Statschat/blob/main/LICENSE)
[![Mac-OS compatible](https://shields.io/badge/MacOS--9cf?logo=Apple&style=social)]()

## Code state

> [!WARNING]
> Please be aware that for development purposes, these experiments use
> experimental Large Language Models (LLM's) not intended for production. They
> can present inaccurate information, hallucinated statements and offensive
> text by random chance or through malevolent prompts.

- **Under development** / **Experimental**
- **Tested on macOS only**
- **Peer-reviewed**
- **Depends on external API's**

## Introduction

This is an experimental application for semantic search of ONS statistical
publications. It uses LangChain to implement a fairly simple Retriaval Augmented Generation (RAG) using embedding search
and QA information retrieval process.

Upon receiving a query, documents are
returned as search results using embedding similarity to score relevance. Next, the relevant text is passed to a Large Language
Model (LLM), which is prompted to write an answer to the original question, if it can, using only the information contained within the documents.

For this prototype, relevant web pages are
scraped and the data stored in `data/bulletins`, the docstore / embedding store
that is created is likewise in local folders and files, and the LLM is either run in memory or accessed through VertexAI.

## Installation

The project requires specific versions of some packages so it is recommended to
set up a virtual environment.  Using venv and pip:

```shell
python3.10 -m venv env
source env/bin/activate

python -m pip install --upgrade pip
python -m pip install .
```

> [!NOTE]
> If you are doing development work on `statschat`, you should install the
> package locally as editable with our optional `dev` dependencies:
> ```shell
> python -m pip install -e ".[dev]"
> ```

### Pre-commit actions

This repository contains a configuration of pre-commit hooks. These are
language agnostic and focussed on repository security (such as detection of
passwords and API keys).

If approaching this project as a developer, you are encouraged to install and
enable `pre-commits` by running the following in your shell:
1. Install `pre-commit`:
   ```shell
   pip install pre-commit
   ```
2. Enable `pre-commit`:
   ```shell
   pre-commit install
   ```

Once pre-commits are activated, whenever you commit to this repository a series of checks will be executed. The use of active
pre-commits are highly encouraged.

> [!NOTE]
> Pre-commit hooks execute Python, so it expects a working Python build.

## Usage

This main module statschat can be either called directly or deployed as an API (using fastapi).
A lightweight flask front end is implemented separately in a subfolder and relies on the API running.

The first time you instantiate the `Inquirer` class, any ML models specified in the code will be
downloaded to your machine. This will use a few GB of data and take a few
minutes. App and search pipeline parameter are stored and can be updated by
editing `statschat/_config/main.toml`.

We have included few EXAMPLE scraped data files in `data/bulletins` so that
the preprocessing and app can be run as a small example system without waiting
on webscraping.

### With Vertex AI

If you wish to use Google's model API update the model variables in
`statschat/_config/main.toml`:
* to use the question-answering system with Google's PaLM2 API set the
  `generative_model_name` parameter to `text-unicorn` or `gemini-pro` (their
  name for the model).
* for PaLM2 (Gecko) to create embeddings, set the `embedding_model_name`
  parameter to `textembedding-gecko@001`. You may also wish to disable the
  removal of near-identical documents in the preprocessing pipeline (line 59,
  `statschat/embedding/preprocess.py`), to reduce calls to the embedding API.

In addition to changing this parameter, you will need a Google Cloud Platform
(GCP) project set up, with the Vertex AI API enabled. You will need to have the
GCP Command Line Interface installed in the machine running this code, logged
in to an account with sufficient permissions to access the API (you may need to
set up [application default credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc#how-to)).
Usually this can be achieved by running:
```shell
gcloud config set project "<PROJECT_ID>"
gcloud auth application-default login
```

## Example endpoint commands

1. #### Webscraping the source documents (not included in the public repository, only examples in `data/bulletins`)

    ```shell
    python statschat/webscraping/main.py
    ```

2. #### Creating a local document store

    ```shell
    python statschat/embedding/preprocess.py
    ```

3. #### Updating an existing local document store with new articles

    ```shell
    python statschat/embedding/preprocess_update_db.py
    ```

4. #### Run the interactive Statschat API

    ```shell
    uvicorn fast-api.main_api:app
    ```

    The fastapi is set to respond to http requests on port 8000. When running, you can see docs at http://localhost:8000/docs.

5. #### Run the flask web interface

    ```shell
    python flask-app/app.py
    ```
    To use the user UI
    navigate in your browser to http://localhost:5000. Note that it requires the API to be running and the endpoind specified in the app.

6. #### Run the search evaluation pipeline
    ```shell
    python statschat/model_evaluation/evaluation.py
    ```
    The StatsChat pipeline is currently evaluated based on small number of test
    question. The main 'app_config.toml' determines pipeline setting used in
    evaluation and results are written to `data/model_evaluation` folder.


7. #### Testing
    ```shell
    python -m pytest
    ```
    Preferred unittesting framework is PyTest.

### Search engine parameters

There are some key parameters in `statschat/_config/main.toml` that we're
experimenting with to improve the search results, and the generated text
answer.  The current values are initial guesses:

| Parameter | Current Value | Function |
| --- | --- | --- |
| k_docs | 10 | Maximum number of search results to return |
| similarity_threshold | 2.0 | Cosine distance, a searched document is only returned if it is at least this similar (EQUAL or LOWER) |
| k_contexts | 3 | Number of top documents to pass to generative QA LLM |


# Data Science Campus

At the [Data Science Campus](https://datasciencecampus.ons.gov.uk/about-us/) we
apply data science, and build skills, for public good across the UK and
internationally. Get in touch with the Campus at
[datasciencecampus@ons.gov.uk](datasciencecampus@ons.gov.uk).

# License

<!-- Unless stated otherwise, the codebase is released under [the MIT Licence][mit]. -->

The code, unless otherwise stated, is released under [the MIT License][mit].

The documentation for this work is subject to [© Crown copyright][copyright]
and is available under the terms of the [Open Government 3.0][ogl] licence.

[mit]: LICENSE
[copyright]: http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/
[ogl]: http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/

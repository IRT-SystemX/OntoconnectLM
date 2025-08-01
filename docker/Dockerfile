FROM python:3.10

LABEL project="SMD"
LABEL version="1.0"
LABEL description="This is a dockerfile for SMD"

RUN apt-get update && apt-get install -y \
    vim \
    wget \
    curl \
    less

COPY ./requirements.txt ./
COPY ./streamlit/.streamlit/config.toml /root/.streamlit/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download fr_core_news_lg && python -m spacy download fr_core_news_sm

# EXPOSE 8501

RUN echo "alias ll='ls -lah --color=auto'" >> ~/.bashrc
CMD ["streamlit", "run", "/ontoconnectlm/app.py", "--server.address=0.0.0.0"]

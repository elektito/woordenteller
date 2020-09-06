FROM python:3.8

RUN apt-get update && apt-get install -y \
    libfrog-dev \
    frog \
    frogdata \
    libfolia-dev \
    libicu-dev \
    libxml2-dev \
    libticcutils-dev \
    libucto-dev \
    libtimbl-dev
RUN pip install cython gunicorn

# copy requirementst.txt and install dependencies before copying
# everything else, so that dependency installation is only triggered
# when the requirements.txt is changed and not when any of the other
# input files change.
COPY requirements.txt /opt/woordteller/
WORKDIR /opt/woordteller
RUN pip install -r requirements.txt

COPY . /opt/woordteller

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]

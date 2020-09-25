FROM elektito/frog:0.21

RUN apt-get update && apt-get install -y python3-pip git

RUN pip3 install cython gunicorn

# copy requirementst.txt and install dependencies before copying
# everything else, so that dependency installation is only triggered
# when the requirements.txt is changed and not when any of the other
# input files change.
COPY requirements.txt /opt/woordenteller/
WORKDIR /opt/woordenteller
RUN pip3 install -r requirements.txt

COPY . /opt/woordenteller

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]

FROM python:3.7

ADD barbora_bot.py /

RUN pip install requests

CMD [ "python", "./barbora_bot.py", "--email", "", "--password", "", "--botapikey", "", "--botchatid", "" ]

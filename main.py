import base64
import argparse

# word cloud
from os import path
from scipy import misc

from wordcloud import WordCloud, STOPWORDS

# Google auth and storing gmail information
import httplib2

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

message_file = open('messages.txt', 'w')

CLIENT_SECRET_FILE = 'client_secret.json'
OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'
STORAGE = Storage('gmail.storage')
GMAIL_SERVICE = ''


def logon():
    global GMAIL_SERVICE
    flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
    http = httplib2.Http()
    credentials = STORAGE.get()
    if credentials is None or credentials.invalid:
        credentials = run(flow, STORAGE, http=http)
    http = credentials.authorize(http)
    GMAIL_SERVICE = build('gmail', 'v1', http=http)


def get_all_threads(query):
    threads = GMAIL_SERVICE.users().threads().list(userId='me',
                                                   q=query).execute()
    total = 0
    if threads['threads']:
        for thread in threads['threads']:
            total += get_thread(thread['id'])
            print "Fetched {} threads".format(total)


def get_thread(threadId):
    thread = GMAIL_SERVICE.users().threads().get(userId='me',
                                                    id=threadId).execute()
    if thread['messages']:
        for message in thread['messages']:
            if message['payload']['mimeType'] == 'text/plain':
                try:
                    message_body = base64.urlsafe_b64decode(message['payload']['body']['data']
                                                                .encode("utf-8"))
                    message_file.writelines(
                        [line + '\n' for line in message_body.lower().splitlines()])
                except KeyError as e:
                    print "ERROR", e
                    pprint.pprint(message['payload']['body']['data'])
                except TypeError as e:
                    print "TYPEERROR", e, message['payload']['body']['data']
        return len(thread['messages'])


def generate_cloud():
    d = path.dirname(__file__)
    janice = open(path.join(d, 'messages.txt')).read()
    group_mask = misc.imread(path.join(d, "mask.png"), flatten=True)
    wc = WordCloud(background_color="white", max_words = 2000, mask=group_mask)
    wc.generate(text)
    wc.to_file(path.join(d, "masked.jpg"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('query', help='Query to build word cloud from.')

    args = parser.parse_args()
    print "logging in"
    logon()
    print "getting all threads"
    get_all_threads(args.query)
    print "finished, closing files"
    message_file.close()
    print "Generating cloud."
    generate_cloud()


if __name__ == "__main__":
    main()

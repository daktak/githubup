#!/usr/bin/env python3
import os,sys
import urllib
import json
import smtplib
import configparser
import shlex
import subprocess
from urllib import request
import csv
try:
    confFile = sys.argv[1]
except :
    confFile = '/etc/githubup/githubup.ini'


def getList(st):
	my_splitter = shlex.shlex(st, posix=True)
	my_splitter.whitespace += ','
	my_splitter.whitespace_split = True
	return list(my_splitter)

config = configparser.ConfigParser()
config.read(confFile)

users = getList(config['Options']['owner'])
repos = getList(config['Options']['repo'])
dirprefix = config['Options']['dirprefix']
names = getList(config['Options']['name'])
branchs = getList(config ['Options']['branch'])
update_cmd = config['Options']['update_cmd']
commit_threshold = config['Options']['commit_threshold']
email_on = int(config['Notifications']['email'])
boxcar_on = int(config['Notifications']['boxcar'])
androidpn_on = int(config['Notifications']['androidpn'])
if email_on:
    email_always = int(config['Email']['email_always'])
    email_to = config['Email']['to']
    email_from = config['Email']['from']
    email_server = config['Email']['server']
    email_method = config['Email']['method']
    email_port = config['Email']['port']
    email_user = config['Email']['login']
    email_pass = config['Email']['pass']
email_subject = config['Email']['subject']
if boxcar_on:
    boxcar_token = config['Boxcar']['token']
if androidpn_on:
    androidpn_url = config['AndroidPN']['url']
    androidpn_broadcast = config['AndroidPN']['broadcast']
    androidpn_username = config['AndroidPN']['username']
output = '' 
i = -1 
triggered_notify = False 
LATEST_VERSION = None
COMMITS_BEHIND = 0

for repo in repos:
    i = i + 1
    dir = dirprefix+names[i]
    output = output+os.linesep
    new_update_cmd = update_cmd.replace('%name',names[i])
    new_update_cmd = new_update_cmd.replace('%repo',repo)
    new_update_cmd = new_update_cmd.replace('%owner',users[i])
    new_update_cmd = new_update_cmd.replace('%branch',branchs[i])

    version_file = os.path.join('%s' % dir, 'version.txt')

    fp = open(version_file, 'r')
    CURRENT_VERSION = fp.read().strip(' \n\r')
    fp.close()

    url = 'https://api.github.com/repos/%s/%s/commits/%s' % (users[i], repo, branchs[i])
    try:
    	result = urllib.request.urlopen(url).read()
    	git = json.loads(result.decode("utf8"))
    	LATEST_VERSION = git['sha']
    except:
        output = output+('Could not get the latest commit from github for %s' % names[i])+os.linesep
    if CURRENT_VERSION:
        if LATEST_VERSION:
        #print ( 'Comparing currently installed version with latest github version')
            url = 'https://api.github.com/repos/%s/%s/compare/%s...%s' % (users[i], repo, CURRENT_VERSION, LATEST_VERSION)
            try:
                result = urllib.request.urlopen(url).read()
                git = json.loads(result.decode("utf8"))
                COMMITS_BEHIND = git['total_commits']
            except: 
                output = output+( 'Could not get commits behind from github for %s' % names[i])+os.linesep
                COMMITS_BEHIND = 0
    
        if COMMITS_BEHIND >= 1:
            output = output+('New version of %s is available. You are %s commits behind' %( repo,COMMITS_BEHIND))+os.linesep
        elif COMMITS_BEHIND == 0:
            output = output+('%s is up to date' % names[i])+os.linesep
        elif COMMITS_BEHIND == -1:
            output = output+('You are running an unknown version of %s.' % names[i])+os.linesep

        if COMMITS_BEHIND >= int(commit_threshold):
            triggered_notify = True
            output = output+'Running update for '+names[i]+os.linesep
            output = output+subprocess.check_output(new_update_cmd, shell=True).decode("utf8")+os.linesep
    
    else:
        output = output+('You are running an unknown version of %s.' % names[i])+os.linesep

print ( output )
print ("Triggered: "+str(triggered_notify))
print ("Email: "+str(email_on))
if (email_on):
    print ("Email Always: "+str(email_always))
    if (email_always):
    	triggered_notify = True 
    if (triggered_notify):
        print ( 'Email being sent to %s' % email_to)
        body = ('From: %s' % email_from)+os.linesep+('To: %s' % email_to)+os.linesep+('Subject: %s' % email_subject)+os.linesep+os.linesep+output+os.linesep
        server=smtplib.SMTP(email_server,email_port)
        if email_method=='STARTTLS':
            server.ehlo()
            server.starttls()
        if not email_user=='':
            server.login(email_user,email_pass)
        server.sendmail(email_from,email_to,body)
        server.quit()
print ("Boxcar: "+str(boxcar_on))
if (boxcar_on):
  if (triggered_notify):
    try:
      print ('Notifying via boxcar')
      url = 'https://new.boxcar.io/api/notifications'
      data = urllib.parse.urlencode({
      'user_credentials': boxcar_token,
      'notification[title]': email_subject.encode('utf-8'),
      'notification[long_message]': output.replace(os.linesep, "<br />").encode('utf-8'),
      'notification[sound]': "done"
      })
      data = data.encode('utf-8')
      req = urllib.request.Request(url)
      handle = urllib.request.urlopen(req, data)
      handle.close()
    except  urllib.error.URLError as e:
      print ('Error sending Boxcar2 Notification: %s' % e)
print ("AndroidPN: "+str(androidpn_on))
if (androidpn_on):
    if (triggered_notify):
     try:
       print ('Notifying via AndroidPN')
       #curl --data "title=test&message=eu&action=send&broadcast=Y&uri=" http://192.168.1.10:7071/notification.do
       data = urllib.parse.urlencode({
       'title': email_subject.encode('utf-8'),
       'message': output.encode('utf-8'),
       'action': "send",
       'broadcast': androidpn_broadcast,
       'uri': "",
       'username': androidpn_username
       })
       data = data.encode('utf-8')
       req = urllib.request.Request(androidpn_url)
       handle = urllib.request.urlopen(req, data)
       handle.close()
     except  urllib.error.URLError as e:
      print ('Error sending Boxcar2 Notification: %s' % e)


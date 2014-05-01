#!/usr/bin/env python3
import os,sys
import urllib
import json
import smtplib
import configparser
import shlex
import subprocess
from urllib import request

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
email_on = config['Notifications']['email']
boxcar_on = config['Notifications']['boxcar']
if email_on:
    email_always = config['Email']['email_always']
    email_to = config['Email']['to']
    email_from = config['Email']['from']
    email_subject = config['Email']['subject']
    email_server = config['Email']['server']
if boxcar_on:
    boxcar_token = config['Boxcar']['token']
output = '' 
i = -1 
triggered_notify = 0
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
            triggered_notify = 1
            output = output+'Running update for '+names[i]+os.linesep
            output = output+subprocess.check_output(new_update_cmd, shell=True).decode("utf8")+os.linesep
    
    else:
        output = output+('You are running an unknown version of %s.' % names[i])+os.linesep

print ( output )
if email_on == 1:
    if email_always == 1:
    	triggered_notify = 1
    if triggered_notify:
    	print ( 'Email being sent to %s' % email_to)
    	body = ('From: %s' % email_from)+os.linesep+('To: %s' % email_to)+os.linesep+('Subject: %s' % email_subject)+os.linesep+os.linesep+output+os.linesep
    	server=smtplib.SMTP(email_server)
    	server.sendmail(email_from,email_to,body)
    	server.quit()

if boxcar_on == 1:
  if triggered_notify:
    try:
      url = 'https://new.boxcar.io/api/notifications'
      data = urllib.parse.urlencode({
      'user_credentials': boxcar_token,
      'notification[title]': email_subject.encode('utf-8'),
      'notification[long_message]': output.encode('utf-8'),
      'notification[sound]': "done"
      })
      data = data.encode('utf-8')
      req = urllib.request.Request(url)
      handle = urllib.request.urlopen(req, data)
      handle.close()
    except  urllib.error.URLError as e:
      print ('Error sending Boxcar2 Notification: %s' % e)

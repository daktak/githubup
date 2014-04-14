#!/usr/bin/env python2
import os
import urllib2
import json
import smtplib
import commands
from configobj import ConfigObj

try:
    confFile = sys.argv[2]
except :
    confFile = '/etc/githubup/githubup.ini'

config = ConfigObj(confFile)

users = config['Options']['owner']
repos = config['Options']['repo']
dirprefix = config['Options']['dirprefix']
names = config['Options']['name']
branchs = config ['Options']['branch'] 
update_cmd = config['Options']['update_cmd']
commit_threshold = config['Options']['commit_threshold']
email_on = config['Notifications']['email']
if email_on:
	email_always = config['Email']['email_always']
	email_to = config['Email']['to']
	email_from = config['Email']['from']
	email_subject = config['Email']['subject']
	email_server = config['Email']['server']
output = '' 
i = -1 
triggered_email = 0 
LATEST_VERSION = None


for repo in repos:
	i = i + 1
	dir = dirprefix+names[i]
	output = output+os.linesep
	new_update_cmd = update_cmd.replace('%name',names[i])
	new_update_cmd = new_update_cmd.replace('%repo',repo[i])
	new_update_cmd = new_update_cmd.replace('%owner',users[i])
	new_update_cmd = new_update_cmd.replace('%branch',branchs[i])

	version_file = os.path.join('%s' % dir, 'version.txt')

	fp = open(version_file, 'r')
	CURRENT_VERSION = fp.read().strip(' \n\r')
	fp.close()

	url = 'https://api.github.com/repos/%s/%s/commits/%s' % (users[i], repo, branchs[i])
	try:
		result = urllib2.urlopen(url).read()
		git = json.loads(result)
		LATEST_VERSION = git['sha']
	except:
		output = output+('Could not get the latest commit from github for %s' % names[i])+os.linesep
	if CURRENT_VERSION:
	  if LATEST_VERSION:
		#print ( 'Comparing currently installed version with latest github version')
		url = 'https://api.github.com/repos/%s/%s/compare/%s...%s' % (users[i], repo, CURRENT_VERSION, LATEST_VERSION)
		try:
			result = urllib2.urlopen(url).read()
			git = json.loads(result)
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
			triggered_email = 1
			output = output+'Running update for '+names[i]+os.linesep
			output = output+commands.getoutput(new_update_cmd)+os.linesep
	
	else:
		output = output+('You are running an unknown version of %s.' % names[i])+os.linesep

print ( output )
if email_on:
    if email_always == 1:
	triggered_email = 1
    if triggered_email:
	print ( 'Email being sent to %s' % email_to)
	body = ('From: %s' % email_from)+os.linesep+('To: %s' % email_to)+os.linesep+('Subject: %s' % email_subject)+os.linesep+os.linesep+output+os.linesep
	server=smtplib.SMTP(email_server)
	server.sendmail(email_from,email_to,body)
	server.quit()

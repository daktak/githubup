# githubup

Check version.txt from installed github projects and run an update if required


## Install
* copy githubup.ini /etc/githubup/
* copy githubup.py to /usr/local/bin 

Add to cron to run at specified interval

### Example for Gentoo webapps
```
[Options]
owner = ampache, 
repo = ampache,
dirprefix = /usr/share/webapps/ampache/99999/
name = htdocs
branch = master
update_cmd = emerge ampache && webapp-config -U -h localhost -d ampache ampache 99999
commit_threshold = 1
```
### Example for multiple projects with similar directory structure etc
```
[Options]
owner = midgetspy,rembo10,evilhero,DobyTang 
repo = sick-beard,headphones,mylar,lazylibrarian
dirprefix = /usr/share/
name = sickbeard,headphones,mylar,lazylibrarian
branch = master,master,master,master
update_cmd = emerge -1 --quiet-build=y %%name && /etc/init.d/%%name restart
commit_threshold = 1
```

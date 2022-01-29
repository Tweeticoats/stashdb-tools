# stashdb-tools

This is the start of bot tools to submit drafts to stashdb.org
This currently uses xbvr as the base database allowing you to take scenes and submit this as a draft to stashdb.org


# Running
Create a mysql database, and add a user with permission to use this database.
```
MariaDB [(none)]> create database xbvr;
MariaDB [(none)]>  GRANT ALL PRIVILEGES ON xbvr.* to 'xbvr'@'localhost' identified by 'password';
```
Start an instance of xbvr using this MariaDB database.

```
docker run -d  --name=xbvr --net=host --restart=always -e "DATABASE_URL=mysql://xbvr:xxxx@192.168.0.xx:3306/xbvr?charset=utf8mb4&parseTime=True&loc=Local"  --mount source=xbvr-config-2,target=/root/.config/ iamklh/xbvr:notofficial
```
Run the create table statements in db.sql


This tool uses environment variables to store credentials, please set these before running.

| Parameter                                     | Function |
|:----------------------------------------------| --- |
| DB_HOST=192.168.0.xxx  | MariaDB database host (localhost by default)
| DB_USER=xbvr           | MariaDB database user (xbvr by default)
| DB_PASS=xxxxx          | MariaDB database password (xbvr by default)
| DB_NAME=xbvr           | MariaDB database name (xbvr by default)
| API_KEY=               | stashdb.org api key
| XBVR_HOST=http://localhost:9999 | ip address and port for xbvr (used for image cache)


Match performers:
```
stashdbTools.py performer_match
```
Match studio:
```
stashdbTools.py studio_match
```
Match tags:
```
stashdbTools.py tags_match
```

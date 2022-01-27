#import sqlite3
import requests
import sys
import json
import re
import base64
import imghdr
import mimetypes
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os


import mysql.connector

class stashdbTools:
    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "Origin": "http://localhost:9998"
    }



    conn=None
    url='https://stashdb.org/graphql'

    def __init__(self,api_key,db_config):
#        self.conn = sqlite3.connect(dbname, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        print("connecting to db")
        self.conn = mysql.connector.connect(**db_config)

        self.headers["ApiKey"]=api_key

    def __del__(self):
        try:
            self.conn.close()
            print("closing db")
        except:
            print("error closing db")


    def __callGraphQL(self, query, variables=None):
        json = {}
        json['query'] = query
        if variables != None:
            json['variables'] = variables

        # handle cookies
        response = requests.post(self.url, json=json, headers=self.headers)

        if response.status_code == 200:
            result = response.json()
            if result.get("error", None):
                for error in result["error"]["errors"]:
                    raise Exception("GraphQL error: {}".format(error))
            if result.get("data", None):
                return result.get("data")
        else:
            raise Exception(
                "GraphQL query failed:{} - {}. Query: {}. Variables: {}".format(response.status_code, response.content,
                                                                                query, variables))
    def queryPerformer(self,id):
        query="""query findPerformer($id:ID!){
  findPerformer(id: $id){
    id
    name
    disambiguation
    aliases
    gender
    urls{
      type
      url
    }
    birthdate{
      date
      accuracy
    }
    age
    ethnicity
    country
    eye_color
    hair_color
    height
    measurements{
      cup_size
      band_size
      waist
      hip
    }
    breast_type
    career_start_year
    career_end_year
    tattoos{
      location
      description
    }
    piercings{
      location
      description
    }
    images{
      id
      url
      width
      height
    }
    deleted
  }
}
"""
        variables = {'id': id}
        result = self.__callGraphQL(query, variables)
        return result

    def queryPerformers(self,name,page=1,per=500):
        query="""query Performers($filter: QuerySpec, $performerFilter: PerformerFilterType) {
    queryPerformers(filter: $filter, performer_filter: $performerFilter) {
    count
    performers{
      id
      name
    }
  }
}"""
        variables = {
            "performerFilter": {"name":name},
            "filter":{"page":page,"per_page":per,"sort":"name","direction":"ASC"}
        }
        result = self.__callGraphQL(query, variables)



        return result

    def lookupStudio(self,id):
        query="""query Studio($id: ID!) {
  findStudio(id: $id) {
    id
    name
    child_studios {
      id
      name
      __typename
    }
    parent {
      id
      name
      __typename
    }
    urls {
      url
      type
      __typename
    }
    images {
      id
      url
      height
      width
      __typename
    }
    __typename
  }
}
"""
        variables = {'id': id}
        result = self.__callGraphQL(query, variables)
        return result

    def queryStudio(self,name,page=1,per_page=4,direction='DESC'):
        query="""query Studios($filter: QuerySpec, $studioFilter: StudioFilterType) {
  queryStudios(filter: $filter, studio_filter: $studioFilter) {
    count
    studios {
      id
      name
      parent {
        id
        name
        __typename
      }
      urls {
        url
        type
        __typename
      }
      images {
        id
        url
        height
        width
        __typename
      }
      __typename
    }
    __typename
  }
}"""
        variables = {
            "filter": {
                "page": page,
                "per_page": per_page,
                "direction": direction
            },
            "studioFilter": {"names":name}
        }
        result = self.__callGraphQL(query, variables)
        return result

    def createStudio(self,input):
        query="""mutation studioCreate($input: StudioCreateInput!) {
  studioCreate(input: $input) {
    id
    name
  }
}"""
        variables = {'input': input}
        result = self.__callGraphQL(query, variables)

    def queryTags(self, input):
        query = """query Tags($filter: QuerySpec, $tagFilter: TagFilterType) {
queryTags(filter: $filter, tag_filter: $tagFilter) {
count
tags {
  id
  name
  description
  __typename
}
__typename
}
}
"""
        variables = {"filter": {"direction": "ASC","page": 1, "per_page": 40, "sort": "name" }, "tagFilter": {"name": input} }
        result = self.__callGraphQL(query, variables)
        if "queryTags" in result:
            return result["queryTags"]["tags"]
        return None



    def createImage(self,image):
#        query="""mutation imageCreate($input: ImageCreateInput!) {
#  imageCreate(input: $input) {
#    id
#    url
#    width
#    height
#  }
#}"""
#        print("xx"+str(image))
#        variables = {'input': {'file':None}}
#        req = {}
#        req['query'] = query
#        req['variables'] = variables

#        query="""{"operationName": "AddImage", "variables": {"imageData": {"file": None}},
#         "query": "mutation AddImage($imageData: ImageCreateInput!) {\n  imageCreate(input: $imageData) {\n    id\n    url\n    width\n    height\n    __typename\n  }\n}\n"}"""
#

#        print(json.dumps(req))
#        response = requests.post(self.url, files=(('operations',(None,json.dumps(q)),('map',(None,'{"1":["variables.imageData.file"]}')),('1',(None,image))),headers=self.headers)
#        response = requests.post(self.url, files={'operations':query,'map':'{"1":["variables.imageData.file"]}','1':(None,image)},headers=self.headers)
#        print(response)
#        query={"operationName":"AddImage","variables":{"imageData":{"file":None}},"query":"mutation AddImage($imageData: ImageCreateInput!) {\n  imageCreate(input: $imageData) {\n    id\n    url\n    width\n    height\n    __typename\n  }\n}\n"}
        img_type = imghdr.what(None, h=image) or 'jpeg'
        mime = mimetypes.types_map.get('.' + img_type, 'image/jpeg')


        m = MultipartEncoder(fields={'operations':'{"operationName":"AddImage","variables":{"imageData":{"file":null}},"query":"mutation AddImage($imageData: ImageCreateInput!) {  imageCreate(input: $imageData) {id}}"}',
                                     'map':'{"1":["variables.imageData.file"]}',
                                     '1': ('1.jpg',image,mime)})

        headers_tmp = self.headers.copy()
        headers_tmp["Content-Type"] = m.content_type

        response = requests.post(self.url, data=m,headers=headers_tmp)
        return response.json()

    """
    mutation  submitSceneDraft($input: SceneDraftInput!) {
  submitSceneDraft(input: $input) {
    id
  }
}
{
  "input": {
    "title": "Picture Perfect",
    "details":"Webster's defines boudoir as a woman's dressing room, bedroom or private sitting room while photography is the process of producing images on a sensitized surface by the action of radiant energy. Put those two things together, add some silk pillows, and you've got yourself a wild photo session with Penny Pax! Be the lucky photographer as this busty ginger Hotwife poses for an Anniversary gift and a hole lot more!",
    "url":"https://www.milfvr.com/picture-perfect-5470569",
    "date":"2019-09-27",
    "studio":{
      "name":"Milfvr",
      "id":"38382977-9f5e-42fb-875b-2f4dd1272b11"
    },
    "performers": [{
      "name":"Penny Pax",
      "id":"a67371ea-2130-4d82-8d42-c9cfa847d4ae"
    }],
    "tags":null,
    "image": null,
    "fingerprints": []
  }
}"""
    def submitDraft(self,scene, image):
        
        
        query="""mutation  submitSceneDraft($input: SceneDraftInput!) {
  submitSceneDraft(input: $input) {
    id
  }
}"""
        img_type = imghdr.what(None, h=image) or 'jpeg'
        mime = mimetypes.types_map.get('.' + img_type, 'image/jpeg')


        m = MultipartEncoder(fields={'operations':'{"operationName":"AddImage","variables":{"imageData":{"file":null}},"query":"mutation AddImage($imageData: ImageCreateInput!) {  imageCreate(input: $imageData) {id}}"}',
                                     'map':'{"1":["variables.imageData.file"]}',
                                     '1': ('1.jpg',image,mime)})

        headers_tmp = self.headers.copy()
        headers_tmp["Content-Type"] = m.content_type

        response = requests.post(self.url, data=m,headers=headers_tmp)
        return response.json()

    def pendingEdits(self,type,id):
        query="""query PendingEditsCount($type: TargetTypeEnum!, $id: ID!) {  queryEdits(    edit_filter: {target_type: $type, target_id: $id, status: PENDING}    filter: {per_page: 1}  ) {    count    __typename  }}"""


        variables = {'id': id,'type':type}
        result = self.__callGraphQL(query, variables)
        if "queryEdits" in result:
            return result["queryEdits"]["count"]
        return -1

    def queryScenesByStudio(self,studio_id):
        query="""query Scenes($filter: QuerySpec, $sceneFilter: SceneFilterType) {
  queryScenes(filter: $filter, scene_filter: $sceneFilter) {
    count
    scenes {
      ...QuerySceneFragment
      __typename
    }
    __typename
  }
}
fragment QuerySceneFragment on Scene {
  id
  date
  title
  duration
  urls {
    ...URLFragment
    __typename
  }
  images {
    ...ImageFragment
    __typename
  }
  studio {
    id
    name
    __typename
  }
  performers {
    as
    performer {
      ...ScenePerformerFragment
      __typename
    }
    __typename
  }
  __typename
}
fragment URLFragment on URL {
  url
  site {
    id
    name
    icon
    __typename
  }
  __typename
}
fragment ImageFragment on Image {
  id
  url
  width
  height
  __typename
}
fragment ScenePerformerFragment on Performer {
  id
  name
  disambiguation
  deleted
  gender
  aliases
  __typename
}
"""

        variables={"filter": {"direction": "DESC","page": 1,"per_page": 20},"sceneFilter": {"parentStudio":studio_id}}
        result = self.__callGraphQL(query, variables)
        if "queryScenes" in result:
            return result["queryScenes"]["scenes"]
        return None


    def matchPerformers(self):
        c = self.conn.cursor()
        c.execute('select id,name from actors where id not in (select id from performer_stashdb);')
        rec=[]
        for row in c.fetchall():
            id= row[0]
            name=row[1]
            print(""+str(id)+" "+name)
            stashdbid=self.lookupPerformer(name)
            if stashdbid is not None:
                print("adding stash id: "+stashdbid+" for performer: "+name)
                c2=self.conn.cursor()
                c2.execute("insert into performer_stashdb (id,stash_id) values (%s,%s)",(id,stashdbid))
                self.conn.commit();

    def matchStudio(self):
        c = self.conn.cursor()
        c.execute('select id,name from sites where id not in (select id from sites_stashdb);    ')
        rec=[]
        for row in c.fetchall():
            id= row[0]
            name=row[1]
            print(""+str(id)+" "+name)

            stashdbid=self.lookupStudio(name)
            if stashdbid is not None:
                print("adding stash id: "+stashdbid+" for studio: "+name)
                c2=self.conn.cursor()
                c2.execute('insert into sites_stashdb(id,stash_id) values (%s,%s)',(id,stashdbid,))
                self.conn.commit();

    def matchTags(self):
        c = self.conn.cursor()
        c.execute('select id,name from tags where id not in (select id from tags_stashdb);')
        rec=[]
        for row in c.fetchall():
            id= row[0]
            name=row[1]
            print(""+str(id)+" "+name)

            tags=self.queryTags(name)
            if tags is not None:
                for t in tags:
                    if t["name"].lower()==name:
                        print("adding stash id: "+t['id']+" for Tag: "+name)
                        c2=self.conn.cursor()
                        c2.execute('insert into tags_stashdb(id,stash_id) values (%s,%s)',(id,t['id'],))
                        self.conn.commit();

    def matchScenes(self):
        c = self.conn.cursor()
        c.execute('select id,stash_id from sites_stashdb');
        for row in c.fetchall():
            studio_id=row[0]
            studio_stash_id=row[1]
            scenes=self.queryScenesByStudio(studio_stash_id)
            c1 = self.conn.cursor()
            c1.execute('select id,title,scene_url, studio from scenes where studio=%s',(studio_id,))
            for row in c2.fetchall():
                id= row[0]
                title=row[1]
                scene_url=row[2]
                print(""+str(id)+" "+title)
                for s in scenes:
                    if s['url']



    def lookupPerformer(self,name):
        res = self.queryPerformers(name)
        if "queryPerformers" in res:
            for p in res["queryPerformers"]["performers"]:
                if (p["name"]).lower() == name.lower():
                    return p["id"]
        return None

    def lookupStudio(self,name):
        res = self.queryStudio(name,per_page=60)
        if "queryStudios" in res:
            for p in res["queryStudios"]["studios"]:
                if (p["name"]).lower().replace(" ","") == name.lower().replace(" ",""):
                    return p["id"]

        r=re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', name)).split()
        name=" ".join(r)

        res = self.queryStudio(name,per_page=100)
        if "queryStudios" in res:
            for p in res["queryStudios"]["studios"]:
                if (p["name"]).lower().replace(" ","") == name.lower().replace(" ",""):
                    return p["id"]
        r=re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', name)).split()

        name=" ".join(r)
        name=name.replace("Bang","Bang!")


        res = self.queryStudio(name,per_page=100)
        if "queryStudios" in res:
            for p in res["queryStudios"]["studios"]:
                if (p["name"]).lower().replace(" ","") == name.lower().replace(" ",""):
                    return p["id"]

    def exportStudios(self):
        c = self.conn.cursor()
#        c.execute('select id,name,url,(select image from studios_image where studio_id=id) image from studios where id not in (select studio_id from studio_stash_ids) order by 1 asc;')
        c.execute('select id,name,url,(select image from studios_image where studio_id=id) image from studios;')
        for row in c.fetchall():

            id= row[0]
            name=row[1]
            urls=row[2]
            image=row[3]

            input={"name":name}
            if image is not None:
                print("creating image?")
                image_create=self.createImage(image)
                if "data" in image_create:
                    image_id=image_create["data"]["imageCreate"]["id"]
                    input["image_ids"]=[image_id]
            if urls is not None:
                input["urls"]= [{"url": urls, "type": "studio"}]
            self.createStudio(input)

    def exportPerformers(self):
        c=self.conn.cursor()
        c.execute('select id,name,gender,url, twitter,instagram,birthdate,ethnicity,country,eye_color,height,measurements,fake_tits,career_length,tattoos,piercings,aliases,details,death_date,hair_color,weight  from performers where id not in (select performer_id from performer_stash_ids where endpoint=?);',(self.url))
        for row in c.fetchall():
            id=row[0]
            name=row[1]
            gender=row[2]
            url=row[3]

if __name__ == '__main__':

    db_config = {
        'user': os.getenv('DB_USER', 'xbvr'),
        'password': os.getenv('DB_PASS', 'xbvr'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'xbvr'),
        'raise_on_warnings': True
    }

    api_key = os.getenv('API_KEY')
    if api_key is None:
        print("API_KEY needs to be defined")
        exit(1)

    tools = stashdbTools(api_key, db_config)
    if sys.argv[1] == "performer_match":
        tools.matchPerformers()
    elif sys.argv[1] == "studio_match":
        tools.matchStudio()
    elif sys.argv[1] == "tags_match":
        tools.matchTags()
    elif sys.argv[1]=="tmp":
        print("Pending edits: " +str(tools.pendingEdits('PERFORMER','c2b7cb03-dbea-4007-b0f4-49459154713c')))


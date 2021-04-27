import sqlite3
import requests
import sys
import json
import re


class stashdbTools:
    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "DNT": "1",
        "Origin": "https://stashdb.org"
    }



    conn=None
    url='https://stashdb.org/graphql'

    def __init__(self,api_key,dbname='stash-go.sqlite'):
        self.conn = sqlite3.connect(dbname, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.headers["ApiKey"]=api_key



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

    def loopPerformers(self):
        c = self.conn.cursor()
        c.execute('select id,name from performers where id not in (select performer_id from performer_stash_ids) order by 1 asc;')
        rec=[]
        for row in c.fetchall():
            id= row[0]
            name=row[1]
            print(""+str(id)+" "+name)
            stashdbid=self.lookupPerformer(name)
            if stashdbid is not None:
                print("adding stash id: "+stashdbid+" for performer: "+name)
                c2=self.conn.cursor()
                c2.execute("insert into performer_stash_ids(performer_id, endpoint, stash_id) values (?,?,?)",(id,self.url,stashdbid,))
                self.conn.commit();

    def loopStudio(self):
        c = self.conn.cursor()
        c.execute('select id,name from studios where id not in (select studio_id from studio_stash_ids) order by 1 asc;')
        rec=[]
        for row in c.fetchall():
            id= row[0]
            name=row[1]
            print(""+str(id)+" "+name)

            stashdbid=self.lookupStudio(name)
            if stashdbid is not None:
                print("adding stash id: "+stashdbid+" for studio: "+name)
                c2=self.conn.cursor()
                c2.execute('insert into studio_stash_ids(studio_id, endpoint, stash_id) values (?,?,?)',(id,self.url,stashdbid,))
                self.conn.commit();


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



if __name__ == '__main__':
    if len(sys.argv) > 2:
        if sys.argv[1] == "performer_match":
            tools=stashdbTools(sys.argv[2],'stash-go.sqlite')
            tools.loopPerformers()
        if sys.argv[1] == "studio_match":
            tools=stashdbTools(sys.argv[2],'stash-go.sqlite')
            tools.loopStudio()



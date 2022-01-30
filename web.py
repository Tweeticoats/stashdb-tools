from flask import Flask,jsonify,render_template,request,Response,redirect,session
import stashdbTools
import os

app = Flask(__name__)

app.secret_key = 'N46XYWbnaXG6JtdJZxez'

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

tools = stashdbTools.stashdbTools(api_key, db_config)

@app.route('/')
def root_url():
    print(db_config['user'])
    c=tools.conn.cursor()
    c.execute('select a.id,a.name,a.avatar_url,b.stash_id from sites as a left join sites_stashdb as b on a.id =b.id;')
    studios=[]
    for row in c.fetchall():
        data={}
        data['id'] = row[0]
        data['name'] = row[1]
        data['image'] = row[2]
        if row[2][:8] == 'https://':
            data['image'] = tools.xbvr_host + '/img/200x/https:/' + row[2][8:]
        data['stash_id'] = row[3]
        studios.append(data)
    tools.conn.commit()
    return render_template('index.html',studios=studios)


@app.route('/studio/<string:studio_id>')
def studio(studio_id):
    c=tools.conn.cursor()
    c.execute('select a.id,a.name,a.avatar_url,b.stash_id from sites as a left join sites_stashdb as b on a.id =b.id where a.id=%s;',(studio_id,))
    row=c.fetchone()
    if row:
        studio={}
        studio['id'] = row[0]
        studio['name'] = row[1]
        studio['image'] = row[2]
        studio['stash_id'] = row[3]

        tools.conn.commit()
        scenes=[]
        c.execute('select a.id,a.title, a.cover_url,a.scene_url,a.synopsis from scenes a left join scenes_stashdb as b on a.id=b.id where a.site=%s order by release_date',(studio_id,))
        scenes=[]
        for row in c.fetchall():
            data = {}
            data['id'] = row[0]
            data['title'] = row[1]
            data['image'] = row[2]
            if row[2][:8] == 'https://':
                data['image'] = tools.xbvr_host + '/img/200x/https:/' + row[2][8:]
            data['description'] = row[3]
            scenes.append(data)


        c.execute('select distinct actors.ID,actors.name from actors,scene_cast,scenes where actors.id=scene_cast.actor_id and scene_cast.scene_id=scenes.id and scenes.site=%s and actors.id not in (select id from performer_stashdb) order by actors.count desc;',(studio_id,))
        missing_performers=[]
        for row in c.fetchall():
            data = {}
            data['id'] = row[0]
            data['name'] = row[1]
            missing_performers.append(data)

        return render_template('studio.html',studio=studio,scenes=scenes,missing_performers=missing_performers)
    return 'ERROR'


@app.route('/scene/<int:scene_id>')
def scene(scene_id):
    scene = tools.query_db_scenes(scene_id)

    complete=tools.isComplete(scene)

    return render_template('scene.html', scene=scene,scene_id=scene_id,complete=complete)


@app.route('/scene_submit/<int:scene_id>')
def scene_submit(scene_id):
    scene = tools.query_db_scenes(scene_id)
    status = tools.submitDraft(scene)
    print(status)
    if 'data' in status:
        if 'submitSceneDraft' in status['data']:
            return redirect("https://stashdb.org/drafts/" + status['data']['submitSceneDraft']['id'], code=302)
        else:
           return jsonify(status)

@app.route('/actor/<int:actor_id>')
def actor(actor_id):
    c=tools.conn.cursor()
    c.execute('select a.id,a.created_at,a.updated_at,a.name,a.count,b.stash_id from actors a left join performer_stashdb as b on a.id=b.id where a.id=%s;',(actor_id,))
    row=c.fetchone()
    if row:
        actor={"id":row[0],"created_at":row[1],"updated_at":row[2],"name":row[3],"count":row[4],"stash_id":row[5]}
        c2=tools.conn.cursor()
        c2.execute('select scenes.site,scenes.title,scenes.id from scenes,scene_cast where scenes.id=scene_cast.scene_id and scene_cast.actor_id=%s order by scenes.site,title;',(actor_id,))
        scenes={}
        for row2 in c2.fetchall():
            if row2[0] in scenes:
                scenes[row2[0]].append({"title":row2[1],"id":row2[2]})
            else:
                scenes[row2[0]]=[{"title":row2[1],"id":row2[2]}]
        performers_list=tools.queryPerformers(row[3])

        return render_template('actor.html', actor=actor,performers_list=performers_list,scenes=scenes)
    return "No actor"

@app.route('/actor_update/<int:actor_id>')
def actor_update(actor_id):
    stash_id = request.args.get('stash_id',type=str)
    c=tools.conn.cursor()
    status=c.execute('insert into performer_stashdb(id,stash_id) values (%s,%s);',(actor_id,stash_id,))
    tools.conn.commit()
    return redirect("/actor/"+str(actor_id), code=302)




if __name__ == '__main__':

    app.run(host='0.0.0.0')

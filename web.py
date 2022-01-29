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

        return render_template('studio.html',studio=studio,scenes=scenes)
    return 'ERROR'


@app.route('/scene/<int:scene_id>')
def scene(scene_id):
    scene = tools.query_db_scenes(scene_id)
    return render_template('scene.html', scene=scene,scene_id=scene_id)


@app.route('/scene_submit/<int:scene_id>')
def scene_submit(scene_id):
    scene = tools.query_db_scenes(scene_id)
    status = tools.submitDraft(scene)
    print(status)
    if 'data' in status:
        return redirect("https://stashdb.org/drafts/" + status['data']['submitSceneDraft']['id'], code=302)


if __name__ == '__main__':

    app.run(host='0.0.0.0')

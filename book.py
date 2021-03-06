#coding=utf-8
from flask import Flask, request, render_template, jsonify, make_response, abort, send_from_directory
from flask.ext.httpauth import HTTPBasicAuth
#from itsdangerous import TimedJSONWebSignatureSerializer as TimedJSONWebSignatureSerializer
import MySQLdb
import redis
import geohash
import jwt
import json
import os
from werkzeug import secure_filename

#curl -i http://127.0.0.1:5000/book
#curl -i http://127.0.0.1:5000/book/1
#curl -i -H "Content-Type: application/json" -X POST -d '{"name":"mybook", "price":49.8, "author":"long", "publisher":"publisher", "publishnum":1, "pagenum":353, "wordnum":335000, "isbn":"9787539981697", "type":1}' http://127.0.0.1:5000/book
#curl -i -X DELETE http://127.0.0.1:5000/book/3
#curl -i -H "Content-Type: application/json" -X POST -d '{"userid":"123", "gpsx":39.92324, "gpsy":116.3906}' http://127.0.0.1:5000/gps
#curl -i -H "Content-Type: application/json" -X POST -d '{"gpsx":39.92324, "gpsy":116.3906}' http://127.0.0.1:5000/usernearby
#curl -i -H "Content-Type: application/json" -X POST -d '{"user":"abc", "pwd":"123"}' http://127.0.0.1:5000/login
#url --form "myfiles=@/media/sf_share/shudang/k.jpg" http://localhost:5000/upload

conn = MySQLdb.connect(host='localhost', user='root', passwd='0709', db='shudang', charset='utf8')
cur = conn.cursor()

r = redis.StrictRedis(host='127.0.0.1', port=6379)

app = Flask(__name__)
auth = HTTPBasicAuth()

@app.route('/', methods=['GET'])
def roots():
	cur.execute('select id,name,price,author,publisher,publishnum,pagenum,wordnum,isbn,type from sdbook')
	books = cur.fetchall()
	return jsonify({'books':books})

@app.route('/book', methods=['GET'])
#@auth.login_required
def getbooks():
	cur.execute('select id,name,price,author,publisher,publishnum,pagenum,wordnum,isbn,type from sdbook')
	results = cur.fetchall()
	books = []
	for row in results:
		book = {}
		book['id'] = row[0]
		book['Title'] = row[1]
		book['price'] = row[2]
		book['author'] = row[3]
		book['publisher'] = row[4]
		book['publishnum'] = row[5]
		book['pagenum'] = row[6]
		book['wordnum'] = row[7]
		book['isbn'] = row[8]
		book['type'] = row[9]
		books.append(book)
	return json.dumps(books);
	#return jsonify({'books':books})

@app.route('/book/<int:bookid>', methods=['GET'])
def getbook(bookid):
	cur.execute('select id,name,price,author,publisher,publishnum,pagenum,wordnum,isbn,type from sdbook')
	books = cur.fetchall()
	book = filter(lambda t: t[0] == bookid, books)
	if len(book) == 0:
		abort(404)
	return jsonify({'books':book})

@app.route('/book', methods=['POST'])
def postbook():
	if not request.json:
		abort(404)
	param = (request.json['name'], request.json['price'], request.json['author'], request.json['publisher'], request.json['publishnum'], request.json['pagenum'], request.json['wordnum'], request.json['isbn'], request.json['type'])
	sql = "insert into sdbook(name,price,author,publisher,publishnum,pagenum,wordnum,isbn,type)values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
	cur.execute(sql, param)
	conn.commit()
	cur.execute('select id,name,price,author,publisher,publishnum,pagenum,wordnum,isbn,type from sdbook')
	books = cur.fetchall()
	return jsonify({'books':books}), 201

@app.route('/book/<bookid>', methods=['DELETE'])
def deletebook(bookid):
	sql = "delete from sdbook where id = %s"
	cur.execute(sql, bookid)
	conn.commit()
	cur.execute('select id,name,price,author,publisher,publishnum,pagenum,wordnum,isbn,type from sdbook')
	books = cur.fetchall()
	return jsonify({'books':books}), 201

@app.route('/gps', methods=['GET'])
def getgpss():
	return jsonify({'gps':r.get('wx4g0ec19x3d')})

@app.route('/gps', methods=['POST'])
def postgps():
	if not request.json:
		abort(404)
	gpsx = request.json['gpsx']
	gpsy = request.json['gpsy']
	userid = request.json['userid']
	gpsdata = geohash.encode(gpsx, gpsy)
	key = gpsdata + "_" + userid
	r.set(key, gpsdata)
	return jsonify({'gps':r.get(key)})

@app.route('/usernearby', methods=['POST'])
def getusernearby():
	if not request.json:
		abort(404)
	gpsx = request.json['gpsx']
	gpsy = request.json['gpsy']
	gpsdata = geohash.encode(gpsx, gpsy)
	key = gpsdata[:5] + "*"
	nearbys = r.keys(key)
	return jsonify({'gps':nearbys})

@app.route('/login', methods=['POST'])
def login():
	if not request.json:
		abort(404)
	user = request.json['user']
	pwd = request.json['pwd']
	encoded = jwt.encode({user: 'payload'}, 'secret', algorithm='HS256')
	print jwt.decode(encoded, 'secret', algorithms=['HS256'])
	r.set(encoded, '1')
	return jsonify({'token':encoded})



app.config['UPLOAD_FOLDER'] = 'pic/'
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload', methods=['POST'])
def upload():
	uploaded_files = request.files.getlist("myfiles[]")
	print uploaded_files
	filenames = []
	for file in uploaded_files:
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
			filenames.append(filename)
	return jsonify({'return': 'OK'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@auth.verify_password
def verify_password(username_or_token, password):
	tokeninfo = r.keys(username_or_token)
	print tokeninfo
	if not tokeninfo:
		return False
	return True

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == "__main__":
	app.run(host='0.0.0.0', debug = True)

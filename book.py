#coding=utf-8
from flask import Flask, request, render_template, jsonify, make_response, abort
#from itsdangerous import TimedJSONWebSignatureSerializer as TimedJSONWebSignatureSerializer
import MySQLdb
import redis
import geohash

#curl -i http://127.0.0.1:5000/book
#curl -i http://127.0.0.1:5000/book/1
#curl -i -H "Content-Type: application/json" -X POST -d '{"name":"mybook", "price":49.8, "author":"long", "publisher":"publisher", "publishnum":1, "pagenum":353, "wordnum":335000, "isbn":"9787539981697", "type":1}' http://127.0.0.1:5000/book
#curl -i -X DELETE http://127.0.0.1:5000/book/3
#curl -i -H "Content-Type: application/json" -X POST -d '{"userid":"123", "gpsx":39.92324, "gpsy":116.3906}' http://127.0.0.1:5000/gps
#curl -i -H "Content-Type: application/json" -X POST -d '{"gpsx":39.92324, "gpsy":116.3906}' http://127.0.0.1:5000/usernearby

conn = MySQLdb.connect(host='localhost', user='root', passwd='0709', db='shudang', charset='utf8')
cur = conn.cursor()

r = redis.StrictRedis(host='127.0.0.1', port=6379)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def roots():
	cur.execute('select id,name,price,author,publisher,publishnum,pagenum,wordnum,isbn,type from sdbook')
	books = cur.fetchall()
	return jsonify({'books':books})

@app.route('/book', methods=['GET'])
def getbooks():
	cur.execute('select id,name,price,author,publisher,publishnum,pagenum,wordnum,isbn,type from sdbook')
	books = cur.fetchall()
	return jsonify({'books':books})

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
	return jsonify({'gps':r.get(gpsdata)})

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

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == "__main__":
	app.run(host='0.0.0.0', debug = True)

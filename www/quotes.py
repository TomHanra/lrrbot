import flask
import math
from www import server
from www import login
from common import utils

QUOTES_PER_PAGE = 25

@server.app.route('/quotes/')
@server.app.route('/quotes/<int:page>')
@login.with_session
@utils.with_postgres
def quotes(conn, cur, session, page=1):
	cur.execute("SELECT COUNT(*) FROM quotes WHERE NOT deleted")
	count, = next(cur)
	pages = (count - 1) // QUOTES_PER_PAGE + 1

	page = max(1, min(page, pages))

	cur.execute("""
		SELECT qid, quote, attrib_name, attrib_date
		FROM quotes
		WHERE NOT deleted
		ORDER BY qid DESC
		OFFSET %s
		LIMIT %s
	""", ((page-1) * QUOTES_PER_PAGE, QUOTES_PER_PAGE))

	return flask.render_template('quotes.html', session=session, quotes=list(cur), page=page, pages=pages)

@server.app.route('/quotes/search')
@login.with_session
@utils.with_postgres
def quote_search(conn, cur, session):
	query = flask.request.values["q"]
	page = int(flask.request.values.get("page", 1))
	cur.execute("""
		CREATE TEMP TABLE cse AS
		SELECT qid, quote, attrib_name, attrib_date
		FROM quotes
		WHERE
			TO_TSVECTOR('english', quote) @@ PLAINTO_TSQUERY('english', %s)
			AND NOT deleted
		ORDER BY qid DESC
	""", (query, ))
	pages = (cur.rowcount - 1) // QUOTES_PER_PAGE + 1
	page = max(1, min(page, pages))
	cur.execute("SELECT * FROM cse OFFSET %s LIMIT %s", ((page-1) * QUOTES_PER_PAGE, QUOTES_PER_PAGE))
	return flask.render_template('quotes.html', session=session, quotes=list(cur), page=page, pages=pages, args={'q': query})
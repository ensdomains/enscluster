import asyncio
import logging
from cloudant.client import CouchDB
from flask import Blueprint, Flask, request, render_template, g
from flask_graphql import GraphQLView
from google.cloud import logging as glogging
from graphql.execution.executors.asyncio import AsyncioExecutor
from werkzeug.serving import run_simple

import query
import query_backend


couchdb = CouchDB('admin', 'Z6Ce4SkQp6WmG2ufpv', url='http://35.210.124.52', connect=True)
loop = asyncio.get_event_loop()

class ViewWithBackend(GraphQLView):
    def get_context(self):
        return {'backend': query_backend.Backend(couchdb, loop)}

app = Flask(__name__)
app.add_url_rule('/graphql', view_func=ViewWithBackend.as_view('graphql', schema=query.schema, graphiql=True, executor=AsyncioExecutor()))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_simple('localhost', 8080, app, use_reloader=True)
else:
    logger = glogging.Client()
    logger.setup_logging(log_level=logging.INFO)

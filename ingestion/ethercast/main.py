import hmac
import logging
from cloudant import couchdb
from functools import wraps


COUCHDB_USER = 'importer'
COUCHDB_PASS = 'LbJtaJqsE9RmW7Ns8F'
COUCHDB_URL = 'http://35.241.55.221'
SIGNATURE_SECRET = '2a9f7f4a2deab1eb2569d6c33f312feee6b4b14c2028f05ed13c90037dced8be'
CONFIGS = {
    'registry': {
        'secret': '2a9f7f4a2deab1eb2569d6c33f312feee6b4b14c2028f05ed13c90037dced8be',
        'db': 'ens',
    },
    'addrChanged': {
        'secret': 'b41e28206dcb5514ad511803a8ba55bd5a1c7136d113295fffbf6d1a35baf82b',
        'db': 'resolvers',
    },
    'contentChanged': {
        'secret': '56d97ba530607745d297e040bef4b2fd516e42cee5430e9875997e1e20c62c5c',
        'db': 'resolvers',
    },
    'nameChanged': {
        'secret': '1a9fe52e544ffd526108f14fbd6d51d9ae7d062920a5b4f218bda8419e85cc4f',
        'db': 'resolvers',
    },
    'abiChanged': {
        'secret': '4672c2462ee34d30f34542809bae006bf4cc6cc932fe1378e44c759793a0ab94',
        'db': 'resolvers',
    },
    'pubkeyChanged': {
        'secret': '71ef604c2890ef2098233b2a65293f51f728d5e8fdc2bbdc63f9a4e02ebf1293',
        'db': 'resolvers',
    },
    'textChanged': {
        'secret': 'c5ef709aff19d08634b463856de892af5468e93f57bc95ad8f747819e9a2d79e',
        'db': 'resolvers',
    },
    'multihashChanged': {
        'secret': '2c671ba862edfe02e924efae6ead0bb86418f7825947db4de17dcedba4a7f7a3',
        'db': 'resolvers',
    },
}

def validate_signature(secret, request):
    sigs = dict(x.strip().split('=', 2) for x in request.headers['X-Ethercast-Signature'].split(';'))
    computed = hmac.new(secret.encode('utf-8'), request.data, 'sha512').hexdigest()
    return computed == sigs['sha512']


def ingest(request):
    with couchdb(COUCHDB_USER, COUCHDB_PASS, url=COUCHDB_URL) as client:
        config = CONFIGS[request.args.get('config', 'registry')]
        if not config:
            return 400, 'Unrecognised configuration'
        if not validate_signature(config['secret'], request):
            return 400, 'Invalid signature'
        db = client[config['db']]
        doc = request.get_json()
        doc['_id'] = '%s:%s' % (doc['blockHash'], int(doc['logIndex'], 16))
        doc['_deleted'] = doc['removed']
        del doc['removed']
        db.create_document(doc)

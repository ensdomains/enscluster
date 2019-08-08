import asyncio
import concurrent.futures
import json
import requests
from hexbytes import HexBytes
from itertools import islice
from aiodataloader import DataLoader


PREIMAGE_URL = 'https://preimagedb.appspot.com/sha256/query'
MIN_HASH = '0x0000000000000000000000000000000000000000000000000000000000000000'
MAX_HASH = '0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
DEFAULT_LIMIT = 10
MAX_LIMIT = 100

class Backend:
    def __init__(self, couchdb, loop):
        self.couchdb = couchdb
        self.loop = loop
        self.get_preimage = DataLoader(self.get_preimages, loop=loop)
        self.query_registry = DataLoader(self.batch_query_registry, loop=loop)
        self.get_parent_name = DataLoader(self.get_parent_names, loop=loop)

    async def get_parent_names(self, namehashes):
        db = self.couchdb['ens']
        results = db.get_view_result('_design/main', 'parentnodes', group=True, keys=namehashes).all()
        return [result['value'] for result in results]

    async def get_subdomains(self, namehash, limit=None, start=None):
        def func():
            db = self.couchdb['ens']
            startkey = (namehash, start or MIN_HASH)
            endkey = (namehash, MAX_HASH)
            result = db.get_view_result('_design/main', 'subnodes', reduce=True, limit=min(limit or DEFAULT_LIMIT, MAX_LIMIT), startkey=startkey, endkey=endkey, group=True).all()
            return [(row['key'][1], row['value']) for row in result]
        return await self.loop.run_in_executor(None, func)

    async def batch_query_registry(self, namehashes):
        db = self.couchdb['ens']
        results = db.get_view_result('_design/main', 'registry', group=True, keys=namehashes).all()
        def transform_result(result):
            ret = {'label': result.get('label')}
            ret.update((k, result[k][1]) for k in result if k != 'label')
            return ret
        return [transform_result(result['value']) for result in results]

    async def get_registry_events(self, namehash, limit=None, start=None):
        def func():
            db = self.couchdb['ens']
            startkey = (namehash,) + (start or ({},))
            endkey = (namehash, 0, 0)
            result = db.get_view_result('_design/main', 'events', limit=min(limit or DEFAULT_LIMIT, MAX_LIMIT), startkey=startkey, endkey=endkey, descending=True).all()
            return [row['value'] for row in result]
        return await self.loop.run_in_executor(None, func)

    async def get_resolver_events(self, address, namehash, limit=None, start=None):
        def func():
            db = self.couchdb['resolvers']
            startkey = (address, namehash) + (start or ({},))
            endkey = (address, namehash, 0, 0)
            result = db.get_view_result('_design/main', 'events', limit=min(limit or DEFAULT_LIMIT, MAX_LIMIT), startkey=startkey, endkey=endkey, descending=True).all()
            return [row['value'] for row in result]
        return await self.loop.run_in_executor(None, func)

    async def get_preimages(self, hashes):
        hashes = [hash[2:] if hash.startswith('0x') else hash for hash in hashes]
        response = requests.post(PREIMAGE_URL, headers={"Content-Type": "application/json"}, data=json.dumps(hashes))
        response.raise_for_status()
        result = [preimage or ("[%s]" % (hash,)) for hash, preimage in zip(hashes, response.json()['data'])]
        return result

    async def get_owned_names(self, address, limit=None, start=None):
        db = self.couchdb['ens']
        limit = min(limit or DEFAULT_LIMIT, MAX_LIMIT)
        startkey = (address, start or "")
        endkey = (address, {})
        result = iter(db.get_view_result('_design/main', 'owners', startkey=startkey, endkey=endkey))
        ret = []
        while len(ret) < limit:
            nodes = [node['key'][1] for node in islice(result, (limit - len(ret)) * 2)]
            if len(nodes) == 0:
                break
            infos = await self.query_registry.load_many(nodes)
            for node, info in zip(nodes, infos):
                if info['owner'] == address:
                    ret.append(node)
        return ret

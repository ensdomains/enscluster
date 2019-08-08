import argparse
import gzip
import json
import logging
import time
from cloudant.client import CouchDB
from itertools import islice, chain


parser = argparse.ArgumentParser(description="Tool to bulk load Ethereum events into a couchdb instance")
parser.add_argument('--couchdb', default="http://localhost:5984/")
parser.add_argument('--username', default="couchdb")
parser.add_argument('--password', default="couchdb")
parser.add_argument('--database', default='ethereum')
parser.add_argument('--batchsize', default=500)
parser.add_argument('files', nargs='+')
parser.add_argument('--gzipped', default=False, action='store_true')


def grouper(iterable, size):
    sourceiter = iter(iterable)
    while True:
        batchiter = islice(sourceiter, size)
        yield chain([next(batchiter)], batchiter)


class Loader:
    def __init__(self, db, batch_size, transform_func):
        self.db = db
        self.batch_size = batch_size
        self.transform_func = transform_func

    def load_file(self, fh):
        it = (self.transform_func(json.loads(line)) for line in fh)
        total = 0
        for batch in grouper(it, self.batch_size):
            batch = list(batch)
            self.db.bulk_docs(batch)
            total += len(batch)
            logging.info("Put %d docs (%d total)", len(batch), total)


REWRITES = {
    'log_index': 'logIndex',
    'transaction_hash': 'transactionHash',
    'transaction_index': 'transactionIndex',
    'block_timestamp': 'blockTimestamp',
    'block_number': 'blockNumber',
    'block_hash': 'blockHash',
}

def transform_log(log):
    log = {REWRITES.get(k, k): v for k, v in log.items()}
    log['_id'] = '%s:%d' % (log['blockHash'], int(log['logIndex']))
    return log


def main(args):
    client = CouchDB(args.username, args.password, url=args.couchdb, connect=True)
    db = client[args.database]
    loader = Loader(db, args.batchsize, transform_log)
    for filename in args.files:
        logging.info("Reading file '%s'", filename)
        if args.gzipped:
            fh = gzip.open(filename, 'r')
        else:
            fh = open(filename, 'r')
        loader.load_file(fh)
        fh.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main(parser.parse_args())

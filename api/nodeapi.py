#import asyncio
import logging
from collections import namedtuple
from flask import Blueprint, Flask, request, render_template, g
from flask_graphql import GraphQLView
from google.cloud import logging as glogging
#from graphql.execution.executors.asyncio import AsyncioExecutor
from web3 import Web3, HTTPProvider
from werkzeug.serving import run_simple
from graphql import (
    graphql,
    GraphQLArgument,
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLList,
    GraphQLString,
    GraphQLFloat,
    GraphQLInt,
    GraphQLBoolean
)
from graphql.type.scalars import (
    GraphQLScalarType,
    coerce_string,
    parse_string_literal
)


def get_blocks(hashes):
    return [web3.eth.getBlock(hash) for hash in hashes]


def get_transactions(hashes):
    return [web3.eth.getTransaction(hash) for hash in hashes]


def resolve_address(addr):
    if addr is None:
        return None
    return AccountTuple(addr)


def resolve_logs(root, info, **kwargs):
    logs = web3.eth.getLogs(kwargs)
    print(logs)
    return logs


def coerce_hash(hash):
    return hash.hex()


GraphQLHexBytes = GraphQLScalarType(name="HexBytes", serialize=coerce_hash, parse_value=coerce_string, parse_literal=parse_string_literal)

AccountTuple = namedtuple('Account', 'address')

Account = GraphQLObjectType(
    name='Account',
    fields=lambda:{
        "address": GraphQLField(GraphQLString),
        "balance": GraphQLField(GraphQLString, resolver=lambda root, info: web3.eth.getBalance(root.address)),
        "code": GraphQLField(GraphQLHexBytes, resolver=lambda root, info: web3.eth.getCode(root.address)),
        "nonce": GraphQLField(GraphQLInt, resolver=lambda root, info: web3.eth.getTransactionCount(root.address))
    }
)

Log = GraphQLObjectType(
    name='Log',
    fields=lambda:{
        "address": GraphQLField(Account, resolver=lambda root, info: resolve_address(root.address)),
        "topics": GraphQLField(GraphQLList(GraphQLHexBytes)),
        "data": GraphQLField(GraphQLString),
        "transactionHash": GraphQLField(GraphQLHexBytes),
        "transactionIndex": GraphQLField(GraphQLInt),
        "transaction": GraphQLField(Transaction, resolver=lambda root, info: web3.eth.getTransaction(root.transactionHash)),
        "blockNumber": GraphQLField(GraphQLInt),
        "blockHash": GraphQLField(GraphQLHexBytes),
        "block": GraphQLField(Block, resolver=lambda root, info: web3.eth.getBlock(root.blockHash)),
        "logIndex": GraphQLField(GraphQLInt),
        "removed": GraphQLField(GraphQLBoolean),
    }
)

TransactionReceipt = GraphQLObjectType(
    name='TransactionReceipt',
    fields=lambda:{
        "block": GraphQLField(Block, resolver=lambda root, info: web3.eth.getBlock(root.blockHash)),
        "blockHash": GraphQLField(GraphQLHexBytes),
        "blockNumber": GraphQLField(GraphQLInt),
        "contractAddress": GraphQLField(GraphQLString),
        "cumulativeGasUsed": GraphQLField(GraphQLInt),
        "from": GraphQLField(Account, resolver=lambda root, info: resolve_address(getattr(root, 'from'))),
        "to": GraphQLField(Account, resolver=lambda root, info: resolve_address(root.to)),
        "gasUsed": GraphQLField(GraphQLInt),
        "logs": GraphQLField(GraphQLList(Log)),
        "logsBloom": GraphQLField(GraphQLHexBytes),
        "status": GraphQLField(GraphQLInt),
        "transactionHash": GraphQLField(GraphQLString),
        "transactionIndex": GraphQLField(GraphQLInt),
        "transaction": GraphQLField(Transaction, resolver=lambda root, info: web3.eth.getTransaction(root.transactionHash)),
    }
)

Transaction = GraphQLObjectType(
    name='Transaction',
    fields=lambda:{
        "block": GraphQLField(Block, resolver=lambda root, info: web3.eth.getBlock(root.blockHash)),
        "blockHash": GraphQLField(GraphQLHexBytes),
        "blockNumber": GraphQLField(GraphQLInt),
        "from": GraphQLField(Account, resolver=lambda root, info: resolve_address(getattr(root, 'from'))),
        "to": GraphQLField(Account, resolver=lambda root, info: resolve_address(root.to)),
        "gas": GraphQLField(GraphQLInt),
        "gasPrice": GraphQLField(GraphQLInt),
        "hash": GraphQLField(GraphQLHexBytes),
        "input": GraphQLField(GraphQLString),
        "nonce": GraphQLField(GraphQLInt),
        "transactionIndex": GraphQLField(GraphQLInt),
        "value": GraphQLField(GraphQLString),
        "v": GraphQLField(GraphQLInt),
        "r": GraphQLField(GraphQLHexBytes),
        "s": GraphQLField(GraphQLHexBytes),
        "receipt": GraphQLField(TransactionReceipt, resolver=lambda root, info: web3.eth.getTransactionReceipt(root.hash)),
    }
)

Block = GraphQLObjectType(
    name='Block',
    fields=lambda:{
        "difficulty": GraphQLField(GraphQLFloat),
        "extraData": GraphQLField(GraphQLHexBytes),
        "gasLimit": GraphQLField(GraphQLInt),
        "gasUsed": GraphQLField(GraphQLInt),
        "hash": GraphQLField(GraphQLHexBytes),
        "logsBloom": GraphQLField(GraphQLHexBytes),
        "miner": GraphQLField(Account, resolver=lambda root, info: resolve_address(root.miner)),
        "mixHash": GraphQLField(GraphQLHexBytes),
        "nonce": GraphQLField(GraphQLHexBytes),
        "number": GraphQLField(GraphQLInt),
        "parentHash": GraphQLField(GraphQLHexBytes),
        "parent": GraphQLField(Block, resolver=lambda root, info: web3.eth.getBlock(root.parentHash)),
        "receiptsRoot": GraphQLField(GraphQLHexBytes),
        "sha3Uncles": GraphQLField(GraphQLHexBytes),
        "size": GraphQLField(GraphQLInt),
        "stateRoot": GraphQLField(GraphQLHexBytes),
        "timestamp": GraphQLField(GraphQLInt),
        "totalDifficulty": GraphQLField(GraphQLFloat),
        "transactions": GraphQLField(GraphQLList(Transaction), resolver=lambda root, info: get_transactions(root.transactions)),
        "transactionsRoot": GraphQLField(GraphQLHexBytes),
        "uncles": GraphQLField(GraphQLList(Block), resolver=lambda root, info: get_blocks(root.uncles)),
    }
)

schema = GraphQLSchema(
    query= GraphQLObjectType(
        name='Query',
        fields={
            'block': GraphQLField(
                Block,
                args={
                    "number": GraphQLArgument(type=GraphQLInt),
                    "hash": GraphQLArgument(type=GraphQLString)
                },
                resolver=lambda root, info, number=None, hash=None: web3.eth.getBlock(number or hash)
            ),
            'transaction': GraphQLField(
                Transaction,
                args={
                    "hash": GraphQLArgument(type=GraphQLString)
                },
                resolver=lambda root, info, hash: web3.eth.getTransaction(hash)
            ),
            'receipt': GraphQLField(
                TransactionReceipt,
                args={
                    "hash": GraphQLArgument(type=GraphQLString)
                },
                resolver=lambda root, info, hash: web3.eth.getTransactionReceipt(hash)
            ),
            'logs': GraphQLField(
                GraphQLList(Log),
                args={
                    "fromBlock": GraphQLArgument(type=GraphQLString),
                    "toBlock": GraphQLArgument(type=GraphQLString),
                    "address": GraphQLArgument(type=GraphQLString),
                    "topics": GraphQLArgument(type=GraphQLList(GraphQLString)),
                    "blockhash": GraphQLArgument(type=GraphQLString),
                },
                resolver=resolve_logs,
            )
        }
    )
)


web3 = Web3(HTTPProvider())
app = Flask(__name__)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True, context=web3))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_simple('localhost', 8080, app, use_reloader=True)
else:
    logger = glogging.Client()
    logger.setup_logging(log_level=logging.INFO)

function map(doc) {
    if(doc.topics.length == 0) return;

    var eventutils = require('views/lib/eventutils');
    var abi = eventutils.ABIs[doc.topics[0]];
    if(abi === undefined) return;
    var ev = eventutils.decodeEvent(abi, doc.data, doc.topics, false);
    var blockNumber = parseInt(doc.blockNumber);
    var key = [doc.address, ev.node];
    switch(abi.name) {
    case 'AddrChanged':
        emit(key, {addr: [blockNumber, ev.a]});
        break;
    case 'ContentChanged':
        emit(key, {content: [blockNumber, ev.hash]});
        break;
    case 'NameChanged':
        emit(key, {name: [blockNumber, ev.name]});
        break;
    case 'ABIChanged':
        emit(key, {abi: [ev.contentType]});
        break;
    case 'PubkeyChanged':
        emit(key, {pubkey: [blockNumber, ev.x, ev.y]});
        break;
    case 'TextChanged':
        emit(key, {text: [ev.key]});
        break;
    case 'MultihashChanged':
        emit(key, {multihash: [blockNumber, ev.hash]});
        break;
    }
}

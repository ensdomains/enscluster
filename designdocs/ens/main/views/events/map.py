function map(doc) {
    if(doc.topics.length == 0) return;
    if(doc.address != "0x314159265dd8dbb310642f98f50c066173c1259b") return;

    var eventutils = require('views/lib/eventutils');
    var abi = eventutils.ABIs[doc.topics[0]];
    if(abi === undefined) return;
    var ev = eventutils.decodeEvent(abi, doc.data, doc.topics, false);
    ev.blockNumber = parseInt(doc.blockNumber);
    ev.blockHash = doc.blockHash;
    ev.logIndex = parseInt(doc.logIndex);
    ev.transactionHash = doc.transactionHash;
    ev.transactionIndex = parseInt(doc.transactionIndex);
    ev.blockTimestamp = doc.blockTimestamp;
    if(ev._eventName == "NewOwner") {
        // Duplicate new owner events for subdomains too
        var subnode = eventutils.computeSubnode(ev.node, ev.label);
        emit([subnode, ev.blockNumber, ev.logIndex], ev);
    }
    emit([ev.node, ev.blockNumber, ev.logIndex], ev);
}

function map(doc) {
    if(doc.topics.length == 0) return;

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
    ev.address = doc.address;
    emit([ev.address, ev.node, ev.blockNumber, ev.logIndex], ev);
}

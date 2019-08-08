function map(doc) {
    if(doc.topics.length == 0) return;
    if(doc.address != "0x314159265dd8dbb310642f98f50c066173c1259b") return;

    var eventutils = require('views/lib/eventutils');
    var abi = eventutils.ABIs[doc.topics[0]];
    if(abi === undefined) return;
    var ev = eventutils.decodeEvent(abi, doc.data, doc.topics, false);
    switch(abi.name) {
    case 'Transfer':
        emit([ev.owner, ev.node], null);
        break;
    case 'NewOwner':
        var subnode = eventutils.computeSubnode(ev.node, ev.label);
        emit([ev.owner, subnode], null);
    }
}

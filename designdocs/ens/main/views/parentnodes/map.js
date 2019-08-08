function map(doc) {
    if(doc.topics.length == 0) return;
    if(doc.address != "0x314159265dd8dbb310642f98f50c066173c1259b") return;

    var eventutils = require('views/lib/eventutils');
    var abi = eventutils.ABIs[doc.topics[0]];
    if(abi === undefined || abi.name != 'NewOwner') return;
    var ev = eventutils.decodeEvent(abi, doc.data, doc.topics, false);
    emit(eventutils.computeSubnode(ev.node, ev.label), [ev.node, ev.label]);
}

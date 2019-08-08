function reduce(keys, values, rereduce) {
    function lastBlockReducer(a, b) {
        if(a === undefined || b[0] > a[0]) return b;
        return a;
    }

    function setUnionReducer(a, b) {
        if(a === undefined) return b;
        var ret = a.concat(b).sort();
        return ret.filter(function(value, i) { return ret.indexOf(value) == i; });
    }

    var subreducers = {
        addr: lastBlockReducer,
        content: lastBlockReducer,
        name: lastBlockReducer,
        abi: setUnionReducer,
        pubkey: lastBlockReducer,
        text: setUnionReducer,
        multihash: lastBlockReducer
    }

    var ret = {}
    for(var i = 0; i < values.length; i++) {
        var keys = Object.keys(values[i]);
        for(var j = 0; j < keys.length; j++) {
            ret[keys[j]] = subreducers[keys[j]](ret[keys[j]], values[i][keys[j]]);
        }
    }
    return ret;
}

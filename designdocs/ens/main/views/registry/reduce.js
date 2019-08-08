function reduce(keys, values, rereduce) {
    function lastBlockReducer(a, b) {
        if(a === undefined || b[0] > a[0]) return b;
        return a;
    }

    function anyValueReducer(a, b){
        return a || b;
    }

    var subreducers = {
        owner: lastBlockReducer,
        resolver: lastBlockReducer,
        ttl: lastBlockReducer,
        label: anyValueReducer
    }

    var ret = {}
    for(var i = 0; i < values.length; i++) {
        var value = values[i];
        var keys = Object.keys(value);
        for(var j = 0; j < keys.length; j++) {
            var key = keys[j];
            if(subreducers[key] !== undefined) {
                ret[key] = subreducers[key](ret[key], value[key]);
            }
        }
    }
    return ret;
}

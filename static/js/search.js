$(function() {
    var make_leaf = function(value) {
        var re = new RegExp(value, 'i');
        return {
            'type': 'leaf',
            'apply': function(pred) { return pred(re); }
        };
    };
    function backslash_count(s, end) {
        var count = 0;
        for (var i = end; i > 0; --i) {
            if (s[i - 1] != '\\') break;
            count += 1;
        }
        return count;
    }
    var tokenize = function(s) {
        var ops = [')', 'OR', 'AND', 'NOT', '('];
        function inner(s) {
            var tokens = [];
            var begin = 0;
            var od = '';
            while (begin != s.length) {
                var isop = false;
                for (i in ops) {
                    var op = ops[i];
                    if (s.substr(begin, op.length) == op) {
                        if (backslash_count(s, begin) % 2 == 0) {
                            if (od.length) {
                                tokens.push(od);
                                od = '';
                            }
                            tokens.push(op);
                            begin += op.length;
                            isop = true;
                            break;
                        }
                    }
                }
                if (!isop) {
                    od = od.concat(s[begin]);
                    begin += 1;
                }
            }
            if (od.length) {
                tokens.push(od);
            }
            return tokens;
        }
        function merge(tokens) {
            var result = [];
            $.each(tokens, function(i, token) {
                if (result.length && ops.indexOf(result[result.length - 1]) < 0 && ops.indexOf(token) < 0) {
                    result.push(result.pop() + token)
                } else {
                    result.push(token);
                }
            });
            return result;
        }
        function postprocess(tokens) {
            tokens = merge(tokens);
            var begin = -1;
            while (true) {
                begin = tokens.indexOf('(', begin + 1);
                if (begin < 0) return tokens;
                var end = tokens.indexOf(')', begin + 1);
                if (end < 0) return tokens;
                if (end - begin == 2 && ops.indexOf(tokens[begin + 1]) < 0) {
                    return postprocess(
                        tokens.slice(0, begin)
                        .concat([tokens.slice(begin, end + 1).join('')])
                        .concat(tokens.slice(end + 1, tokens.length))
                    );
                }
            }
        }
        return $.map(postprocess(inner(s)), $.trim);
    };

    var parse = function(s) {
        var unary = function(apply, od) {
            var arg = od.pop();
            od.push({
                'type': 'unary',
                'apply': function(pred) { return apply(arg.apply(pred)); }
            });
        };
        var binary = function(apply, od) {
            var rhs = od.pop();
            var lhs = od.pop();
            od.push({
                'type': 'binary',
                'apply': function(pred) { return apply(lhs.apply(pred), rhs.apply(pred)); }
            });
        };
        var ops = {
            '^': {
                'rank': 0,
                'pair': ['$']
            },
            '$': {
                'rank': 1,
                'pair': []
            },
            '(': {
                'lrank': 2,
                'rrank': 7,
                'pair': [')']
            },
            ')': {
                'rank': 3,
                'pair': []
            },
            'OR': {
                'rank': 4,
                'pair': [],
                'call': function(od) { binary(function(lhs, rhs) { return lhs || rhs; }, od); }
            },
            'AND': {
                'rank': 5,
                'pair': [],
                'call': function(od) { binary(function(lhs, rhs) { return lhs && rhs; }, od); }
            },
            'NOT': {
                'rank': 6,
                'pair': [],
                'call': function(od) { unary(function(arg) { return !arg; }, od); }
            }
        };
        var greater = function(lhs, rhs) {
            var lr = 'lrank' in lhs ? lhs.lrank : lhs.rank;
            var rr = 'rrank' in rhs ? rhs.rrank : rhs.rank;
            return lr > rr;
        };
        var op = [];
        var od = [make_leaf('')];
        op.push('^');
        try {
            $.each(tokenize(s).concat(['$']), function(i, token) {
                if (token in ops) {
                    var again = true;
                    while (again) {
                        if ($.inArray(token, ops[op[op.length - 1]].pair) >= 0) {
                            op.pop();
                            again = false;
                        } else if (greater(ops[op[op.length - 1]], ops[token])) {
                            ops[op.pop()].call(od);
                        } else {
                            op.push(token);
                            again = false;
                        }
                    }
                } else {
                    od.push(make_leaf(token));
                }
            });
        } catch(e) {
            return null;
        }
        if (op.length) return null;
        return od.pop();
    };

    $.ans = new Object();
    $('<ol/>').addClass('index').appendTo('article');
    $.getJSON('/whole.json', function(data) {
        $.ans.whole = data;
        $('#query').keypress(function(e) {
            if (e.which == 13) {
                var query = $('#query').val();
                var tree = parse(query);
                var ol = $('article > ol');
                ol.empty();
                if (tree) {
                    $.each($.ans.whole, function(index, post) {
                        if (tree.apply(function(re) { return re.test(post.title) || re.test(post.body) })) {
                            ol.append(
                                $('<li/>').append($('<h1/>').append($('<a/>', {
                                    'text': post.title,
                                    'href': post.route
                                }))).append($('<p/>').append($('<time/>', {
                                    'class': 'post-date',
                                    'datetime': post.date,
                                    'text': post.date
                                })))
                            );
                        }
                    });
                }
            }
        });
    });
});

from hashlib import md5
import sys
import types

PY3 = sys.version_info[0] == 3

if PY3: # pragma: no cover
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
    long = int
    def is_nonstr_iter(v):
        if isinstance(v, str):
            return False
        return hasattr(v, '__iter__')
else: # pragma no cover
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str
    long = long
    def is_nonstr_iter(v):
        return hasattr(v, '__iter__')

def bytes_(s, encoding='latin-1', errors='strict'):
    """ If ``s`` is an instance of ``text_type``, return
    ``s.encode(encoding, errors)``, otherwise return ``s``"""
    if isinstance(s, text_type): # pragma: no cover
        return s.encode(encoding, errors)
    return s


MAX_ORDER = 1 << 30
DEFAULT_PHASH = md5().hexdigest()

class Sentinel(object):
    def __init__(self, repr):
        self.repr = repr

    def __repr__(self):
        return self.repr

FIRST = Sentinel('FIRST')
LAST = Sentinel('LAST')

class SortingError(ValueError):
    pass

class CyclicDependencyError(ValueError):
    pass

class predvalseq(tuple):
    """ A subtype of tuple used to represent a sequence of predicate values """
    pass

class TopologicalSorter(object):
    """ A utility class which can be used to perform topological sorts against
    tuple-like data."""
    def __init__(
        self,
        default_before=LAST,
        default_after=None,
        first=FIRST,
        last=LAST,
        ):
        self.names = []
        self.req_before = set()
        self.req_after = set()
        self.name2before = {}
        self.name2after = {}
        self.name2val = {}
        self.order = []
        self.default_before = default_before
        self.default_after = default_after
        self.first = first
        self.last = last

    def remove(self, name):
        """ Remove a node from the sort input """
        self.names.remove(name)
        del self.name2val[name]
        after = self.name2after.pop(name, [])
        if after:
            self.req_after.remove(name)
            for u in after:
                self.order.remove((u, name))
        before = self.name2before.pop(name, [])
        if before:
            self.req_before.remove(name)
            for u in before:
                self.order.remove((name, u))

    def add(self, name, val, after=None, before=None):
        """ Add a node to the sort input.  The ``name`` should be a string or
        any other hashable object, the ``val`` should be the sortable (doesn't
        need to be hashable).  ``after`` and ``before`` represents the name of
        one of the other sortables (or a sequence of such named) or one of the
        special sentinel values :attr:`pyramid.util.FIRST`` or
        :attr:`pyramid.util.LAST` representing the first or last positions
        respectively.  ``FIRST`` and ``LAST`` can also be part of a sequence
        passed as ``before`` or ``after``.  A sortable should not be added
        after LAST or before FIRST.  An example::

           sorter = TopologicalSorter()
           sorter.add('a', {'a':1}, before=LAST, after='b')
           sorter.add('b', {'b':2}, before=LAST, after='c')
           sorter.add('c', {'c':3})

           sorter.sorted() # will be {'c':3}, {'b':2}, {'a':1}

        """
        if name in self.names:
            self.remove(name)
        self.names.append(name)
        self.name2val[name] = val
        if after is None and before is None:
            before = self.default_before
            after = self.default_after
        if after is not None:
            if not is_nonstr_iter(after):
                after = (after,)
            self.name2after[name] = after
            self.order += [(u, name) for u in after]
            self.req_after.add(name)
        if before is not None:
            if not is_nonstr_iter(before):
                before = (before,)
            self.name2before[name] = before
            self.order += [(name, o) for o in before]
            self.req_before.add(name)


    def sorted(self):
        """ Returns the sort input values in topologically sorted order"""
        order = [(self.first, self.last)]
        roots = []
        graph = {}
        names = [self.first, self.last]
        names.extend(self.names)

        for a, b in self.order:
            order.append((a, b))

        def add_node(node):
            if not node in graph:
                roots.append(node)
                graph[node] = [0] # 0 = number of arcs coming into this node

        def add_arc(fromnode, tonode):
            graph[fromnode].append(tonode)
            graph[tonode][0] += 1
            if tonode in roots:
                roots.remove(tonode)

        for name in names:
            add_node(name)

        has_before, has_after = set(), set()
        for a, b in order:
            if a in names and b in names: # deal with missing dependencies
                add_arc(a, b)
                has_before.add(a)
                has_after.add(b)

        if not self.req_before.issubset(has_before):
            raise SortingError(
                'Unsatisfied before dependencies: %s'
                % (', '.join(sorted(self.req_before - has_before)))
            )
        if not self.req_after.issubset(has_after):
            raise SortingError(
                'Unsatisfied after dependencies: %s'
                % (', '.join(sorted(self.req_after - has_after)))
            )

        sorted_names = []

        while roots:
            root = roots.pop(0)
            sorted_names.append(root)
            children = graph[root][1:]
            for child in children:
                arcs = graph[child][0]
                arcs -= 1
                graph[child][0] = arcs
                if arcs == 0:
                    roots.insert(0, child)
            del graph[root]

        if graph:
            # loop in input
            cycledeps = {}
            for k, v in graph.items():
                cycledeps[k] = v[1:]
            raise CyclicDependencyError(cycledeps)

        result = []

        for name in sorted_names:
            if name in self.names:
                result.append((name, self.name2val[name]))

        return result


class not_(object):
    """
    You can invert the meaning of any predicate value by wrapping it in a call
    to :class:`walkabout.not_`.

    .. code-block:: python
       :linenos:

       from walkabout import not_

       config.add_view(
           'mypackage.views.my_view',
           route_name='ok',
           request_method=not_('POST')
           )

    The above example will ensure that the view is called if the request method
    is *not* ``POST``, at least if no other view is more specific.

    This technique of wrapping a predicate value in ``not_`` can be used
    anywhere predicate values are accepted:

    - :meth:`pyramid.config.Configurator.add_view`

    - :meth:`pyramid.config.Configurator.add_route`

    - :meth:`pyramid.config.Configurator.add_subscriber`

    - :meth:`pyramid.view.view_config`

    - :meth:`pyramid.events.subscriber`

    .. versionadded:: 1.5
    """
    def __init__(self, value):
        self.value = value


class Notted(object):

    def __init__(self, predicate):
        self.predicate = predicate

    def _notted_text(self, val):
        # if the underlying predicate doesnt return a value, it's not really
        # a predicate, it's just something pretending to be a predicate,
        # so dont update the hash
        if val:
            val = '!' + val
        return val

    def text(self):
        return self._notted_text(self.predicate.text())

    def phash(self):
        return self._notted_text(self.predicate.phash())

    def __call__(self, *args):
        result = self.predicate(*args)
        phash = self.phash()
        if phash:
            result = not result
        return result


class PredicateList(object):

    def __init__(self):
        self.sorter = TopologicalSorter()
        self.last_added = None

    def add(self, name, factory, weighs_more_than=None, weighs_less_than=None):
        # Predicates should be added to a predicate list in (presumed)
        # computation expense order.
        ## if weighs_more_than is None and weighs_less_than is None:
        ##     weighs_more_than = self.last_added or FIRST
        ##     weighs_less_than = LAST
        self.last_added = name
        self.sorter.add(
            name,
            factory,
            after=weighs_more_than,
            before=weighs_less_than,
            )

    def make(self, api, **kw):
        # Given a configurator and a list of keywords, a predicate list is
        # computed.  Elsewhere in the code, we evaluate predicates using a
        # generator expression.  All predicates associated with a view or
        # route must evaluate true for the view or route to "match" during a
        # request.  The fastest predicate should be evaluated first, then the
        # next fastest, and so on, as if one returns false, the remainder of
        # the predicates won't need to be evaluated.
        #
        # While we compute predicates, we also compute a predicate hash (aka
        # phash) that can be used by a caller to identify identical predicate
        # lists.
        ordered = self.sorter.sorted()
        phash = md5()
        weights = []
        preds = []
        for n, (name, predicate_factory) in enumerate(ordered):
            vals = kw.pop(name, None)
            if vals is None: # XXX should this be a sentinel other than None?
                continue
            if not isinstance(vals, predvalseq):
                vals = (vals,)
            for val in vals:
                realval = val
                notted = False
                if isinstance(val, not_):
                    realval = val.value
                    notted = True
                pred = predicate_factory(realval, api)
                if notted:
                    pred = Notted(pred)
                hashes = pred.phash()
                if not is_nonstr_iter(hashes):
                    hashes = [hashes]
                for h in hashes:
                    phash.update(bytes_(h))
                weights.append(1 << n+1)
                preds.append(pred)
        if kw:
            raise SortingError('Unknown predicate values: %r' % (kw,))
        # A "order" is computed for the predicate list.  An order is
        # a scoring.
        #
        # Each predicate is associated with a weight value.  The weight of a
        # predicate symbolizes the relative potential "importance" of the
        # predicate to all other predicates.  A larger weight indicates
        # greater importance.
        #
        # All weights for a given predicate list are bitwise ORed together
        # to create a "score"; this score is then subtracted from
        # MAX_ORDER and divided by an integer representing the number of
        # predicates+1 to determine the order.
        #
        # For views, the order represents the ordering in which a "multiview"
        # ( a collection of views that share the same context/request/name
        # triad but differ in other ways via predicates) will attempt to call
        # its set of views.  Views with lower orders will be tried first.
        # The intent is to a) ensure that views with more predicates are
        # always evaluated before views with fewer predicates and b) to
        # ensure a stable call ordering of views that share the same number
        # of predicates.  Views which do not have any predicates get an order
        # of MAX_ORDER, meaning that they will be tried very last.
        score = 0
        for bit in weights:
            score = score | bit
        order = (MAX_ORDER - score) / (len(preds) + 1)
        return order, preds, phash.hexdigest()

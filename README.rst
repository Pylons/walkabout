``walkabout``
=============

This package extends the ``zope.interface`` component registry by
allowing multiple adapters to be regstered for the same specification
(``required``, ``provides``, ``name``).  Each adapter registered can
have one or more "predicates" associated with it:  at lookup time, the
first adapter whose predicate(s) match is returned.

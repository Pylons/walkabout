import unittest


class TestSentinel(unittest.TestCase):
    def test_repr(self):
        from . import Sentinel
        r = repr(Sentinel('ABC'))
        self.assertEqual(r, 'ABC')


class TestTopologicalSorter(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from . import TopologicalSorter
        return TopologicalSorter(*arg, **kw)

    def test_remove(self):
        inst = self._makeOne()
        inst.names.append('name')
        inst.name2val['name'] = 1
        inst.req_after.add('name')
        inst.req_before.add('name')
        inst.name2after['name'] = ('bob',)
        inst.name2before['name'] = ('fred',)
        inst.order.append(('bob', 'name'))
        inst.order.append(('name', 'fred'))
        inst.remove('name')
        self.assertFalse(inst.names)
        self.assertFalse(inst.req_before)
        self.assertFalse(inst.req_after)
        self.assertFalse(inst.name2before)
        self.assertFalse(inst.name2after)
        self.assertFalse(inst.name2val)
        self.assertFalse(inst.order)

    def test_add(self):
        from . import LAST
        sorter = self._makeOne()
        sorter.add('name', 'factory')
        self.assertEqual(sorter.names, ['name'])
        self.assertEqual(sorter.name2val,
                         {'name':'factory'})
        self.assertEqual(sorter.order, [('name', LAST)])
        sorter.add('name2', 'factory2')
        self.assertEqual(sorter.names, ['name',  'name2'])
        self.assertEqual(sorter.name2val,
                         {'name':'factory', 'name2':'factory2'})
        self.assertEqual(sorter.order,
                         [('name', LAST), ('name2', LAST)])
        sorter.add('name3', 'factory3', before='name2')
        self.assertEqual(sorter.names,
                         ['name',  'name2', 'name3'])
        self.assertEqual(sorter.name2val,
                         {'name':'factory', 'name2':'factory2',
                          'name3':'factory3'})
        self.assertEqual(sorter.order,
                         [('name', LAST), ('name2', LAST),
                          ('name3', 'name2')])

    def test_add_overwriting_existing(self):
        from . import LAST
        sorter = self._makeOne()
        sorter.add('name', 'factory1')
        sorter.add('name', 'factory2')
        self.assertEqual(sorter.name2val,
                         {'name':'factory2'})
        self.assertEqual(sorter.order, [('name', LAST)])

    def test_sorted_ordering_1(self):
        sorter = self._makeOne()
        sorter.add('name1', 'factory1')
        sorter.add('name2', 'factory2')
        self.assertEqual(sorter.sorted(),
                         [
                             ('name1', 'factory1'),
                             ('name2', 'factory2'),
                             ])

    def test_sorted_ordering_2(self):
        from . import FIRST
        sorter = self._makeOne()
        sorter.add('name1', 'factory1')
        sorter.add('name2', 'factory2', after=FIRST)
        self.assertEqual(sorter.sorted(),
                         [
                             ('name2', 'factory2'),
                             ('name1', 'factory1'),
                             ])

    def test_sorted_ordering_3(self):
        from . import FIRST
        sorter = self._makeOne()
        add = sorter.add
        add('auth', 'auth_factory', after='browserid')
        add('dbt', 'dbt_factory')
        add('retry', 'retry_factory', before='txnmgr', after='exceptionview')
        add('browserid', 'browserid_factory')
        add('txnmgr', 'txnmgr_factory', after='exceptionview')
        add('exceptionview', 'excview_factory', after=FIRST)
        self.assertEqual(sorter.sorted(),
                         [
                             ('exceptionview', 'excview_factory'),
                             ('retry', 'retry_factory'),
                             ('txnmgr', 'txnmgr_factory'),
                             ('dbt', 'dbt_factory'),
                             ('browserid', 'browserid_factory'),
                             ('auth', 'auth_factory'),
                             ])

    def test_sorted_ordering_4(self):
        from . import FIRST
        sorter = self._makeOne()
        add = sorter.add
        add('exceptionview', 'excview_factory', after=FIRST)
        add('auth', 'auth_factory', after='browserid')
        add('retry', 'retry_factory', before='txnmgr', after='exceptionview')
        add('browserid', 'browserid_factory')
        add('txnmgr', 'txnmgr_factory', after='exceptionview')
        add('dbt', 'dbt_factory')
        self.assertEqual(sorter.sorted(),
                         [
                             ('exceptionview', 'excview_factory'),
                             ('retry', 'retry_factory'),
                             ('txnmgr', 'txnmgr_factory'),
                             ('browserid', 'browserid_factory'),
                             ('auth', 'auth_factory'),
                             ('dbt', 'dbt_factory'),
                             ])

    def test_sorted_ordering_5(self):
        from . import LAST, FIRST
        sorter = self._makeOne()
        add = sorter.add
        add('exceptionview', 'excview_factory')
        add('auth', 'auth_factory', after=FIRST)
        add('retry', 'retry_factory', before='txnmgr', after='exceptionview')
        add('browserid', 'browserid_factory', after=FIRST)
        add('txnmgr', 'txnmgr_factory', after='exceptionview', before=LAST)
        add('dbt', 'dbt_factory')
        self.assertEqual(sorter.sorted(),
                         [
                             ('browserid', 'browserid_factory'),
                             ('auth', 'auth_factory'),
                             ('exceptionview', 'excview_factory'),
                             ('retry', 'retry_factory'),
                             ('txnmgr', 'txnmgr_factory'),
                             ('dbt', 'dbt_factory'),
                             ])

    def test_sorted_ordering_missing_before_partial(self):
        from . import SortingError
        sorter = self._makeOne()
        add = sorter.add
        add('dbt', 'dbt_factory')
        add('auth', 'auth_factory', after='browserid')
        add('retry', 'retry_factory', before='txnmgr', after='exceptionview')
        add('browserid', 'browserid_factory')
        self.assertRaises(SortingError, sorter.sorted)

    def test_sorted_ordering_missing_after_partial(self):
        from . import SortingError
        sorter = self._makeOne()
        add = sorter.add
        add('dbt', 'dbt_factory')
        add('auth', 'auth_factory', after='txnmgr')
        add('retry', 'retry_factory', before='dbt', after='exceptionview')
        add('browserid', 'browserid_factory')
        self.assertRaises(SortingError, sorter.sorted)

    def test_sorted_ordering_missing_before_and_after_partials(self):
        from . import SortingError
        sorter = self._makeOne()
        add = sorter.add
        add('dbt', 'dbt_factory')
        add('auth', 'auth_factory', after='browserid')
        add('retry', 'retry_factory', before='foo', after='txnmgr')
        add('browserid', 'browserid_factory')
        self.assertRaises(SortingError, sorter.sorted)

    def test_sorted_ordering_missing_before_partial_with_fallback(self):
        from . import LAST
        sorter = self._makeOne()
        add = sorter.add
        add('exceptionview', 'excview_factory', before=LAST)
        add('auth', 'auth_factory', after='browserid')
        add('retry', 'retry_factory', before=('txnmgr', LAST),
                                      after='exceptionview')
        add('browserid', 'browserid_factory')
        add('dbt', 'dbt_factory')
        self.assertEqual(sorter.sorted(),
                         [
                             ('exceptionview', 'excview_factory'),
                             ('retry', 'retry_factory'),
                             ('browserid', 'browserid_factory'),
                             ('auth', 'auth_factory'),
                             ('dbt', 'dbt_factory'),
                             ])

    def test_sorted_ordering_missing_after_partial_with_fallback(self):
        from . import FIRST
        sorter = self._makeOne()
        add = sorter.add
        add('exceptionview', 'excview_factory', after=FIRST)
        add('auth', 'auth_factory', after=('txnmgr','browserid'))
        add('retry', 'retry_factory', after='exceptionview')
        add('browserid', 'browserid_factory')
        add('dbt', 'dbt_factory')
        self.assertEqual(sorter.sorted(),
                         [
                             ('exceptionview', 'excview_factory'),
                             ('retry', 'retry_factory'),
                             ('browserid', 'browserid_factory'),
                             ('auth', 'auth_factory'),
                             ('dbt', 'dbt_factory'),
                             ])

    def test_sorted_ordering_with_partial_fallbacks(self):
        from . import LAST
        sorter = self._makeOne()
        add = sorter.add
        add('exceptionview', 'excview_factory', before=('wontbethere', LAST))
        add('retry', 'retry_factory', after='exceptionview')
        add('browserid', 'browserid_factory', before=('wont2', 'exceptionview'))
        self.assertEqual(sorter.sorted(),
                         [
                             ('browserid', 'browserid_factory'),
                             ('exceptionview', 'excview_factory'),
                             ('retry', 'retry_factory'),
                             ])

    def test_sorted_ordering_with_multiple_matching_fallbacks(self):
        from . import LAST
        sorter = self._makeOne()
        add = sorter.add
        add('exceptionview', 'excview_factory', before=LAST)
        add('retry', 'retry_factory', after='exceptionview')
        add('browserid', 'browserid_factory', before=('retry', 'exceptionview'))
        self.assertEqual(sorter.sorted(),
                         [
                             ('browserid', 'browserid_factory'),
                             ('exceptionview', 'excview_factory'),
                             ('retry', 'retry_factory'),
                             ])

    def test_sorted_ordering_with_missing_fallbacks(self):
        from . import SortingError
        from . import LAST
        sorter = self._makeOne()
        add = sorter.add
        add('exceptionview', 'excview_factory', before=LAST)
        add('retry', 'retry_factory', after='exceptionview')
        add('browserid', 'browserid_factory', before=('txnmgr', 'auth'))
        self.assertRaises(SortingError, sorter.sorted)

    def test_sorted_ordering_conflict_direct(self):
        from . import CyclicDependencyError
        sorter = self._makeOne()
        add = sorter.add
        add('browserid', 'browserid_factory')
        add('auth', 'auth_factory', before='browserid', after='browserid')
        self.assertRaises(CyclicDependencyError, sorter.sorted)

    def test_sorted_ordering_conflict_indirect(self):
        from . import CyclicDependencyError
        sorter = self._makeOne()
        add = sorter.add
        add('browserid', 'browserid_factory')
        add('auth', 'auth_factory', before='browserid')
        add('dbt', 'dbt_factory', after='browserid', before='auth')
        self.assertRaises(CyclicDependencyError, sorter.sorted)


class TestNotted(unittest.TestCase):

    def _makeOne(self, predicate):
        from . import Notted
        return Notted(predicate)

    def test_it_with_phash_val(self):
        pred = DummyPredicate('val', None)
        inst = self._makeOne(pred)
        self.assertEqual(inst.text(), '!val')
        self.assertEqual(inst.phash(), '!val')
        self.assertEqual(inst(None,), False)

    def test_it_without_phash_val(self):
        pred = DummyPredicate('', None)
        inst = self._makeOne(pred)
        self.assertEqual(inst.text(), '')
        self.assertEqual(inst.phash(), '')
        self.assertEqual(inst(None,), True)


class TestPredicateList(unittest.TestCase):

    def _makeOne(self):
        from . import PredicateList
        inst = PredicateList()
        for name, factory in (
            ('one', PredicateOne),
            ('two', PredicateTwo),
            ('three', PredicateThree),
            ):
            inst.add(name, factory)
        return inst

    def _callFUT(self, **kw):
        inst = self._makeOne()
        api = object()
        return inst.make(api, **kw)

    def test_ordering_same(self):
        order1, _, _ = self._callFUT(one=True, three=False)
        order2, _, _ = self._callFUT(one=True, three=True)
        self.assertTrue(order1 == order2)

    def test_ordering_same_count_importance(self):
        # two added before three, therefore three is more important
        order1, _, _ = self._callFUT(one=True, two=False)
        order2, _, _ = self._callFUT(one=True, three=True)
        self.assertTrue(order1 > order2)

    def test_ordering_higher_count(self):
        order1, _, _ = self._callFUT(one=True, three=False)
        order2, _, _ = self._callFUT(two=True)
        self.assertTrue(order1 < order2)

    def test_w_explicit_weights(self):
        from . import PredicateList
        inst = PredicateList()
        inst.add('one', PredicateOne)
        inst.add('two', PredicateTwo, after='one')
        inst.add('three', PredicateThree, after='two')
        order1, _, _ = inst.make(object(), one=True, two=False)
        order2, _, _ = inst.make(object(), one=True, three=True)
        self.assertTrue(order1 < order2)

    def test_notted(self):
        from . import not_
        _, predicates, _ = self._callFUT(
            one='ONE',
            two=not_('TWO'),
            three=not_('THREE'),
            )
        self.assertEqual(predicates[0].text(), 'one: ONE')
        self.assertEqual(predicates[1].text(),
                         "!two: TWO")
        self.assertEqual(predicates[2].text(), '!three: THREE')
        self.assertEqual(predicates[0](None,), False)
        self.assertEqual(predicates[1](None,), True)
        self.assertEqual(predicates[2](None,), True)

    def test_unknown_predictate(self):
        from . import SortingError
        self.assertRaises(SortingError,
                            self._callFUT,
                                one='ONE',
                                nonesuch='NONESUCH',
                                )


class PredicateDispatchTests(unittest.TestCase):

    def _getTargetClass(self):
        from . import PredicateDispatch
        return PredicateDispatch

    def _makeOne(self, name='name'):
        return self._getTargetClass()(name)

    def test_ctor_defaults(self):
        mv = self._makeOne()
        self.assertEqual(mv.candidates, [])

    def test___discriminator__(self):
        class Discriminating(object):
            def __discriminator__(self, *args):
                return 'Discriminating: %s' % ', '.join([str(x) for x in args])
        mv = self._makeOne()
        mv.add(Discriminating(), 100)
        self.assertEqual(mv.__discriminator__('a', 'b'),
                         'Discriminating: a, b')

    def test_add_one(self):
        mv = self._makeOne()
        mv.add('view', 100)
        self.assertEqual(mv.candidates, [(100, 'view', None)])

    def test_add_multiple(self):
        mv = self._makeOne()
        mv.add('view', 100)
        mv.add('view2', 99)
        mv.add('view3', 98)
        self.assertEqual(mv.candidates, [(98, 'view3', None),
                                         (99, 'view2', None),
                                         (100, 'view', None)])

    def test_add_with_phash(self):
        mv = self._makeOne()
        mv.add('view', 100, phash='abc')
        mv.add('view', 100, phash='abc')
        mv.add('view', 100, phash='def')
        mv.add('view', 100, phash='abc')
        self.assertEqual(mv.candidates, [(100, 'view', 'abc'),
                                         (100, 'view', 'def')])

    def test_add_with_phash_replacing(self):
        mv = self._makeOne()
        mv.add('view1', 100, phash='abc')
        mv.add('view2', 100, phash='abc')
        self.assertEqual(mv.candidates, [(100, 'view2', 'abc')])

    def test_multiple_with_functions_as_views(self):
        # this failed on py3 at one point, because functions aren't orderable
        # and we were sorting the views via a plain sort() rather than
        # sort(key=itemgetter(0)).
        def view1(request): pass
        def view2(request): pass
        mv = self._makeOne()
        mv.add(view1, 100, None)
        self.assertEqual(mv.candidates,
                        [(100, view1, None)])
        mv.add(view2, 100, None)
        self.assertEqual(mv.candidates,
                        [(100, view1, None),
                         (100, view2, None)])

    def test_match_wo___predicated__(self):
        candidate = object()
        mv = self._makeOne()
        mv.add(candidate, 100)
        self.assertTrue(mv.match({}, 'a', 'b') is candidate)

    def test_match_w_by_phash_miss(self):
        from . import PredicateMismatch
        candidate = object()
        mv = self._makeOne()
        mv.add(candidate, 100, 'abc')
        by_phash = {'abc': [lambda *args: ''.join(args) == 'abc']}
        self.assertRaises(PredicateMismatch, mv.match, by_phash, 'a', 'b')

    def test_match_w_by_phash_hit(self):
        candidate1 = object()
        candidate2 = object()
        by_phash = {'abc': [lambda *args: ''.join(args) == 'abc'],
                    'def': [lambda *args: True],
                   }
        mv = self._makeOne()
        mv.add(candidate1, 100, 'abc')
        mv.add(candidate2, 100, 'def')
        self.assertTrue(mv.match(by_phash, 'a', 'b') is candidate2)


class PredicateDomainTests(unittest.TestCase):

    def _getTargetClass(self):
        from . import PredicateDomain
        return PredicateDomain

    def _makeOne(self, target_interface, registry):
        return self._getTargetClass()(target_interface, registry)

    def test_class_conforms_to_IPredicateDomain(self):
        from zope.interface.verify import verifyClass
        from . import IPredicateDomain
        verifyClass(IPredicateDomain, self._getTargetClass())

    def test_instance_conforms_to_IPredicateDomain(self):
        from zope.interface import Interface
        from zope.interface.verify import verifyObject
        from . import IPredicateDomain
        class IFoo(Interface): pass
        verifyObject(IPredicateDomain, self._makeOne(IFoo, object()))

    def test_add_predicate(self):
        from zope.interface import Interface
        class IFoo(Interface): pass
        domain = self._makeOne(IFoo, object())
        domain.add_predicate('one', PredicateOne)
        domain.add_predicate('two', PredicateTwo, after='one')
        domain.add_predicate('three', PredicateThree, after='two')
        order1, _, _ = domain.predicates.make(object(), one=True, two=False)
        order2, _, _ = domain.predicates.make(object(), one=True, three=True)
        self.assertTrue(order1 < order2)

    def test_add_candidate_zero_args(self):
        from zope.interface import Interface
        from zope.interface.registry import Components
        class IFoo(Interface): pass
        registry = Components()
        candidate = object()
        domain = self._makeOne(IFoo, registry)
        domain.add_predicate('one', PredicateOne)
        self.assertRaises(TypeError, domain.add_candidate, candidate, one='ONE')

    def test_add_candidate_invalid_arg(self):
        from zope.interface import Interface
        from zope.interface.registry import Components
        class IFoo(Interface): pass
        registry = Components()
        candidate = object()
        domain = self._makeOne(IFoo, registry)
        domain.add_predicate('one', PredicateOne)
        self.assertRaises(ValueError,
                          domain.add_candidate, candidate, None, one='ONE')

    def test_add_candidate_class_arg(self):
        from zope.interface import Interface
        from zope.interface.registry import Components
        class IFoo(Interface): pass
        class Bar(object): pass
        registry = Components()
        candidate = object()
        domain = self._makeOne(IFoo, registry)
        domain.add_predicate('zero', DummyPredicate)
        domain.add_candidate(candidate, Bar, zero='ZERO')
        found = domain.lookup(Bar())
        self.assertTrue(found is candidate)

    def test_add_candidate(self):
        from zope.interface import Interface
        from zope.interface import implementer
        from zope.interface.registry import Components
        class IFoo(Interface): pass
        class IBar(Interface): pass
        @implementer(IBar)
        class Bar(object): pass
        registry = Components()
        candidate = object()
        domain = self._makeOne(IFoo, registry)
        domain.add_predicate('zero', DummyPredicate)
        domain.add_candidate(candidate, IBar, zero='ZERO')
        found = domain.lookup(Bar())
        self.assertTrue(found is candidate)

    def test_lookup_extra_kw(self):
        from zope.interface import Interface
        from zope.interface.registry import Components
        class IFoo(Interface): pass
        registry = Components()
        domain = self._makeOne(IFoo, registry)
        self.assertRaises(TypeError, domain.lookup, object(),
                            unknown='UNKNOWN')

    def test_lookup_miss(self):
        from zope.interface import Interface
        from zope.interface.registry import Components
        from . import PredicateMismatch
        class IFoo(Interface): pass
        registry = Components()
        domain = self._makeOne(IFoo, registry)
        self.assertRaises(PredicateMismatch, domain.lookup, object())

    def test_lookup_with_name(self):
        from zope.interface import Interface
        from zope.interface import implementer
        from zope.interface.registry import Components
        from . import PredicateMismatch
        class IFoo(Interface): pass
        class IBar(Interface): pass
        @implementer(IBar)
        class Bar(object): pass
        registry = Components()
        candidate = object()
        domain = self._makeOne(IFoo, registry)
        domain.add_predicate('zero', DummyPredicate)
        domain.add_candidate(candidate, IBar, name='named', zero='ZERO')
        self.assertRaises(PredicateMismatch, domain.lookup, Bar())
        found = domain.lookup(Bar(), name='named')
        self.assertTrue(found is candidate)

    def test_all(self):
        from zope.interface import Interface
        from zope.interface import implementer
        from zope.interface.registry import Components
        class IFoo(Interface): pass
        class IBar(Interface): pass
        @implementer(IBar)
        class Bar(object): pass
        registry = Components()
        candidate1 = object()
        candidate2 = object()
        domain = self._makeOne(IFoo, registry)
        domain.add_predicate('zero', DummyPredicate)
        domain.add_predicate('one', PredicateOne)
        domain.add_candidate(candidate1, IBar, name='name1', zero='ZERO')
        domain.add_candidate(candidate2, IBar, name='name2')
        domain.add_candidate(candidate2, IBar, name='name3', one='ONE')
        self.assertEqual(sorted(domain.all(Bar())),
                         [('name1', candidate1), ('name2', candidate2)])



class DummyPredicate(object):
    def __init__(self, val, api):
        self.val = val
    def __call__(self, subject):
        return True
    def phash(self):
        return self.val
    text = phash


class PredicateOne(object):
    def __init__(self, val, api):
        self.val = val
    def __call__(self, subject):
        return False
    def phash(self):
        return 'one: %s' % self.val
    text = phash

class PredicateTwo(object):
    def __init__(self, val, api):
        self.val = val
    def __call__(self, subject):
        return False
    def phash(self):
        return 'two: %s' % self.val
    text = phash

class PredicateThree(object):
    def __init__(self, val, api):
        self.val = val
    def __call__(self, subject):
        return False
    def phash(self):
        return 'three: %s' % self.val
    text = phash

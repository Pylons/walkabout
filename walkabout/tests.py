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
        inst.add('two', PredicateTwo, weighs_less_than='one')
        inst.add('three', PredicateThree, weighs_less_than='two')
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

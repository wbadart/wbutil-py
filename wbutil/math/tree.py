#!/usr/bin/env python3
'''
wbutil/math/tree.py

Classes for creating easy to use decision trees.

Will Badart <wbadart@live.com>
created: FEB 2018
'''

from csv import reader
from functools import lru_cache, partial
from math import log2 as lg
from operator import eq, ge, lt, itemgetter
from os import PathLike
from typing import Generator, Iterable, Tuple, Union
from uuid import uuid4

from graphviz import Digraph
from wbutil import compose

__all__ = [
    'DecisionTree',
]

_FeatureListT = Iterable[Union[str, Tuple[str, bool]]]
_PredicateT = compose[bool]


class DecisionTree(object):
    '''Represents a decision tree which branches based on information gain.'''

    # ==========
    # Public API
    # ==========

    def __init__(
            self,
            feature_names: _FeatureListT,
            *data: Iterable,
            test: _PredicateT=None,
            root_majority: str=None) -> None:
        '''
        Initialize the model.

        features:
            Ordered iterable of the feature names as strings. If an element
            of `features' is a 2-tuple, its first item is treated as the
            feature name and the second as a flag for continuous features (data
            in this column will be cast to float). The label/ target feature
            should occupy the last column.
        data:
            Each item in data should be an iterable of equal width to the
            feature list, with the last item holding the instance's label.
        test:
            Predicate to control which instances the tree claims for
            classification. Should not be set by user code.
        root_majority:
            Tracks which label was most common at the root node of the tree.
            Used to break ties at the leaves. If it is None (which it should be
            at the root node) it is computed to be the most frequent label.
        '''

        def ispair(feature):
            return type(feature) is tuple and len(feature) == 2

        features = tuple(feature_names)
        self._raw_features = features
        self._test = test

        # Find the features marked as continuous
        self._continuous = frozenset(
            f[0] for f in features if ispair(f) and f[1] is True)

        # Flatten the feature list (remove continuous labels)
        self._features = tuple(f if not ispair(f) else f[0] for f in features)
        continuous_idx = frozenset(map(self._features.index, self._continuous))

        # Continuous data points should be real numbers
        self._data = [tuple(float(e) if i in continuous_idx else e
                            for i, e in enumerate(tup)) for tup in data]
        self._labels = frozenset(tup[-1] for tup in self._data)
        self._root_majority = root_majority or max(self._labels,
                                                   key=self._count_label)

    def classify(self, instance: tuple) -> str:
        '''
        Predict the label of `instance'. `instance' can be a tuple of length
        equal to or one less than the width of the training data. The former
        case means `instance' has its label in the last position, in which case
        it is ignored.
        If the tree has branches and none accepts the instance, then either the
        instance or the branching is malformed, and a ValueError is raised.
        '''
        for branch in self._branches:
            if branch._test(instance):
                return branch.classify(instance)
        if self._has_branches:
            raise ValueError('no branch accepted %r' % (instance,))
        return self.prediction

    def show(self, dot: Digraph=None, is_root: bool=True) -> Digraph:
        '''
        Give a graphviz visualization of the tree. The two parameters are for
        recursive calls and should be ignored by user code.
        '''
        dot = dot or Digraph()
        key = str(uuid4())
        label = self._best_feature if self._has_branches else self.prediction
        dot.node(key, label=label)
        for branch in self._branches:
            dot, child_key = branch.show(dot, is_root=False)
            test = branch._test.funcs[1]
            dot.edge(key, child_key, label='%s %s' % (
                getattr(test, 'func').__name__, getattr(test, 'args')[0]))
        return dot if is_root else (dot, key)

    @property
    def prediction(self) -> str:
        '''
        The label this node would give if it were a leaf. Examines the training
        data and picks the most popular label. If multiple classes have the
        same frequency, returns the root majority.
        '''
        most_popular = [
            (label, self._count_label(label)) for label in (self._labels)]
        return (most_popular[0][0] if len(self._labels) == 1
                or most_popular[0][1] > most_popular[1][1]
                else self._root_majority)

    @classmethod
    def from_csv(
            cls,
            path: Union[str, PathLike],
            delimiter: str=',',
            features: _FeatureListT=None) -> 'DecisionTree':
        '''
        Load features and training data straight from csv file. `path'
        specifies the location of the file, `delimiter' is the cell separator
        passed to csv.reader, and `features' is a list of feature labels (as
        described in __init__). If `features' is None, the first row of the
        file will be interpreted as the feature labels and they will all
        be discrete features.
        '''
        with open(path) as fs:
            r = reader(fs, delimiter=delimiter)
            features = features or tuple(next(r))
            return cls(features, *r)

    # ====================
    # Entropy calculations
    # ====================

    def _information_gain(self, *tests: _PredicateT) -> float:
        '''
        Compute the information gain of the feature splitting encoded in
        `tests'.
        IG(Y|X=x) = H(Y) - H(Y|X=x)
        '''
        return self._entropy - self._conditional_entropy(*tests)

    def _conditional_entropy(self, *tests: _PredicateT) -> float:
        '''
        Compute the conditional entropy of class Y given feature X. X is
        encoded into `tests', which is a series of predicates which partition
        the data into mutually exclusive subsets.
        H(Y|X) = sum[x](p(x) * H(Y|X=x))
        '''
        entropy = 0.
        for test in tests:
            # `count' is the number of instances that pass the test (i.e. that
            # belong to the branch)
            count = self._count(test)
            # `frequency' is the number of those passing instances that have
            # each label
            frequencies = list(
                sum(1 for t in self._data if test(t) and t[-1] == label)
                for label in self._labels)
            # `total' represents the entropy contributed by this branch
            try:
                total = -sum(
                    (freq / count) * lg(freq / count) for freq in frequencies)
            except (ValueError, ZeroDivisionError):
                continue
            entropy += (count / len(self._data)) * total
        return entropy

    @property  # type: ignore
    @lru_cache(maxsize=1)
    def _entropy(self) -> float:
        '''
        Gives the unconditional entropy of the label class.
        H(Y) = -sum[i:=1->m](p_i log(p_i)) where p_i = P(Y = y_i)
        '''
        probs = (c / len(self._data)
                 for c in map(self._count_label, self._labels))
        return -sum(p * lg(p) for p in probs)

    SPLIT_CRITERION = _information_gain

    # =============================
    # Helper methods and properties
    # =============================

    def _best_split(self, feature: str) -> float:
        '''
        Compute the best pivot for continuous `feature'. Scans the observed
        feature values and computes the one with the greatest split metric.
        '''
        if feature not in self._continuous:
            raise TypeError('expecting a continuous feature')
        feature_index = self._features.index(feature)
        return max(
            frozenset(t[feature_index] for t in self._data),
            key=lambda value: self.SPLIT_CRITERION(
                *self._gen_tests(feature, value)))

    def _count(self, test: _PredicateT) -> int:
        '''
        Count the number of instances which pass predicate `test' (which should
        be a function of a data tuple).
        '''
        return sum(1 for t in self._data if test(t))

    def _count_label(self, label: str) -> int:
        '''
        Count the number of tuples with label `label'. Leverages
        DecisionTree._count by constructing the predicate which determines if a
        tuple has the argument label and calling it for the summation.
        '''
        has_label: compose[bool] = compose(itemgetter(-1), partial(eq, label))
        return self._count(has_label)

    def _gen_tests(self, feature: str, split: float=None) -> Generator:
        '''
        Generate the tests which branch `feature'. Yields a series of
        predicates that partition this node's data into mutually exclusive
        subsets (i.e. for each instance, exactly one of the yielded predicates
        will be true).
        '''
        feature_index = self._features.index(feature)
        if feature in self._continuous:
            split = split if split is not None else self._best_split(feature)
            yield compose(itemgetter(feature_index), partial(lt, split))
            yield compose(itemgetter(feature_index), partial(ge, split))
        else:
            for val in frozenset(t[feature_index] for t in self._data):
                yield compose(itemgetter(feature_index), partial(eq, val))

    @property
    def _best_feature(self) -> str:
        '''
        The feature which gives the best SPLIT_CRITERION metric. Considers both
        discrete and continuous features (only excludes label class.).
        '''
        return max(self._features[:-1],
                   key=lambda f: self.SPLIT_CRITERION(*self._gen_tests(f)))

    @property
    def _branches(self) -> Iterable['DecisionTree']:
        '''
        Finds the optimal branching of this tree and returns the computed
        subtrees.
        '''
        if not self._has_branches:
            return []
        for test in self._gen_tests(self._best_feature):
            yield type(self)(
                self._raw_features,
                *filter(test, self._data),
                test=test,
                root_majority=self._root_majority)

    @property
    def _has_branches(self) -> bool:
        '''
        Report whether the node will branch or not (i.e. whether terminal
        conditions have been met yet).
        '''
        return len(self._data) > 10 and (
            self.SPLIT_CRITERION(
                *self._gen_tests(self._best_feature)) > 0.00001)

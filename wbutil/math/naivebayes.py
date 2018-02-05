#!/usr/bin/env python

'''
wbutil/math/naivebayes.py

Naïve Bayes classifier.

Will Badart <netid:wbadart>
created: FEB 2018
'''

from collections import Counter, defaultdict
from csv import reader
from pprint import pformat
from typing import Sequence

__all__ = [
    'NaiveBayes',
]


class NaiveBayes(object):
    '''
    NaiveBayes objects represent a classifier trained for the given context.
    '''

    def __init__(
            self,
            features: Sequence[str],
            *data: tuple,
            label_index=-1,
            domains=None) -> None:
        '''
        Construct a new naive bayes model with features `features' and training
        instances `data'.

        Specify the column of the label with `label_index' (negative numbers
        are interpreted as index from the right, e.g. label_index = -2 if the
        label is in the second to last column.

        `domains' is a list of types that correspond 1-1 with the features.
        Each domain can be any callable to be applied to the cells of that
        column. Defaults to identity.
        '''
        self._features = features
        self._data = data
        self._label_index = (
            label_index if label_index >= 0 else len(features) + label_index)
        self._label = features[self._label_index]
        self._domains = domains or (_identity,) * len(features)

        # self._counts tracks, for each class for each feature, the number of
        # occurrences of each label
        self._counts: dict = {
            feature: defaultdict(Counter) for feature in features}

        for instance in data:
            instance = tuple(
                self._domains[i](val) for i, val in enumerate(instance))
            for feat, val in self._genfeats(instance):
                self._counts[feat][val][instance[self._label_index]] += 1
            # indexing None moves us from the defaultdict into the Counter for
            # the label counts
            self._counts[self._label][None][instance[self._label_index]] += 1

    def predict(self, instance):
        '''
        Predict the label of the given unlabeled test instance.

            Y = argmax[yj in Y] P(yj) * PRODUCT[P(xi|yj) for xi in X]
        '''
        maxlabel, maxprob = None, 0.0
        for label, count in self._counts[self._label][None].items():

            # prior probability
            labelprob = count / len(self._data)

            # probability of feature=value given current label
            for feat, val in self._genfeats(instance):
                labelprob *= self.probability(feat, val, label)

            if labelprob >= maxprob:
                maxprob = labelprob
                maxlabel = label

        return maxlabel, maxprob

    def probability(self, feature, value, class_):
        '''Read class counts to determine the probability of x_i give y_j.'''
        count = self._counts[feature][value][class_]
        # the frequency of label `class_' for all values of `feature'
        total = sum(ct[class_] for ct in self._counts[feature].values())
        return count / total

    def prediction_report(self, instance):
        '''
        Predict the label of the given instance and return a pretty string with
        the result.
        '''
        prediction, probability = self.predict(instance)
        return (
            'Prediction:\n'
            '    Tuple:       %s\n'
            '    Label:       "%s"\n'
            '    Probability: %f'
            % (instance, prediction, probability))

    @classmethod
    def from_csv(cls, path: str, label_index: int=-1) -> 'NaiveBayes':
        '''
        Generate a Naive Bayes model from a csv file, where the first row
        contains the feature names. label_index follows same convention as
        __init__.
        '''
        with open(path) as fs:
            return cls(*map(tuple, reader(fs)), label_index=label_index)

    def _skiplabel(self, tup):
        '''Iterate over a tuple, skipping the label column.'''
        return (e for i, e in enumerate(tup) if i != self._label_index)

    def _genfeats(self, instance):
        '''
        Iterate over a tuple, including feature name and skipping label column.
        '''
        return self._skiplabel(zip(self._features, instance))

    def __repr__(self):
        return '{cls}({features!r},\n{data},\nlabel_index={idx})'.format(
            cls=type(self).__name__,
            features=self._features,
            data=pformat(self._data),
            idx=self._label_index)

    def __str__(self):
        features = (
            f if i != self._label_index else '*' + f
            for i, f in enumerate(self._features))
        return '{cls}({features})'.format(
            cls=type(self).__name__, features=', '.join(features))


def _identity(a):
    '''Returns the argument.'''
    return a

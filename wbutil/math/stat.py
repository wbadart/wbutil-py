#!/usr/bin/env python

'''
wbutil/math/stat.py

Various utilities for descriptive statistics.

Will Badart <wbadart@live.com>
created: FEB 2018
'''

from collections import Counter
from numbers import Real
from typing import Tuple, Sequence

__all__ = [
    'ConfusionMatrix',
    'mean',
    'median',
    'variance',
    'std',
]


class ConfusionMatrix(object):
    '''
    Track the performance of a binary classifier. Report performance measures
    such as accuracy, recall, precision, and balanced F1 score.

    >>> m = ConfusionMatrix('win', 'lose')
    >>> m.updates(('win', 'win'), ('win', 'lose'))
    >>> m.accuracy
    0.5
    '''

    def __init__(self, positive_label: str, negative_label: str) -> None:
        self._pos = positive_label
        self._neg = negative_label
        self._c: Counter = Counter(TP=0, FP=0, TN=0, FN=0)

    def update(self, actual_label: str, predicted_label: str) -> None:
        '''
        Report a prediction and the corresponding true label. If either of the
        argument labels do not correspond to either the positive or negative
        labels of this matrix, a ValueError is raised.
        '''
        if actual_label not in self._labels:
            raise ValueError('label %r is not a known label' % actual_label)
        if predicted_label not in self._labels:
            raise ValueError(
                'prediction %r is not a known label' % predicted_label)

        if predicted_label == self._pos:
            if predicted_label == actual_label:
                self._c['TP'] += 1
            else:
                self._c['FP'] += 1

        elif predicted_label == self._neg:
            if predicted_label == actual_label:
                self._c['TN'] += 1
            else:
                self._c['FN'] += 1

    def updates(self, *results: Tuple[str, str]) -> None:
        '''
        Process a list of classifications. Each `result' should be a 2-tuple
        with the actual label on the left and the predicted label on the right.
        '''
        for actual, predicted in results:
            self.update(actual, predicted)

    @property
    def accuracy(self) -> float:
        '''
        Report the accuracy of the model (proportion of predictions which we
        correct.
        (TP + TN) / |observations|
        '''
        return (self.TP + self.TN) / len(self)

    @property
    def error(self) -> float:
        '''
        Report the model's error rate (another way to frame accuracy). Gives
        1 - accuracy or:
        (FP + FN) / |observations|
        '''
        return (self.FP + self.FN) / len(self)

    @property
    def sensitivity(self) -> float:
        '''
        True positive recognition rate (for data sets with heavy class
        imbalance).
        TP / P aka TP / (TP + FN)
        '''
        return self.TP / (self.TP + self.FN)

    @property
    def specificity(self) -> float:
        '''
        True negative recognition rate
        TN / N aka TN / (TN + FP)
        '''
        return self.TN / (self.TN + self.FP)

    @property
    def precision(self) -> float:
        '''
        Report the precision of the model. Signals how exact the model is by
        calculating the proportion of positive labels which corresponded to
        actual positive instances.
        TP / P' where P' is the total number of positive predictions, TP + FP
        '''
        return self.TP / (self.TP + self.FP)

    @property
    def recall(self) -> float:
        '''
        Proportion of positive instances labeled as such by the model.
        TP / P (same as sensitivity)
        '''
        return self.TP / (self.TP + self.FN)

    @property
    def f1(self) -> float:
        '''
        Gives the balanced F measure for the model.
        2PR / (P + R) where P and R are precision and recall respectively.
        '''
        return 2 * self.precision * self.recall \
            / (self.precision + self.recall)

    @property
    def TP(self) -> int:
        '''
        Count of true positives (actual and prediction both positive) observed.
        '''
        return self._c['TP']

    @property
    def FP(self) -> int:
        '''
        Count of false positives (predicted positive for negative instance)
        observed.
        '''
        return self._c['FP']

    @property
    def TN(self) -> int:
        '''
        Count of true negatives (actual and prediction both negative) observed.
        '''
        return self._c['TN']

    @property
    def FN(self) -> int:
        '''
        Count of false negatives (predicted false for a positive instance)
        observed.
        '''
        return self._c['FN']

    @property
    def _labels(self) -> set:
        return {self._pos, self._neg}

    def __len__(self) -> int:
        '''Corresponds to the number of predictions observed.'''
        return sum(self._c.values())

    def __str__(self) -> str:
        '''Gives a nice, relatively pretty-printed table of results.'''
        return (
            f'Actual \\ Predicted | {self._pos} | {self._neg}\n'
            f'    {self._pos} | {self.TP} | {self.FN}\n'
            f'    {self._neg} | {self.FP} | {self.TN}')


def mean(a: Sequence[Real]) -> float:
    '''
    Return the mean of a list of numbers.

    >>> mean([1, 2, 3, 4])
    2.5
    '''
    return sum(a) / len(a)


def median(a: Sequence[Real]) -> float:
    '''
    Return the median of a list of numbers.

    >>> median([4, 6, 1])
    4
    >>> median([1, 1, 2, 3])
    1.5
    '''
    if _isodd(len(a)):
        return float(sorted(a)[len(a) // 2])
    else:
        return mean(sorted(a)[len(a) // 2 - 1:len(a) // 2 + 1])


def variance(a: Sequence[Real]) -> float:
    '''
    Get the variance (average squared distance to the mean) of a number list.

    >>> variance([1, 2, 3])
    0.6666666666666666
    >>> variance([1, 1, 1, 1])
    1.0
    '''
    avg = mean(a)
    return mean([(avg - e) ** 2 for e in a])


def std(a: Sequence[Real]) -> float:
    '''
    Gives the standard deviation of a list of numbers (sqrt(variance)).
    '''
    return variance(a) ** 0.5


def _isodd(n):
    return n % 2 != 0

from itertools import combinations

import numpy as np
from sklearn.externals.joblib import Parallel, delayed
from sklearn.neighbors import NearestNeighbors
from sklearn.utils import check_array, gen_even_slices
from sklearn.utils.validation import check_is_fitted

from ..base import BaseDetector
from ...utils import assign_info_on_pandas_obj, construct_pandas_obj

__all__ = ['FastABOD']


def _abof(X, ind, fit_X):
    """Compute angle-based outlier factors for test samples."""

    with np.errstate(invalid='raise'):
        return np.var([[
            (pa @ pb) / (pa @ pa) / (pb @ pb) for pa, pb in combinations(
                fit_X[ind_p] - p, 2
            )
        ] for p, ind_p in zip(X, ind)], axis=1)


class FastABOD(BaseDetector):
    """Fast angle-based outlier detector.

    Parameters
    ----------
    fpr : float, default 0.01
        False positive rate. Used to compute the threshold.

    metric : str or callable, default 'minkowski'
        Metric to use for distance computation.

    metric_params : dict, default None
        Additional keyword arguments for the metric function.

    n_jobs : int, default 1
        Number of jobs to run in parallel. If -1, then the number of jobs is
        set to the number of CPU cores.

    n_neighbors : int, default 5
        Number of neighbors.

    p : int, default 2
        Power parameter for the Minkowski metric.

    Attributes
    ----------
    threshold_ : float
        Threshold.

    References
    ----------
    H.-P. Kriegel, M. Schubert and A. Zimek,
    "Angle-based outlier detection in high-dimensional data,"
    In Proceedings of SIGKDD'08, pp. 444-452, 2008.
    """

    def __init__(
        self,               fpr=0.01,
        metric='minkowski', metric_params=None,
        n_jobs=1,           n_neighbors=5,
        p=2
    ):
        self.fpr           = fpr
        self.metric        = metric
        self.metric_params = metric_params
        self.n_jobs        = n_jobs
        self.n_neighbors   = n_neighbors
        self.p             = p

        self.check_params()

    def check_params(self):
        """Check validity of parameters and raise ValueError if not valid."""

        if self.fpr < 0.0 or 1.0 < self.fpr:
            raise ValueError(
                'fpr must be between 0 and 1 inclusive but was {0}'.format(
                    self.fpr
                )
            )

        if self.n_neighbors <= 1:
            raise ValueError(
                'n_neighbors must be greator than 1 but was {0}'.format(
                    self.n_neighbors
                )
            )

        if self.p < 1:
            raise ValueError(
                'p must be greater than or equal to 1 but was {0}'.format(
                    self.p
                )
            )

    @assign_info_on_pandas_obj
    def fit(self, X, y=None):
        """Fit the model according to the given training data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        self : detector
            Return self.
        """

        X                 = check_array(X)

        self._knn         = NearestNeighbors(
            metric        = self.metric,
            metric_params = self.metric_params,
            n_jobs        = self.n_jobs,
            n_neighbors   = self.n_neighbors,
            p             = self.p
        ).fit(X)

        self.y_score_     = self.anomaly_score()
        self.threshold_   = np.percentile(
            self.y_score_, 100.0 * (1.0 - self.fpr)
        )

        return self

    @construct_pandas_obj
    def anomaly_score(self, X=None):
        """Compute anomaly scores for test samples.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features), default None
            Test samples.

        Returns
        -------
        y_score : array-like of shape (n_samples,)
            Anomaly scores for test samples.
        """

        check_is_fitted(self, '_knn')

        if X is None:
            X        = self._knn._fit_X
            ind      = self._knn.kneighbors(None, return_distance=False)
        else:
            X        = check_array(X)
            ind      = self._knn.kneighbors(X, return_distance=False)

        n_samples, _ = X.shape

        try:
            result   = Parallel(self.n_jobs)(
                delayed(_abof)(
                    X[s], ind[s], self._knn._fit_X
                ) for s in gen_even_slices(n_samples, self.n_jobs)
            )
        except FloatingPointError as e:
            raise ValueError('X must not contain training samples') from e

        return -np.concatenate(result)
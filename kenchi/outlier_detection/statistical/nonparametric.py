import numpy as np
from sklearn.neighbors import KernelDensity
from sklearn.utils import check_array
from sklearn.utils.validation import check_is_fitted

from ..base import BaseDetector
from ...utils import assign_info_on_pandas_obj, construct_pandas_obj

VALID_KERNELS = [
    'gaussian', 'tophat', 'epanechnikov', 'exponential', 'linear', 'cosine'
]


class KernelDensityOutlierDetector(BaseDetector):
    """Outlier detector using kernel density estimation.

    Parameters
    ----------
    bandwidth : float, default 1.0
        Bandwidth of the kernel.

    fpr : float, default 0.01
        False positive rate. Used to compute the threshold.

    kernel : str, default 'gaussian'
        Kernel to use.

    metric : str or callable, default 'minkowski'
        Metric to use for distance computation.

    metric_params : dict, default None
        Additional keyword arguments for the metric function.

    Attributes
    ----------
    threshold_ : float
        Threshold.
    """

    def __init__(
        self,               bandwidth=1.0,
        fpr=0.01,           kernel='gaussian',
        metric='euclidean', metric_params=None
    ):
        self.bandwidth     = bandwidth
        self.fpr           = fpr
        self.kernel        = kernel
        self.metric        = metric
        self.metric_params = metric_params

        self.check_params()

    def check_params(self):
        """Check validity of parameters and raise ValueError if not valid."""

        if self.bandwidth <= 0.0:
            raise ValueError(
                'bandwidth must be positive but was {0}'.format(
                    self.bandwidth
                )
            )

        if self.fpr < 0 or 1 < self.fpr:
            raise ValueError(
                'fpr must be between 0 and 1 inclusive but was {0}'.format(
                    self.fpr
                )
            )

        if self.kernel not in VALID_KERNELS:
            raise ValueError('invalid kernel: {0}'.format(self.kernel))

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

        self._kde         = KernelDensity(
            bandwidth     = self.bandwidth,
            kernel        = self.kernel,
            metric        = self.metric,
            metric_params = self.metric_params
        ).fit(X)

        self.y_score_     = self.anomaly_score(X)
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

        check_is_fitted(self, '_kde')

        if X is None:
            return self.y_score_
        else:
            X = check_array(X)

            return -self._kde.score_samples(X)
from abc import abstractmethod, ABCMeta

import numpy as np
from sklearn.utils.validation import check_is_fitted


from .plotting import plot_anomaly_score
from .utils import construct_pandas_object


class DetectorMixin(metaclass=ABCMeta):
    """Mixin class for all detectors."""

    _estimator_type    = 'detector'

    plot_anomaly_score = plot_anomaly_score

    @abstractmethod
    def fit(self, X, y=None, **fit_params):
        """Fit the model according to the given training data."""

        pass

    @abstractmethod
    @construct_pandas_object
    def anomaly_score(self, X):
        """Compute anomaly scores."""

        pass

    @construct_pandas_object
    def predict(self, X):
        """Predict if a particular sample is an outlier or not.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples.

        Returns
        -------
        y_pred : array-like, shape = (n_samples,)
            Return 0 for inliers and 1 for outliers.
        """

        check_is_fitted(self, 'threshold_')

        return (self.anomaly_score(X) > self.threshold_).astype(np.int32)

    def fit_predict(self, X, y=None, **fit_params):
        """Fit the model according to the given training data and predict
        labels (0 inlier, 1 outlier) on the training set.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : array-like, shape = (n_samples,)
            Return 0 for inliers and 1 for outliers.
        """

        return self.fit(X, y, **fit_params).predict(X)

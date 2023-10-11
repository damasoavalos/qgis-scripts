import numpy as np
from scipy.special import comb
from matplotlib import pyplot as plt
import bezier

import sys
sys.path.append(r'D:\Repositories\python-scripts\qgis-scripts')
from vertices import vertices


def bernstein_poly(i, n, t):
    """
     The Bernstein polynomial of n, i as a function of t
    """

    return comb(n, i) * (t**(n-i)) * (1 - t)**i


def bezier_curve(_points, _nTimes=1000):
    """
       Given a set of control _points, return the
       Bézier curve defined by the control _points.

       _points should be a list of lists, or list of tuples
       such as [ [1,1],
                 [2,3],
                 [4,5], ..[Xn, Yn] ]
        _nTimes is the number of time steps, defaults to 1000

        See http://processingjs.nihongoresources.com/bezierinfo/
    """

    _nPoints = len(_points)
    _xPoints = np.array([p[0] for p in _points])
    _yPoints = np.array([p[1] for p in _points])

    bp = []
    polynomial_array = []
    t = np.linspace(0.0, 1.0, _nTimes)
    for i in range(0, _nPoints):
        bp.append(bernstein_poly(i, _nPoints - 1, t))
    polynomial_array = np.array(bp)
    # polynomial_array = np.array([bernstein_poly(i, _nPoints-1, t) for i in range(0, _nPoints)])

    _xvals = np.dot(_xPoints, polynomial_array)
    _yvals = np.dot(_yPoints, polynomial_array)

    return _xvals, _yvals


if __name__ == "__main__":

    nPoints = 4
    points = np.random.rand(nPoints, 2)*200
    # points = np.asfortranarray(vertices)
    xpoints = [p[0] for p in points]
    ypoints = [p[1] for p in points]

    xvals, yvals = bezier_curve(points, _nTimes=1000)
    plt.plot(xvals, yvals)
    plt.plot(xpoints, ypoints, "ro")
    for nr in range(len(points)):
        plt.text(points[nr][0], points[nr][1], nr)

    plt.show()

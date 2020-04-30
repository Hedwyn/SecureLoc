"""****************************************************************************
Copyright (C) 2019 LCIS Laboratory - Baptiste Pestourie

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, in version 3.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
This program is part of the SecureLoc Project @https://github.com/Hedwyn/SecureLoc
 ****************************************************************************

@file GaussNewton.py
@author Baptiste Pestourie
@date 2019 July 1st
@brief Application class - handles the localization engine scheduling and main operations
@see https://github.com/Hedwyn/SecureLoc
@see Adapted from https://github.com/basil-conto/gauss-newton,
shared by Basil L. Contovounesios
This code has been modified so it can handle 3D instead of 1D variables.
Some variables have been renamed.A dynamic correction feature has been added so as the correction vector is decreasing over the iterations.
All the functions have been integrated into a single class.
"""

import numpy as np
import sympy as sp
from parameters import *




class GNdataset:
    """Representation of a NIST nonlinear regression dataset.
    The class attributes are the same as the constructor parameters.
    """

    def __init__(self, name, expr, symbols, xvals, yvals, zvals, rangingvals, cvals, starts ):
        """Create a new Dataset.
        Parameters / Attributes
        -----------------------
        name : string
            Name of dataset, e.g. "Misra1a".
        expr : string
            Representation of dataset's model in a format understood by
            sympy.sympify().
        symbols : tuple or list
            SymPy Symbols found in `expr`. The first one should be the predictor
            variable and the rest are interpreted as model parameters.
        xvals : ndarray
            Observed or generated values for predictor variable.
        rangingvals : ndarray
            Observed or generated values for response variable.
        cvals : ndarray
            Certified values (i.e. reference solutions) for model parameters.
        starts : ndarray
            Nested set of initial guesses or starting estimates for the least
            squares solution of the system.
        """
        # Parameters become attributes
        self.name, self.starts  = name, starts
        self.expr, self.symbols = expr, symbols

        self.xvals,self.yvals, self.zvals, self.rangingvals, self.cvals = xvals, yvals, zvals, rangingvals, cvals

        # Predictor variable and parameters
        self._x,self._y, self._z,self._b = symbols[0], symbols[1], symbols[2], symbols[3:]

        # SymPy expression
        self._symexpr = sp.sympify(expr)
        # NumPy expression
        self._numexpr = sp.lambdify((self._x,) + (self._y,) + (self._z,)  + self._b, self._symexpr, "numpy")
        # Partial derivatives
        self._pderivs = [self._symexpr.diff(b) for b in self._b]
        d_print("derivatives: " + str(self._pderivs))

    def __repr__(self):
        """Return Dataset description in the form <Dataset NAME at ADDRESS>."""
        return "<Dataset {} at {:x}>".format(self.name, id(self))

    def __str__(self):
        """Return name of Dataset, e.g. "Misra1a"."""
        return self.name

    def model(self, x = None, y = None, z = None, b = None):
        """Evaluate the model with the given predictor variable and parameters.
        Parameters
        ----------
        x : ndarray
            Values for the predictor variable. Defaults to the model's observed
            or generated values.
        b : tuple, list or ndarray
            Values for the model parameters. Defaults to their certified values.
        Return
        ------
        y : ndarray
            Corresponding values for the response variable.
        """
        if x is None: x = self.xvals
        if y is None: x = self.yvals
        if z is None: x = self.zvals
        if b is None: b = self.cvals
        return self._numexpr(x,y,z, *b)

    def residuals(self, b):
        """Evaluate the residuals f(x, b) - y with the given parameters.
        Parameters
        ----------
        b : tuple, list or ndarray
            Values for the model parameters.
        Return
        ------
        out : ndarray
            Residual vector for the given model parameters.
        """
        x, y, z, r = self.xvals,self.yvals, self.zvals, self.rangingvals
        residuals = self._numexpr(x,y,z, *b) - r
        d_print("residuals :\n" + str(residuals))
        return residuals

    def jacobian(self, b):
        """Evaluate the model's Jacobian matrix with the given parameters.
        Parameters
        ----------
        b : tuple, list or ndarray
            Values for the model parameters.
        Return
        ------
        out : ndarray
            Evaluation of the model's Jacobian matrix in column-major order wrt
            the model parameters.
        """
        # Substitute parameters in partial derivatives
        subs = [pd.subs(zip(self._b, b)) for pd in self._pderivs]
        d_print("partial derivatives\n:" + str(subs) )
        # Evaluate substituted partial derivatives for all x-values
        vals = [sp.lambdify((self._x,) + (self._y,) + (self._z,) , sub, "numpy")(self.xvals,self.yvals,self.zvals) for sub in subs]
        # Arrange values in column-major order

        d_print("jacobian:\n" + str(np.column_stack(vals)))
        return np.column_stack(vals)


    def solve(self,x0, start_ratio = 0.5, dynamic_ratio = 0.95, tol = 1e-10, maxits = 8):
        """Gauss-Newton algorithm for solving nonlinear least squares problems.
        Parameters
        ----------
        x0 : tuple, list or ndarray
            Initial guesses or starting estimates for the system.

        start_ratio: the ratio of the correction vector that is applied at the first iteration. Shoud be 1 or less.
        dynamic_ratio: multiplicative ratio applied at each iteration on the correction vector;
                       allows decreasing the magnitude of the correction vector at each iteration.
        tol : float
            Tolerance threshold. Not used here. When enabled, the problem is considered solved when this value
            becomes smaller than the magnitude of the correction vector.
            Defaults to 1e-10.
        maxits : int
            Maximum number of iterations of the algorithm to perform.
            If the tolerance threshold is disabled, the number of iterations will always be maxits.
            Defaults to 5.
        Return
        ------
        sol : ndarray
            Resultant values.
        its : int
            Number of iterations performed.
        Note
        ----
        Uses numpy.linalg.pinv() in place of similar functions from scipy, both
        because it was found to be faster and to eliminate the extra dependency.
        """

        dx = np.ones(len(x0))   # Correction vector
        xn = np.array(x0)       # Approximation of solution

        i = 0
        ratio = start_ratio
        while (i < maxits):# and (dx[dx > tol].size > 0):
            # correction = pinv(jacobian) . residual vector
            dx  = ratio * np.dot(np.linalg.pinv(self.jacobian(xn)), -self.residuals(xn))

            d_print("xn:" + str(xn))
            xn += dx            # x_{n + 1} = x_n + dx_n

            i  += 1
            ratio *= dynamic_ratio

        return xn, i

def GN_test():
    """Test function for this module. Applies GN algorithm on given datasets."""

    # Inhibit wrapping of arrays in print
    np.set_printoptions(linewidth = 256)

    for ds in Test,:
        for i, x0 in enumerate(ds.starts):
            sol, its = ds.solve(x0)
            cv = ds.cvals
            print("{}, start {}:".format(ds, i + 1))
            print("  Iterations : {}".format(its))
            print("  Calculated : {}".format(sol))




# Example dataset for rangings
# Test = GNdataset(
#        name = "Test",
#        expr = "sqrt((x-b1)**2 + (y-b2)**2 + (z-b3)**2)",
#     symbols = sp.symbols("x y z b1:4"),
#       xvals = np.array(( 0., 0.9, 1.8)),
#       yvals = np.array(( 0., 4.8, 0.)),
#       zvals = np.array(( 0., 0., 0.)),
#       rangingvals = np.array((1.8,4.8,0.)),
#       cvals = None,
#      starts = np.array(((0.0, 0.4,0.), ))
# )
Test = GNdataset(
       name = "Test",
       expr = "(x-b1)**2 + (y-b2)**2 + (z-b3)**2",
    symbols = sp.symbols("x y z b1:4"),
      xvals = np.array(( 0., 3.0, 0.)),
      yvals = np.array(( 0., 0.0, 3.0)),
      zvals = np.array(( 0.0, 0., 0.)),
      rangingvals = np.array((3.5,3.5,3.5)),
      cvals = None,
     starts = np.array(((0.0, 0.4,0.1), ))
)



if __name__ == "__main__":
    GN_test()

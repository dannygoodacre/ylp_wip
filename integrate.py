import numpy as np
import scipy as sp
import qutip as qt

def integrate(f, a, b, deg=100):
    x, w = np.polynomial.legendre.leggauss(deg)
    val = 0
    h = (b - a) / 2
    c = (a + b) / 2
    for i in range(deg):
        val += w[i] * f(h*x[i] + c)
    val *= h
    
    return val

def pre_integrate(H_coeff, tlist, method):
    integrals = []
    if method == "scipy":
        for i in range(len(tlist)):
            val = [0, 0, 0]
            val[0] = sp.integrate.quad(H_coeff[i][0], tlist[i], tlist[i+1])
            val[1] = sp.integrate.quad(H_coeff[i][1], tlist[i], tlist[i+1])
            val[2] = H_coeff[2] * (tlist[i+1] - tlist[i])
            integrals.append(val)
    elif method == "me":
        for i in range(len(tlist)):
            val = [0, 0, 0]
            val[0] = integrate(H_coeff[i][0], tlist[i], tlist[i+1])
            val[1] = integrate(H_coeff[i][1], tlist[i], tlist[i+1])
            val[2] = H_coeff[2] * (tlist[i+1] - tlist[i])
            integrals.append(val)
    else:
        print("Error: invalid method.")
        return 0
    
    return integrals
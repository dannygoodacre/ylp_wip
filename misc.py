from math import sqrt
import numpy as np
import scipy as sp
import qutip as qt

def vec(mat):
    """
    Return a vector formed by stacking columns of matrix.

    Parameters
    ----------
    mat : ndarray
        Matrix.

    Returns
    -------
    ndarray
        Vectorised form of matrix, using column-major (Fortran) ordering.

    """
    return np.asarray(mat).flatten('F')

def unvec(vec, c = None):
    """
    Return unvectorised/re-matricised vector using column-major (Fortran) ordering.

    Parameters
    ----------
    vec : ndarray
        Vector of elements.
    c : int, optional
        Desired length of columns in matrix. Leave blank if a square matrix. The default is None.

    Returns
    -------
    ndarray
        Matrix formed from vector.

    """
    vec = np.array(vec)

    if (len(vec) % 2 != 0): # odd number of elements
        if (len(vec) == 1):
            return vec
        else:
            print("Error: odd number of elements in vector. Cannot form matrix.")
            return None
    elif (c == None):
        if (sqrt(len(vec)).is_integer()): # matrix is square
            c = int(sqrt(len(vec)))
        else: # matrix is not square
            print("Error: vector cannot form a square matrix. Please provide a column length, c.")
            return None
    elif (not (len(vec) / c).is_integer()): # c does not divide length of vec
        print("Error: value of c is invalid. Cannot split vector evenly into columns of length c")
        return None

    n = int(len(vec) / c) # number of rows

    return vec.reshape((c, n), order = 'F')

def liouvillian(H):
    """
    Return Liouvillian of system given the Hamiltonian.

    Parameters
    ----------
    H : ndarray
        Square matrix with dimension n.

    Returns
    -------
    ndarray
        Square matrix with dimension n^2.

    """
    H = np.asarray(H)
    n = H.shape[0]

    return (np.kron(np.eye(n),H) - np.kron(H.T,np.eye(n)))

def traceInnerProduct(a, b):
    """
    Return trace inner product of two square matrices.

    Parameters
    ----------
    a : ndarray
        Either an individual or array of numpy.array, numpy.matrix, or qutip.Qobj.
    b : ndarray
        Single np.array.

    Returns
    -------
    ndarray or scalar
        The value(s) of the trace of a times b.

    """
    a = np.asarray(a, dtype = object)
    b = np.asarray(b)

    try: # a is an array
        t = []
        for x in a:
            t.append(np.trace(x @ b))

        return np.asarray(t)
    except: # a is individual
        return np.trace(a @ b)

def BlochSphereCoordinates(H, rho0, tlist):
    """
    Return 3D coordinates for trace inner product of density matrix in each spin direction (x,y,z) at times tlist.
    Coordinates are normalised so they lie on the surface of a Bloch sphere.

    Parameters
    ----------
    H : qutip.Qobj
        System Hamiltonian.
    rho0 : qutip.Qobj
        Initial density matrix.
    tlist : list/array
        List of times for t.

    Returns
    -------
    int numpy.array, int numpy.array, int numpy.array
        3D coordinates as described above.

    """
    density_matrices = qt.mesolve(H, rho0, tlist)

    x = np.real(traceInnerProduct(density_matrices.states, qt.sigmax()))/2
    y = np.real(traceInnerProduct(density_matrices.states, qt.sigmay()))/2
    z = np.real(traceInnerProduct(density_matrices.states, qt.sigmaz()))/2

    return x,y,z

def timesteps(h, final_time, midpoint_time):
    times = np.linspace(0, final_time, int(final_time / h) + 1)

    if (midpoint_time):
        times = (times[1:] + times[:-1]) / 2
        
    return times

def setup_lvn(f, g, omega, rho0, h, final_time, midpoint_time):
    def H(t): return f(t)*qt.sigmax() + g(t)*qt.sigmay() + omega*qt.sigmaz()

    return H, [vec(rho0)], timesteps(h, final_time, midpoint_time)

def arnoldi(A, b): 
    """
    Construct orthonormal basis of m-order Krylov subspace generated by images of b under A: span{b, Ab, ..., A^(m-1)b} using the Arnoldi algorithm.

    Parameters
    ----------
    A : ndarray
        n x m.
    b : ndarray
        1 x m.

    Returns
    -------
    V : ndarray
        m x m matrix whose columns form an orthonormal basis of the Krylov subspace.
    H : ndarray
        m x m upper Hessenberg matrix.
    """
    m = A.shape[0]
    V = np.zeros((m, m), dtype = 'complex_')
    H = np.zeros((m, m), dtype = 'complex_')
    
    V[:, 0] = b / np.linalg.norm(b, 2)

    for j in range(1, m + 1):
        w = np.dot(A, V[:, j-1])

        for i in range(1, j+1):
            H[i-1, j-1] = np.dot(V[:, i-1].conj(), w)
            w = w - H[i-1, j-1]*V[:, i-1]
        
        if (j != m):
            H[j, j-1] = np.linalg.norm(w, 2)
            
            if H[j, j-1] > 1e-12:
                V[:, j] = w / H[j, j-1]
            else:
                return V, H

    return V, H

def lanczos(A, b):
    """
    Given Hermitian matrix A, construct orthonormal basis of m-order Krylov subspace generated by images of b under A: span{b, Ab, ..., A^(m-1)b} using the Lanczos algorithm.

    Parameters
    ----------
    A : ndarray
        m x m, Hermitian 
    b : ndarray
        1 x m, treated as column vector.

    Returns
    -------
    V : ndarray
        m x m matrix whose columns form an orthonormal basis of the Krylov subspace.
    T : ndarray
        m x m Tridiagonal matrix
    """
    m = A.shape[0]
    V = np.zeros((m, m), dtype = 'complex_')
    alpha = np.zeros((m,1), dtype = 'complex_')
    beta = np.zeros((m,1), dtype = 'complex_')

    W = np.zeros((m, m), dtype = 'complex_')

    V[:, 0] = b / np.linalg.norm(b)
    w_ = A @ V[:,0]
    alpha[0] = np.dot(w_.conj(),V[:,0])
    W[:,0] = w_ - alpha[0]*V[:,0]

    for j in range(2,m+1):
        beta[j-1] = np.linalg.norm(W[:,j-2])
        V[:, j-1] = W[:, j-2] / beta[j-1]
        w_ = A @ V[:, j-1]
        alpha[j-1] = np.dot(w_.conj(), V[:, j-1])
        W[:, j-1] = w_ - alpha[j-1]*V[:,j-1] - beta[j-1]*V[:,j-2]

    return V, np.diagflat(alpha) + np.diagflat(beta[1:], 1) + np.diagflat(beta[1:], -1)

def pade_expm(A, p, q):
    """
    Approximation of matrix exponential of A using (p,q) Padé approximants.

    Parameters
    ----------
    A : ndarray
        Square matrix.
    p : int
        Order of numerator of approximant.
    q : int
        Order of denominator of approximant.

    Returns
    -------
    ndarray
        The Padé approximant of exp(A)
    """
    N = 0
    D = 0

    f_p = sp.special.factorial(p)
    f_q = sp.special.factorial(q)
    f_p_q = sp.special.factorial(p+q)

    for i in range(0,p+1):
        N += ((sp.special.factorial(p + q - i) * f_p) / (f_p_q * sp.special.factorial(i) * sp.special.factorial(p-i))) * np.linalg.matrix_power(A,i)
    
    for i in range(0,q+1):
        D += ((sp.special.factorial(p + q - i) * f_q) / (f_p_q * sp.special.factorial(i) * sp.special.factorial(q-i))) * np.linalg.matrix_power(-A,i)
    
    return np.dot(np.linalg.inv(D),N)

def krylov_expm(A, b):
    """
    Approximation of matrix exponential of A multiplied by b using Krylov subspaces.

    Parameters
    ----------
    A : ndarray
        n x n matrix.
    b : ndarray
        n x 1

    Returns
    -------
    ndarray
        n x 1,  e^A * b
    """
    if (np.array_equal(A.conj().T, A)):
        V, H = lanczos(A, b) # more efficient for Hermitian matrix
    else:
        V, H = arnoldi(A, b)

    return np.linalg.norm(b) * V @ sp.linalg.expm(H) @ np.identity(A.shape[0])[:,0]
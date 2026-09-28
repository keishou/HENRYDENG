"""Pose-space corrective for linear blend skinning (LBS) artefacts, stored as a bind-space morph target.

LBS squares off / balloons blended regions when a joint rotates far from the bind pose (here: the
shoulder when MakeHuman's 49-degree A-pose arms are lowered to the sides).  For one target pose we solve

    min_P'  sum_i || (L P')_i - R_i (L V)_i ||^2  +  sum_i c_i^2 || P'_i - P_i ||^2

L = uniform graph Laplacian, V = bind-pose vertices, P = LBS-posed vertices, R_i = rotation part (polar
decomposition) of the vertex's blended LBS matrix, c_i = anchor weight: strong where one bone dominates
(LBS is exact there), weak in blended zones.  The correction is taken back to bind space through each
vertex's LBS matrix, d_i = M_i^-1 (P'_i - P_i), so that bind + d skinned into the target pose gives P'.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


def adjacency(fv, n):
    k = np.where(fv[:, 3] == fv[:, 2], 3, 4)
    a, b = [], []
    for j in range(4):
        m = j < k
        jn = np.where(j + 1 < k, j + 1, 0)
        a.append(fv[m, j])
        b.append(fv[np.nonzero(m)[0], jn[m]])
    a = np.concatenate(a)
    b = np.concatenate(b)
    A = sp.csr_matrix((np.ones(2 * len(a)), (np.r_[a, b], np.r_[b, a])), shape=(n, n))
    A.data[:] = 1.0
    return A


def lbs_mats(idx, w, D):
    """Per-vertex blended 3x3 LBS matrices."""
    return np.einsum("nk,nkij->nij", w, D[idx])


def polar_rot(M):
    U, _, Vt = np.linalg.svd(M)
    R = U @ Vt
    bad = np.linalg.det(R) < 0
    U[bad, :, -1] *= -1
    return U @ Vt


def stand_corrective(V, fv, idx, w, D, H, head_rest, anchor=4.0, power=6, soft=0.02, used=None):
    """Bind-space deltas (N,3) that remove LBS distortion in the pose (D, H).
    V (N,3) bind positions (metres), fv (F,4) faces, idx/w (N,k) skin weights."""
    n = len(V)
    T = H - np.einsum("bij,bj->bi", D, head_rest)
    M = lbs_mats(idx, w, D)
    t = np.einsum("nk,nkj->nj", w, T[idx])
    P = np.einsum("nij,nj->ni", M, V) + t
    A = adjacency(fv, n)
    deg = np.asarray(A.sum(1)).ravel()
    iso = deg == 0
    Dinv = sp.diags(1.0 / np.maximum(deg, 1))
    L = sp.identity(n, format="csr") - Dinv @ A
    delta = L @ V
    R = polar_rot(M)
    target = np.einsum("nij,nj->ni", R, delta)
    wmax = w.max(1)
    c = anchor * wmax ** power + soft
    c[iso] = 1e3
    if used is not None:
        c[~used] = 1e3
    Cm = sp.diags(c ** 2)
    Q = (L.T @ L + Cm).tocsc()
    solve = spla.factorized(Q)
    Pn = np.stack([solve(L.T @ target[:, j] + c ** 2 * P[:, j]) for j in range(3)], 1)
    d = np.linalg.solve(M, (Pn - P)[..., None])[..., 0]
    return d, P, Pn

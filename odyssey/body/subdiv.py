"""One level of Catmull-Clark subdivision expressed as a sparse linear operator.

Because every new vertex is a fixed non-negative combination of old vertices, the same matrix S
subdivides positions, skin weights, or anything else stored per vertex:

    S, fv2, U, fuv2 = catmull_clark(fv, fuv, n_verts, n_uvs)
    v2 = S @ v            # (n_new, 3)
    W2 = S @ W            # (n_new, bones), rows still sum to 1
    vt2 = U @ vt          # UVs are subdivided linearly (face-varying, seams preserved)

Faces are hm08-style (F,4) arrays in which a triangle repeats its last index.  Boundary edges
(hems, cuffs, necklines) use the standard crease rules so open edges stay put.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp


def _corners(fv):
    tri = fv[:, 3] == fv[:, 2]
    k = np.where(tri, 3, 4)
    return k


def _edge_table(fv, k):
    """Unique undirected edges of all faces; returns (edges (E,2), face_edge (F,4) index or -1)."""
    F = len(fv)
    a, b = [], []
    for j in range(4):
        valid = j < k
        jn = np.where(j + 1 < k, j + 1, 0)
        a.append(np.where(valid, fv[:, j], -1))
        b.append(np.where(valid, fv[np.arange(F), jn], -1))
    A = np.stack(a, 1)
    B = np.stack(b, 1)
    lo, hi = np.minimum(A, B), np.maximum(A, B)
    key = lo.astype(np.int64) * (1 << 32) + hi
    valid = A >= 0
    uk, inv = np.unique(key[valid], return_inverse=True)
    fe = -np.ones((F, 4), np.int64)
    fe[valid] = inv
    edges = np.stack([uk >> 32, uk & ((1 << 32) - 1)], 1)
    return edges, fe


def _linear_face_varying(fidx, k, n):
    """Linear subdivision of a face-varying index set (UVs): returns U (n2 x n) and new (4*sum?,4) faces."""
    edges, fe = _edge_table(fidx, k)
    E, F = len(edges), len(fidx)
    rows, cols, vals = [np.arange(n)], [np.arange(n)], [np.ones(n)]
    rows.append(n + np.repeat(np.arange(E), 2)); cols.append(edges.ravel()); vals.append(np.full(2 * E, 0.5))
    for j in range(4):
        m = j < k
        rows.append(n + E + np.nonzero(m)[0]); cols.append(fidx[m, j]); vals.append(1.0 / k[m])
    U = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n + E + F, n))
    return U, edges, fe


def _quads(fidx, k, fe, n, E):
    out = []
    F = len(fidx)
    fp = n + E + np.arange(F)
    for j in range(4):
        m = j < k
        jp = np.where(j - 1 >= 0, j - 1, k - 1)   # previous corner's edge index
        e_next = fe[:, j]
        e_prev = fe[np.arange(F), jp]
        q = np.stack([fidx[:, j], n + e_next, fp, n + e_prev], 1)
        out.append(q[m])
    return np.vstack(out)


def catmull_clark(fv, fuv, n_verts, n_uvs):
    fv = np.asarray(fv, np.int64)
    fuv = np.asarray(fuv, np.int64)
    k = _corners(fv)
    F = len(fv)
    edges, fe = _edge_table(fv, k)
    E = len(edges)
    n = n_verts
    # --- face points: mean of corners
    fr, fc, fw = [], [], []
    for j in range(4):
        m = j < k
        fr.append(np.nonzero(m)[0]); fc.append(fv[m, j]); fw.append(1.0 / k[m])
    FP = sp.csr_matrix((np.concatenate(fw), (np.concatenate(fr), np.concatenate(fc))), shape=(F, n))
    # --- edge -> adjacent faces
    ef_face = np.repeat(np.arange(F), 4).reshape(F, 4)
    valid = fe >= 0
    e_of, f_of = fe[valid], ef_face[valid]
    nface = np.bincount(e_of, minlength=E)
    EF = sp.csr_matrix((np.ones(len(e_of)), (e_of, f_of)), shape=(E, F))
    interior = nface == 2
    MID = sp.csr_matrix((np.full(2 * E, 0.5), (np.repeat(np.arange(E), 2), edges.ravel())), shape=(E, n))
    # interior edge point: (a + b + f1 + f2) / 4 = 0.5*mid + 0.25*(f1+f2)
    Ei = sp.diags(interior.astype(float))
    EP = sp.diags(np.where(interior, 0.5, 1.0)) @ MID + 0.25 * (Ei @ EF @ FP)
    # --- vertex points
    boundary_e = nface == 1
    # boundary neighbours
    be = edges[boundary_e]
    nb_count = np.bincount(be.ravel(), minlength=n)
    is_bv = nb_count > 0
    # valence (edges) and incident faces per vertex
    val = np.bincount(edges.ravel(), minlength=n).astype(float)
    VF = sp.csr_matrix((np.ones(int(k.sum())), (np.concatenate([fv[j < k, j] for j in range(4)]),
                                                 np.concatenate([np.nonzero(j < k)[0] for j in range(4)]))), shape=(n, F))
    nf = np.asarray(VF.sum(1)).ravel()
    VE = sp.csr_matrix((np.ones(2 * E), (edges.ravel(), np.repeat(np.arange(E), 2))), shape=(n, E))
    # interior rule: (Favg + 2 Ravg + (m-3) P) / m, m = valence
    m = np.maximum(val, 1)
    Favg = sp.diags(1.0 / np.maximum(nf, 1)) @ VF @ FP
    Ravg = sp.diags(1.0 / m) @ VE @ MID
    I = sp.identity(n, format="csr")
    Vint = sp.diags(1.0 / m) @ Favg + sp.diags(2.0 / m) @ Ravg + sp.diags((m - 3) / m) @ I
    # boundary rule: 3/4 P + 1/8 (a + b)   (only for vertices with exactly two boundary edges)
    VBE = sp.csr_matrix((np.ones(2 * len(be)), (be.ravel(), be[:, ::-1].ravel())), shape=(n, n))
    two = nb_count == 2
    Vbnd = sp.diags(np.where(two, 0.75, 1.0)) @ I + sp.diags(np.where(two, 0.125, 0.0)) @ VBE
    used = val > 0
    VP = sp.diags((used & ~is_bv).astype(float)) @ Vint + sp.diags(is_bv.astype(float)) @ Vbnd \
        + sp.diags((~used).astype(float)) @ I
    S = sp.vstack([VP, EP, FP]).tocsr()
    fv2 = _quads(fv, k, fe, n, E)
    # --- UVs: linear, face-varying
    U, uedges, ufe = _linear_face_varying(fuv, k, n_uvs)
    fuv2 = _quads(fuv, k, ufe, n_uvs, len(uedges))
    return S, fv2, U.tocsr(), fuv2

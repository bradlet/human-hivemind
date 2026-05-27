---
order: 3
title: Eigenvalues and Eigenvectors
estimated_minutes: 35
learning_objectives:
  - Define eigenvalue and eigenvector and explain why they are useful
  - Compute eigenvalues of a 2x2 matrix by hand
  - Sketch how diagonalization simplifies repeated application of a linear map
---

# Eigenvalues and Eigenvectors

An **eigenvector** of a square matrix $A$ is a nonzero vector $\vec{v}$ such
that

$$
A \vec{v} = \lambda \vec{v}
$$

for some number $\lambda$, called the **eigenvalue**. In words: $A$ doesn't
rotate $\vec{v}$, it only stretches or flips it.

Eigenvectors are the "natural directions" of a linear map. Once you know
them, repeated application of $A$ is easy: along an eigenvector, applying
$A^k$ just scales by $\lambda^k$.

## Finding them

For a 2×2 matrix $A$, the eigenvalues are the roots of the polynomial

$$
\det(A - \lambda I) = 0,
$$

where $I$ is the identity matrix. Substitute each $\lambda$ back into
$(A - \lambda I)\vec{v} = 0$ to recover an eigenvector.

## Diagonalization

If $A$ has $n$ independent eigenvectors, we can write $A = P D P^{-1}$ where
$D$ is diagonal. This makes computing $A^k$ as easy as raising each diagonal
entry to the $k$th power — a trick used everywhere from PageRank to PCA.

## Check your understanding

1. Find the eigenvalues of $\begin{pmatrix} 2 & 0 \\ 0 & 3 \end{pmatrix}$.
2. Why are eigenvectors useful when computing $A^{100}$ for a matrix $A$ that
   you'd otherwise have to multiply by itself 100 times?

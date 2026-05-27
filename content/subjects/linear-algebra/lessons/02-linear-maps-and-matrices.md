---
order: 2
title: Linear Maps and Matrices
estimated_minutes: 30
learning_objectives:
  - Define a linear map and verify the two linearity properties
  - Multiply a matrix by a vector to apply a linear map
  - Compose two linear maps by multiplying their matrices
---

# Linear Maps and Matrices

A **linear map** $T$ from one vector space to another preserves the two
operations we care about:

$$
T(\vec{u} + \vec{v}) = T(\vec{u}) + T(\vec{v}), \qquad T(c \cdot \vec{v}) = c \cdot T(\vec{v}).
$$

Every linear map from $\mathbb{R}^n$ to $\mathbb{R}^m$ can be represented as
an $m \times n$ **matrix** $A$. Applying the map is just matrix-vector
multiplication:

$$
T(\vec{v}) = A \vec{v}.
$$

For example, the matrix
$\begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix}$
rotates 2D vectors 90 degrees counterclockwise. Apply it to $(1, 0)$ and you
get $(0, 1)$. Apply it to $(0, 1)$ and you get $(-1, 0)$.

## Composition

If $A$ encodes one transformation and $B$ encodes another, then doing $A$
first and then $B$ is encoded by the **matrix product** $BA$. The order
matters — that's why matrix multiplication is not commutative.

## Check your understanding

1. Write a 2×2 matrix that doubles the $x$-coordinate and leaves $y$ alone.
2. Compute the product of the rotation matrix above with itself. What
   transformation does it represent?

---
order: 2
title: Multi-Layer Networks
estimated_minutes: 30
learning_objectives:
  - Write a forward pass through a 2-layer network as a sequence of matrix multiplies and nonlinearities
  - Explain why depth and width let networks approximate complicated functions
  - State the universal approximation theorem informally
---

# Multi-Layer Networks

Stack two layers of perceptrons. The first computes some **hidden**
representation $\vec{h}$ from the inputs, the second computes the output from
$\vec{h}$:

$$
\vec{h} = \sigma\!\left( W_1 \vec{x} + \vec{b}_1 \right), \qquad
\vec{y} = \sigma\!\left( W_2 \vec{h} + \vec{b}_2 \right).
$$

Here $W_1$ and $W_2$ are matrices of weights — exactly the kind of objects
you met in the linear algebra prerequisite. The whole forward pass is
matrix multiplies separated by elementwise nonlinearities.

## Why depth helps

A two-layer network can already solve XOR: the first layer can rotate inputs
into a basis where the answer *is* linearly separable, and the second layer
makes that linear cut. More generally, the **universal approximation theorem**
says that even a single hidden layer (wide enough) can approximate any
continuous function on a compact domain.

In practice, *deeper* networks generalize better and need exponentially fewer
parameters than equivalently expressive shallow networks. Modern networks
have anywhere from a few layers to thousands.

## Check your understanding

1. Given $W_1 \in \mathbb{R}^{4 \times 3}$ and $W_2 \in \mathbb{R}^{2 \times 4}$,
   what are the dimensions of $\vec{x}$, $\vec{h}$, and $\vec{y}$?
2. Why don't we just keep widening a one-layer network instead of stacking
   layers?

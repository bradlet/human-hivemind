---
order: 1
title: The Perceptron
estimated_minutes: 25
learning_objectives:
  - Describe a perceptron as a weighted sum followed by a nonlinearity
  - Identify why a single perceptron cannot solve XOR
  - Sketch what an activation function does and why it matters
---

# The Perceptron

The simplest building block of a neural network is the **perceptron**: it
takes a vector of inputs $\vec{x} = (x_1, \ldots, x_n)$, weights each by a
learned coefficient $w_i$, sums them with a bias $b$, and runs the result
through a **nonlinearity** $\sigma$:

$$
y = \sigma\!\left( \sum_i w_i x_i + b \right) = \sigma(\vec{w} \cdot \vec{x} + b).
$$

A common choice for $\sigma$ is the **sigmoid**

$$
\sigma(z) = \frac{1}{1 + e^{-z}},
$$

which squashes any real number into the interval $(0, 1)$.

## The XOR problem

A single perceptron can carve a plane into two half-spaces with a single
linear cut. Problems whose answer can be decided that way are called
**linearly separable**, and a perceptron solves them just fine: AND, OR, NOT.

But **XOR** isn't linearly separable. No straight line in the input plane
separates the positive XOR inputs $(0,1)$ and $(1,0)$ from the negative ones
$(0,0)$ and $(1,1)$. To handle XOR — and most interesting problems — you need
more than one layer.

## Check your understanding

1. Why is a nonlinearity essential? What happens if you stack many perceptrons
   with no nonlinearity between them?
2. Sketch the decision boundary of $\sigma(2 x_1 + 3 x_2 - 5)$.

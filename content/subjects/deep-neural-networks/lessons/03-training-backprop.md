---
order: 3
title: Training with Gradient Descent and Backpropagation
estimated_minutes: 40
learning_objectives:
  - Define a loss function and explain why we want to minimize it
  - Describe gradient descent in one sentence and write its update rule
  - Sketch what backpropagation does at a high level
---

# Training with Gradient Descent and Backpropagation

A network with random weights is useless. Training is the process of nudging
each weight to make the network's predictions closer to the truth.

## Loss

We need a single number that captures "how wrong was the network?". This is
the **loss function** $L$. A common choice for regression is the mean squared
error

$$
L = \frac{1}{N} \sum_{i=1}^N (\hat{y}_i - y_i)^2,
$$

and for classification, **cross-entropy**.

## Gradient descent

If we know the gradient $\nabla_\theta L$ of the loss with respect to the
parameters $\theta$, we can take a small step downhill:

$$
\theta_{t+1} = \theta_t - \eta \, \nabla_\theta L,
$$

where $\eta$ is the **learning rate**. Repeat many times. That's it. The
hard part is *computing* the gradient.

## Backpropagation

**Backpropagation** is the chain rule, applied efficiently to a layered
network. Conceptually:

1. Forward pass: compute the loss given the current weights.
2. Backward pass: for each layer from output to input, compute how much the
   loss would change for a small change in that layer's outputs, then chain
   it back to compute the change with respect to the weights.

Modern deep-learning frameworks like PyTorch and JAX do this automatically.
But the underlying recipe is just calculus and matrix multiplications —
nothing more.

## Check your understanding

1. If the learning rate is too large, what tends to go wrong?
2. Why is backpropagation more efficient than computing each weight gradient
   by hand from scratch?

# Subject: Deep Neural Networks

## What this subject teaches
- A neural network is a function approximator built from layered linear+nonlinear units.
- A single perceptron is a weighted sum followed by a nonlinearity; it can only solve linearly separable problems.
- Stacking layers with nonlinearities yields universal function approximation (UAT).
- Training optimizes parameters via gradient descent on a loss function (MSE for regression, cross-entropy for classification).
- Backpropagation is the chain rule applied efficiently through the computation graph to obtain weight gradients.

## Prerequisites assumed
- Linear algebra: vectors, matrices, matrix-vector products
- Comfort with basic calculus (derivatives, chain rule) is helpful but not required for the high-level course
- Programming experience helps when you implement networks, but is not required to follow the lessons

## Key concepts (with one-line definitions)
- Perceptron: w . x + b passed through a nonlinearity sigma.
- Sigmoid: sigma(z) = 1 / (1 + e^-z).
- Hidden layer: an intermediate vector of activations between input and output, h = sigma(W x + b).
- Universal approximation theorem: a single sufficiently wide hidden layer can approximate any continuous function on a compact domain.
- Loss function: scalar measure of how wrong the network's predictions are (e.g., MSE, cross-entropy).
- Gradient descent: theta_{t+1} = theta_t - eta * grad L; iteratively descends the loss surface.
- Backpropagation: efficient algorithm that applies the chain rule layer-by-layer to compute weight gradients.
- Learning rate: step size eta in the gradient descent update; too large diverges, too small is slow.

## How this connects to other subjects
- Builds on: Linear Algebra (matrix operations), Multivariable Calculus (chain rule)
- Leads to: Convolutional Neural Networks, Transformers, Reinforcement Learning, Modern Generative Models

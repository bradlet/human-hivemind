---
order: 1
title: Vectors and Vector Spaces
estimated_minutes: 25
learning_objectives:
  - Define a vector in terms of magnitude and direction
  - Identify when a set of vectors forms a vector space
  - Compute vector addition and scalar multiplication geometrically and componentwise
---

# Vectors and Vector Spaces

A **vector** is an object with both *magnitude* and *direction*. In two
dimensions you can think of one as an arrow drawn from the origin to a point
$(x, y)$ in the plane:

$$
\vec{v} = (x, y).
$$

We can do two basic operations with vectors:

1. **Vector addition.** $(1, 2) + (3, 1) = (4, 3)$. Geometrically: place the
   tail of one arrow at the head of the other.
2. **Scalar multiplication.** Multiplying by a number stretches or shrinks the
   vector: $2 \cdot (1, 2) = (2, 4)$.

A **vector space** is any collection of objects where these two operations are
defined and behave nicely (they're associative, commutative, have a zero
element, etc.). The set of all 2D arrows is a vector space. So is the set of
all polynomials of degree at most 3 — once you decide what "addition" and
"scalar multiplication" mean for polynomials, the same rules carry over.

The big insight: anywhere we can add things and scale things, we can use the
machinery of linear algebra.

## Check your understanding

1. Is the set of all points $(x, y)$ with $x \geq 0$ a vector space? Why or
   why not?
2. Compute $3 \cdot (2, -1) + (-1, 4)$.
3. Name one vector space you've used today that *isn't* arrows in space.

# The Rotating DinnOR Problem

By Evertjan Peer and Cascha van Wanrooij

## Setup
Make sure to have [poetry](https://python-poetry.org) installed (e.g. `brew install poetry`)

```bash
poetry install
poetry run python3 dinnor/solve.py
poetry run python3 dinnor/verify.py
```

## Original request
Organize a rolling dinner schedule with the following rules:
- Always have a different group composition for each course.
- Do not cook the same dish as last year.
- Aim to dine with as many different guests as possible compared to last year.

## Problem Description
The Rotating DinnOR Problem involves assigning N addresses into groups of three across different sections (courses) while considering historical pairings and previous section assignments. The goal is to minimize the reuse of historical pairs of people who have dined together before and to make sure no body cooks the same course as the year before.

## Parameters
- Let $N = 69$ be the number of addresses/people that participate this year
- Let $\text{SECTIONSIZE} = 23$ be the size of each section (course)
- Let $H$ be the set of historical pairs $(i,j)$ that have dined together before
- Let $P_i$ be the previous section assignment for person $i$ (if it exists)
- Let $T$ be the set of all valid triplets $(i,j,k)$ where $i,j,k \in \{1,\ldots,N\}$ and $i \neq j \neq k$

Additionally, we use that
- For each triplet $T$, in the final solution, position 0 indicates the address that cooks (and hosts) for that triplet.
- The position at which a triplet is, determines which course the first address will host: 0-22: starter, 23-45: main, 46-68 dessert

## Decision Variables
1. For each triplet $t \in T$ and position $p \in \{0,\ldots,N-1\}$:
1. For each triplet $t \in T$ and position $p \in \{0,\ldots,N-1\}$:
  $x_{t,p} = 1$ if triplet $t$ is assigned to position $p$, and $0$ otherwise

2. For each triplet $t \in T$:
  $y_t = 1$ if triplet $t$ is used in the solution, and $0$ otherwise

3. For each historical pair $h \in H$:
  $h_{\text{used}} = 1$ if historical pair is reused, and $0$ otherwise

## Objective Function
Minimize the number of historical pairs that are reused:

$$\min \sum_{h \in H} h_{\text{used}}$$

## Constraints

1. Each triplet assigned to exactly one position if used:
   $$\forall t \in T: \sum_{p=0}^{N-1} x_{t,p} = y_t$$

2. Each position must be assigned exactly one triplet:
   $$\forall p \in \{0,\ldots,N-1\}: \sum_{t \in T} x_{t,p} = 1$$

3. Each person must appear in exactly three triplets:
   $$\forall i \in \{1,\ldots,N\}: \sum_{t \in T: i \in t} y_t = 3$$

4. Each person must appear exactly once in each section:
   $$\forall i \in \{1,\ldots,N\}, \forall s \in \{0,1,2\}: \sum_{\substack{t \in T: i \in t \\ p \in [s\cdot\text{SECTIONSIZE}, (s+1)\cdot\text{SECTIONSIZE}-1]}} x_{t,p} = 1$$

5. Each person must be the host (first position in triplet) exactly once:
   $$\forall i \in \{1,\ldots,N\}: \sum_{t \in T: t[0]=i} y_t = 1$$

6. Each pair of people can appear together at most once:
   $$\forall (i,j) \in \binom{N}{2}: \sum_{t \in T: i,j \in t} y_t \leq 1$$

7. Historical pairs tracking (if applicable):
   $$\forall (i,j) \in H: \sum_{t \in T: i,j \in t} y_t \leq h_{\text{used}}$$

8. Previous section constraint (if applicable) (not cooking the same dish as last year):
   $$\forall i \in \{1,\ldots,N\} \text{ with previous section } P_i:$$
   $$\sum_{\substack{t \in T: t[0]=i \\ p \in [(P_i-1)\cdot\text{SECTIONSIZE}, P_i\cdot\text{SECTIONSIZE}-1]}} x_{t,p} = 0$$

## Additional Notes
The problem uses OR-Tools CP-SAT solver with:
   - 60-minute timeout
   - 8 parallel search workers

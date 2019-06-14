---
layout: post
title: "Neural Network Compiler (NNC)"
author: "Dheeraj R. Reddy"
categories: journal
tags: [machine learning, compiler]
---

This was the documentation for a project I completed as part of my compilers class. It's a language to define neural networks, which is then optimized and compiled into efficient executable C++ code. The code of the compiler needs some refining, and will be released shortly. Also, note that the entire project was completed in around 48 hours, so forgive any errors and lack of foresight.

---

Input to the compiler is a `.nnc` file. The file is divided into two sections:
  1. Model properties
  2. Model definition

### Model Properties

Each property of the model is preceded by `~`. Currently the following
properties are available:
  1. NAME: Name of the network
  2. DTYPE: Data type of the network (float16, float32, float64)
  3. BATCH_SIZE
  4. LOSS: Loss function to be minimized (crossentropy, l2, abs)
  5. OPTIMIZER: Optimizer (SGD(lr), MOMENTUM(lr, mom))

Example of model properties:

```
~NAME: example_neural_network
~DTYPE: float32
~BATCH_SIZE: 64
~LOSS: crossentropy
~OPTIMIZER: SGD(0.1)
```

### Model Definition

With the propeties of the model finished, we need to now define the model.

Every tensor in the definition has `@` before the name, and every tensor has
`BATCH_SIZE` as the 0-th dimension. All other variables are considered scalars
if they don't have `@` preceding it.

Only single input and single output networks are supported.

#### Primitive Modules

NCC has some modules defined that can directly emit machine code:
  1. @: DENSE(@, shape:1)
  2. @: ACTIVATION(@, relu/softmax/sigmoid/tanh)
  3. @: ELEMWISE(@, scalar, add/sub/mul/div/mod)
  4. @: DROPOUT(@, scalar)
  5. @: INPUT(shape:n)
  6. OUTPUT(@)
  7. @: TRANSPOSE(@, shape:n)
  8. @: REDUCE(@, axis, sum/mul)
  9. @: CONCAT(@, @)
  10. @: CONV2D(@, (shape:3), scalar, same/none)

Example of model definition:
```
@A: INPUT({28*28})
@B: DENSE(@A, (100))
@C: ACTIVATION(@B, relu)
@R: DROPOUT(@C, d)
@D: DENSE(@R, (10))
@E: ACTIVATION(@D, softmax)
OUTPUT(@E)
```

#### Preprocessor

All mathematical operations that need to be evaluated prior to compilation
can be wrapped in `{mathematical_op}`. You can assign values to scalar in
preprocessors.

Example:
```
{a = 12}
{b = a + 1}
@A: DENSE(@B, ({a * b})
```

#### Block

We can define a reusable module as a composition of primitive module as a single
block in the following way:

```
block BLOCK_NAME(@tensor1, @tensor2, param1, param2) [
  ...
  spit @OUT
]
```

where `spit` is used to define the output of a `block`. A block can only
spit a single tensor. A block can take any number of tensors and scalars
as params. No preprocessor operations are allowed in a block.

#### Comments

`!` is used for single line comments.

No multiline comments are supported.

#### Output

You can compile a network using the following command:
```
nncgo filename.nnc
```

This generates two files: `filename.h` and `filename.so`.

`filename.h` will have a class called the same as given in `~NAME` property.

You can instantiate an object of a class which creates the weight matrices
required. If `filename.h5` is in the same directory, the weights are
loaded from a file.

The class has the following methods:
  1. `forward()`
  2. `minimize()`
  3. `finalize()`

#### forward()
Takes a tensor as input, and returns a tensor as a output.

#### minimize()
Takes a tensor as input, and returns the loss as output. Performs one step
of optimization.

#### finalize()
Writes the weight matrices into `filename.h5`, which can be loaded up for
later.

### Steps during compilation

The `.nnc` file goes through multiple phases:
  1. Preprocessor operations
  2. Block replacement
  3. Graph generation
  4. Graph optimization
  5. High-level code generation (C++)
  6. Use LLVM to generate machine code


#### Preprocessor operations
Uses inline python to compute all the preprocessor operations.

#### Block replacement
Expands each `block` call into a pure module definition. A pure module definition
uses only primitive blocks without any `blocks` or `preprocessors`. This is written
to a `.nccpure` file.

#### Graph Generation
We use `flex` and `bison` to convert a `.nccpure` into a DAG where each
edge is an operation, and each node is the intermediate tensor result.

#### Graph optimization
We optimize the graph by fusing operations that are faster, and we remove
dead end operations that aren't used for the calculation of output tensor.
Example: consecutive matmuls, consecutive transposes, matmul+transpose, etc.

#### High-level code generation (C++)
We generate C++ code using the optimized graph as well as model properties.
We make calls to BLAS functions for various primitive modules. The various
functions are also generated along with functionality to load and store
weights.

#### Use LLVM to generate machine code
The generated C++ file is compiled using LLVM (clang) into the final `.h` and
`.so` files.

### Implementation

`.nnc` to `.nncpure` convertion is done using python.

`.nncpure` to machine code is done using C++ along with flex and bison.

Most of the BLAS operations are self-implementated, but it can be easily replaced
with faster alternatives such as Intel MKL or OpenBLAS. We can extend this
further to use CUDA/CuDNN or OpenCL.

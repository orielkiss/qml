r"""
ZX calculus
===========

.. meta::
    :property="og:description": Investigation of ZX calculus and its applications to quantum computing
    :property="og:image": https://pennylane.ai/qml/_images/zx.png

*Author: Romain Moyard. Posted: April 2023.*


The ZX calculus is a graphical language for reasoning about quantum computations and circuits. It was introduced in
2008 by Coecke and Duncan [#Coecke]_ . It can represent any linear map, and can be considered a diagrammatically
complete generalization of the usual circuit representation. The ZX calculus is based on category theory, an approach
to mathematics which studies objects in terms of their relations rather than in isolation. Thus, the ZX calculus
provides a rigorous way to understand the structure underlying quantum problems, using the link between quantum
operations rather than the operations themselves.

In this tutorial, we first give an overview of the building blocks of the ZX calculus, called <i>ZX-diagrams</i>, and
the rules for transforming them, called <i>rewriting rules</i>. We will then apply them to optimize the number of
T-gates of a benchmark circuit with PennyLane and PyZX [#PyZX]_. We also show that simplifying (reducing) a ZX-diagram
does not always end up with diagram-like graph, and that circuit extraction is a main pain point of the ZX framework.
Finally, we show how ZX calculus can prove the parameter-shift rule .

ZX-diagrams
-----------
This introduction follows the works of the [#East2021]_ and [#JvdW2020]_ . Our goal is to introduce a complete language
for quantum information, for that we need two elements, the ZX-diagram and their rewriting rules. We start by
introducing ZX-diagrams, a graphical depiction of a tensor network representing an arbitrary
linear map. Later, we will introduce ZX rewriting rules, which together with diagrams defines the ZX calculus.

A ZX-diagram is an undirected multi-graph; you can move vertices without affecting the underlying
linear map. The vertices are called Z and X spiders, and represent two kind of linear maps. The edges are called
wires, and represent the dimensions on which the linear maps are acting. Therefore, the edges represent qubits in
quantum computing. The diagram's wires on the left are called inputs, the one leaving on the right are called outputs.

The first building block of the ZX-diagram is the Z spider. In most of the literature, it is depicted as a green vertex.
The Z spider takes a real phase :math:`\alpha \in \mathbb{R}` and represents the following linear map (it accepts any
number of inputs and outputs):

.. figure:: ../demonstrations/zx_calculus/z_spider.jpeg
    :align: center
    :width: 70%

    The Z-spider.

It is easy to see that the usual Z-gate can be represented with a single-wire Z-gate:

.. figure:: ../demonstrations/zx_calculus/z_gate.jpeg
    :align: center
    :width: 70%

    The Z-gate.


As you've probably already guessed, the second building block of the ZX-diagram is the X spider. It is usually depicted
as a red vertex. The X spider also takes a real phase :math:`\alpha \in \mathbb{R}` and it represents the following
linear map (it accepts any number of inputs and outputs):

.. figure:: ../demonstrations/zx_calculus/x_spider.jpeg
    :align: center
    :width: 70%

    The X spider.

It is easy to see that the usual X-gate can be represented with a single-wire X-gate:

.. figure:: ../demonstrations/zx_calculus/x_gate.jpeg
    :align: center
    :width: 70%

    The X gate.

From ordinary quantum theory, we know that the Hadamard gate can be decomposed into X and Z rotations, and can therefore
be represented in ZX calculus. In order to make the diagram easier to read, we introduce the Hadamard gate as a yellow box:

.. figure:: ../demonstrations/zx_calculus/hadamard_gate.png
    :align: center
    :width: 70%

    The Hadamard gate as a yellow box and its decomposition.

This yellow box is also often represented as a blue edge in order to further simplify the display of the diagram.
Below, we will discuss a generalization of the yellow box to a third spider, forming the ZXH calculus.
The yellow box allows us to write the relationship between the X and Z spider as

.. figure:: ../demonstrations/zx_calculus/hxhz.png
    :align: center
    :width: 70%

    How to transform an X spider to a Z spider with the Hadamard gate.

.. figure:: ../demonstrations/zx_calculus/hzhx.png
    :align: center
    :width: 70%

    How to transform an Z spider to a X spider with the Hadamard gate.

A special case of the Z and X spiders are diagrams with no inputs (or outputs). They are used to represent state which
are unnormalized. If a spider has no inputs and outputs, it simply represents a complex scalar.

The phases are :math:`2\pi` periodic, and when a phase is equal to :math:`0`, we omit the zero symbol from the spider.
A simple green node is a Z spider with zero phase and a simple red node is an X spider with zero phase.

You can find the usual representation of quantum states below:

.. figure:: ../demonstrations/zx_calculus/zero_state_plus_state.jpeg
    :align: center
    :width: 70%

    The zero state and zero state.

Similarly, you get the :math:`\vert 1\rangle` state and :math:`\vert -\rangle` state by replacing the zero phase with
:math:`\pi`.

Now that we have these two basic building blocks, we can start composing them and stacking them on top of each other.
Composition consists in joining the outputs of a first diagram to the inputs of a second diagram. Stacking two ZX
diagrams on top of each other represents the tensor product of the corresponding tensors.


We illustrate the rules of stacking and composition by building an equivalent CNOT gate (up to a global phase). We first
start by stacking a phaseless Z spider with one input wire and two output wires with a single wire. We show the
ZX-diagram and corresponding matrix below:

.. figure:: ../demonstrations/zx_calculus/stack_z_w.png
    :align: center
    :width: 70%

    Phaseless Z with one input wire and two output wires stacked with a single wire.

Next, we stack a single wire with a phaseless X spider with two input wires and single output wire. Again, we provide
the matrix:

.. figure:: ../demonstrations/zx_calculus/stack_w_x.png
    :align: center
    :width: 70%

    Single wire stacked with a X phaseless spider with two inputs wires and one output wire.

Finally, we compose the two diagrams, meaning that we join the two output of the first diagram with the two inputs of
the second diagram. By doing this we obtain a CNOT gate, you can convince yourself by applying the matrix multiplication
between the two diagrams.

.. figure:: ../demonstrations/zx_calculus/compose_zw_wx.png
    :align: center
    :width: 70%

    The composition of the two diagrams is a CNOT gate.

We've already mentioned that a ZX-diagram is an undirected multi-graph. The position of the vertices
does not matter, nor does the trajectory of the wires. We can move vertices around, and bend,
unbend, cross, and uncross wires, as long as the connectivity and the order of the inputs and outputs is
maintained.
(In particular, bending a line so that it changes direction from left to right, or vice-versa, is not allowed.)
None of these deformations affects the underlying linear map, meaning that ZX-diagrams have all sorts of
<i>topological</i> symmetries. For instance, the two following diagrams are the same, and both represent the CNOT gate:

.. figure:: ../demonstrations/zx_calculus/cnot_moved.jpeg
    :align: center
    :width: 70%

    The composition of the two diagrams is a CNOT gate.

This means that we can draw a vertical line without ambiguity, which is the usual way of representing the CNOT gate:

.. figure:: ../demonstrations/zx_calculus/cnot.jpeg
    :align: center
    :width: 70%

    Usual representation of the CNOT gate as a ZX-diagram.


We've just shown that we can express any Z rotation and X rotation with the two spiders. Therefore, it is sufficient to
create any one-qubit rotation on the Bloch-sphere, therefore any one-qubit state. By composition and stacking, we can
also create the CNOT gate. Therefore, we have a universal gate set, and we can represent any unitary on any
Hilbert space. We can also create the zero state of any size. Therefore, we can represent any quantum state.
Normalization may be needed (e.g. for the CNOT gate) and we perform this by adding complex scalar vertices.

It turns out that the ability to represent an arbitrary state implies the ability to represent an arbitrary linear map.
Using a mathematical result called the Choi-Jamiolkowski isomorphism, for any linear map :math:`L` from :math:`n` to
:math:`m` wires, we can bend the incoming wires to the right, and find an equivalent state on :math:`n + m`
wires [#JvdW2020]_. Thus, any linear map is equivalent to some state, and since we can create any state, we can create
any map! This shows that ZX-diagrams are a universal tool for reasoning about linear maps. But this doesn't mean the
representation is simple!

For a more in depth introduction, see [#Coecke]_ and [#JvdW2020]_.

ZX calculus: rewriting rules
----------------------------
ZX-diagrams coupled with rewriting rules form what is called the ZX calculus. Previously, we presented the rules
for composition and stacking of diagrams, and talked about the topological symmetries corresponding to deformations. In
this section, we provide rewriting rules that can be used to simplify diagrams without changing the underlying linear
map. This can be very useful for quantum circuit optimization, and for showing that some computations have a very
simple form in the ZX framework (e.g. teleportation).

In the following rules the colours are interchangeable.

0. Since X gate and Z gate do not commute, non-phaseless vertices of different color do not commute.

1. The fuse rule applies when two spiders of the same type are connected by one or more wires. We can fuse spiders by
simply adding the two spider phases and removing the connecting wires.

.. figure:: ../demonstrations/zx_calculus/f_rule.jpeg
    :align: center
    :width: 70%

    The (f)use rule.

2. The :math:`\pi`-copy rule describes how to pull an X gate through a Z spider (or a Z gate with an X spider). Since
X and Z anticommute, pulling the X gate through a Z spider introduces a minus sign into the Z phase.

.. figure:: ../demonstrations/zx_calculus/pi_rule.jpeg
    :align: center
    :width: 70%

    The :math:`\pi`-copy rule.

3. The state copy rule captures how simple one-qubit states interact with a spider of the opposite colour. It is only
valid for states that are multiple of :math:`\pi`, so we have computational basis states (in the X or Z basis).
Basically, if you pull a basis state through a spider of the opposite color, it simply copies it onto each outgoing
wire.

.. figure:: ../demonstrations/zx_calculus/c_rule.jpeg
    :align: center
    :width: 70%

    The state (c)opy rule.

4. The identity rule states that phaseless spiders with one input and one input are equivalent to the identity and
therefore can be removed. This is similar to the rule that Z and X rotation gates which are phaseless are equivalent
to the identity.  This rule provides a way to get rid of self-loops.

.. figure:: ../demonstrations/zx_calculus/id_rule.jpeg
    :align: center
    :width: 70%

    The (id)entity removal rule.

5. A bialgebra is a mathematical structure with a product (combining two wires into one) and a coproduct (splitting a
wire into two wires) where, roughly speaking, we can pull a product through a coproduct at the cost of doubling. This
is similar to the relation enjoyed by the XOR algebra and the COPY coalgebra. This rule is not straightforward to
verify and details can be found in this paper [#JvdW2020]_ .

.. figure:: ../demonstrations/zx_calculus/b_rule.jpeg
    :align: center
    :width: 70%

    The (b)ialgebra rule.

6. The Hopf rule is a bit like the bialgebra rule, telling us what happens when we try to pull a coproduct through a
product. Instead of doubling, however, in this case they decouple, leaving us with an unconnected projector and
state. Again, this relation is satisfied by XOR and COPY, and the corresponding algebraic structure is called a Hopf
algebra. This turns out to follow from the bialgebra and the state copy rule [#JvdW2020]_, but it's useful to record
it as a separate rule.

.. figure:: ../demonstrations/zx_calculus/hopf_rule.jpeg
    :align: center
    :width: 70%

    The (ho)pf rule.


Teleportation example:
----------------------

Now that we have all the necessary tools, let's see how to describe teleportation as a ZX-diagram and simplify it
with our rewriting rules. The results are surprisingly elegant! We follow the explanation from [#JvdW2020]_ .

Teleportation is a protocol for transferring quantum information (a state) from Alice (the sender) to Bob (the
receiver). To perform this, Alice and Bob first need to share a maximally entangled state. The protocol for Alice to
send her quantum state to Bob is then as follows:

1. Alice applies the CNOT gate followed by the Hadamard gate.
2. Alice measures the two qubits that she has.
3. Alice sends the two measurement results to Bob.
4. Given the results, Bob conditionally applies the Z and X gate to his qubit.
5. Bob ends up with the same state as Alice previously had. Teleportation is complete!

In the ordinary quantum circuit notation, we can summarize the procedure as follows:

.. figure:: ../demonstrations/zx_calculus/teleportation_circuit.png
    :align: center
    :width: 70%

    The teleportation circuit.

Let us convert this quantum circuit into a ZX-diagram. The measurements are represented by the state X-spider
parametrized with boolean parameters :math:`a` and :math:`b`. The cup represents the maximally entangled state shared
between Alice and Bob, and as you might expect from earlier comments about bending wires, is the state
Choi-Jamiolkowski equivalent to the identity linear map.

.. figure:: ../demonstrations/zx_calculus/teleportation.png
    :align: center
    :width: 70%

    The teleportation ZX diagram. TODO remove all figures except the first one

Let's simplify the diagram by applying some rewriting rules. The first step is to fuse the :math:`a` state with the
X-spider of the CNOT. We also merge the Hadamard gate with the :math:`b` state, because together it represents a
Z-spider. Then we can fuse the three Z-spiders by simply adding their phases. After that we see that the Z-spider
phase vanishes modulo of :math:`2\pi` and can therefore be simplified using the identity rules. Then we can fuse the
two X-spiders by adding their phase. We notice that the phase again vanishes modulo :math:`2\pi` and we can get rid
of the last X-spider. Teleportation is a simple wire connecting Alice and Bob!

.. figure:: ../demonstrations/zx_calculus/teleportation.png
    :align: center
    :width: 70%

    The teleportation simplification.


ZXH-diagrams
------------

The universality of the ZX calculus does not guarantee the existence of a simple representation, even for simple
linear maps. For example, the Toffoli gate (quantum AND gate) requires around 25 spiders! This motivates the
introduction of a new generator: the multi-leg H-box, defined as follows:

.. figure:: ../demonstrations/zx_calculus/h_box.png
    :align: center
    :width: 70%

    The H-box.

The parameter :math:`a` can be any complex number, and the sum  is over all :math:`i1, ... , im, j1, ... , jn \in {0,
1}`, therefore an H-box represents a matrix where all entries are equal to :math:`1`, except for the bottom right
element, which is \ :math:`a`. This will allow us to concisely express the Toffoli gate, as we will see shortly.

An H-box with one input wire and one output wire, with :math:`a=-1`, is a Hadamard gate up to global phase. Thus,
we omit the parameter when it is equal to :math:`-1`. The Hadamard gate is sometimes represented by a blue edge
rather than a box.

Thanks to the introduction of the multi-leg H-box, the Toffoli gate can be represented with three Z spiders and three
H-boxes — two simple Hadamard gates and one three-ary H-box — as shown below:

.. figure:: ../demonstrations/zx_calculus/toffoli.png
    :align: center
    :width: 70%

    Toffoli

The ZXH-calculus contains a new set of rewriting rules. You can find details in the literature
[#East2021]_.


ZX-diagrams with PennyLane
--------------------------

Now that we have introduced the formalism of the ZXH calculus, let's dive into some code and show what you can do
with PennyLane! PennyLane release 0.28.0 added ZX calculus functionality to the language. You can use the `to_zx`
transform decorator to get a ZXH-diagram from a PennyLane QNode, and also the `from_zx` to transform a ZX-diagram to
a PennyLane tape.  We are using the PyZX library [#PyZX]_ under the hood to represent the ZX diagram. Once your
circuit is a PyZX graph, you can draw it, apply some optimization, extract the underlying circuit and go back to
PennyLane.

Let's start with a very simple circuit consisting of three gates and show that you can represent the QNode as a
PyZX diagram:
"""

import matplotlib.pyplot as plt

import pennylane as qml
import pyzx

dev = qml.device("default.qubit", wires=2)


@qml.transforms.to_zx
@qml.qnode(device=dev)
def circuit():
    qml.PauliX(wires=0),
    qml.PauliY(wires=1),
    qml.CNOT(wires=[0, 1]),
    return qml.expval(qml.PauliZ(wires=0))


g = circuit()

######################################################################
# Now that you have a ZX-diagram as a PyZx object, you can use all the tools from the library to transform the graph.
# You can simplify the circuit, draw it and get a new understanding of your quantum computation.
#
# For example, you can use the matplotlib drawer to get a visualization of the diagram. The drawer returns a matplotlib
# figure and therefore you can save it locally with `savefig` function, or simply show it locally.


fig = pyzx.draw_matplotlib(g)

# The following lines are added because the figure is automatically closed by PyZX.
manager = plt.figure().canvas.manager
manager.canvas.figure = fig
fig.set_canvas(manager.canvas)

plt.show()

######################################################################
# You can also take a ZX-diagram in PyZX, convert it into a PennyLane tape and use it in your QNode. Invoking the
# PyZX circuit generator:


import random

random.seed(42)
random_circuit = pyzx.generate.CNOT_HAD_PHASE_circuit(qubits=3, depth=10)
print(random_circuit.stats())

graph = random_circuit.to_graph()

tape = qml.transforms.from_zx(graph)
print(tape.operations)

######################################################################
# We get a tape corresponding to the randomly generated circuit which we can use it in any QNode. This
# functionality will be very useful for our next topic: circuit optimization.
#
# Graph optimization and circuit extraction
# -----------------------------------------
#
# The ZX calculus is more general and more flexible than the usual circuit representation. We can therefore represent
# circuits with ZX-diagrams and apply rewriting rules to simplify, like we did for teleportation. But not every
# ZX-diagram has a corresponding circuit. To get back to circuits, a method called circuit extraction is needed. For
# a rigorous introduction to this active and promising field of application, see [#Duncan2017]_. The basic idea is
# captured below:
#
# .. figure:: ../demonstrations/zx_calculus/circuit_opt.png
#     :align: center
#     :width: 70%
#
#     The simplification and extraction of ZX-diagrams.
#
# To simplify ZX-diagrams, we can not only use the rewriting rules defined previously, but additional graph-theoretic
# transformations called local complementation and pivoting. These are special transformations that can only be
# applied to "graph-like" ZX-diagrams. As defined in [#Duncan2017]_ , a ZX-diagram is graph-like if
#
# 1. All spiders are Z-spiders.
# 2. Z-spiders are only connected via Hadamard edges.
# 3. There are no parallel Hadamard edges or self-loops.
# 4. Every input or output is connected to a Z-spider and every Z-spider is connected to at most one input or output.
#
# A ZX-diagram is called a graph state if it is graph-like, every spider is connected to an output, and there are no
# phaseless spiders. Furthermore, it was proved that every ZX-diagram is equal to a graph-like ZX-diagram. Thus,
# after conversion into graph-like form, we can use graph-theoretic tools on all ZX-diagrams.
#
# The basic idea is [#Duncan2017]_ is to use the graph-theoretic transformations to get rid of as many interior
# spiders as possible. Interior spiders are the one without inputs or outputs connected to them. To this end,
# Theorem 5.4 [#Duncan2017]_ provides an algorithm which takes a graph-like diagram and performs the following:
#
# 1. Removes all interior proper Clifford spiders,
# 2. Remove adjacent pairs of interior Pauli spiders,
# 3. Remove interior Pauli spiders adjacent to a boundary spider.
#
# This procedure is implemented in PyZX as the `full_reduce` function. The complexity of the procedure is
# :math:`\mathcal{O}( n^3)`. Let's create an example with the circuit `mod_5_4`:


dev = qml.device("default.qubit", wires=5)


@qml.transforms.to_zx
@qml.qnode(device=dev)
def mod_5_4():
    qml.PauliX(wires=4),
    qml.Hadamard(wires=4),
    qml.CNOT(wires=[3, 4]),
    qml.adjoint(qml.T(wires=[4])),
    qml.CNOT(wires=[0, 4]),
    qml.T(wires=[4]),
    qml.CNOT(wires=[3, 4]),
    qml.adjoint(qml.T(wires=[4])),
    qml.CNOT(wires=[0, 4]),
    qml.T(wires=[3]),
    qml.T(wires=[4]),
    qml.CNOT(wires=[0, 3]),
    qml.T(wires=[0]),
    qml.adjoint(qml.T(wires=[3]))
    qml.CNOT(wires=[0, 3]),
    qml.CNOT(wires=[3, 4]),
    qml.adjoint(qml.T(wires=[4])),
    qml.CNOT(wires=[2, 4]),
    qml.T(wires=[4]),
    qml.CNOT(wires=[3, 4]),
    qml.adjoint(qml.T(wires=[4])),
    qml.CNOT(wires=[2, 4]),
    qml.T(wires=[3]),
    qml.T(wires=[4]),
    qml.CNOT(wires=[2, 3]),
    qml.T(wires=[2]),
    qml.adjoint(qml.T(wires=[3]))
    qml.CNOT(wires=[2, 3]),
    qml.Hadamard(wires=[4]),
    qml.CNOT(wires=[3, 4]),
    qml.Hadamard(wires=4),
    qml.CNOT(wires=[2, 4]),
    qml.adjoint(
        qml.T(wires=[4]),
    )
    qml.CNOT(wires=[1, 4]),
    qml.T(wires=[4]),
    qml.CNOT(wires=[2, 4]),
    qml.adjoint(qml.T(wires=[4])),
    qml.CNOT(wires=[1, 4]),
    qml.T(wires=[4]),
    qml.T(wires=[2]),
    qml.CNOT(wires=[1, 2]),
    qml.T(wires=[1]),
    qml.adjoint(qml.T(wires=[2]))
    qml.CNOT(wires=[1, 2]),
    qml.Hadamard(wires=[4]),
    qml.CNOT(wires=[2, 4]),
    qml.Hadamard(wires=4),
    qml.CNOT(wires=[1, 4]),
    qml.adjoint(qml.T(wires=[4])),
    qml.CNOT(wires=[0, 4]),
    qml.T(wires=[4]),
    qml.CNOT(wires=[1, 4]),
    qml.adjoint(qml.T(wires=[4])),
    qml.CNOT(wires=[0, 4]),
    qml.T(wires=[4]),
    qml.T(wires=[1]),
    qml.CNOT(wires=[0, 1]),
    qml.T(wires=[0]),
    qml.adjoint(qml.T(wires=[1])),
    qml.CNOT(wires=[0, 1]),
    qml.Hadamard(wires=[4]),
    qml.CNOT(wires=[1, 4]),
    qml.CNOT(wires=[0, 4]),
    return qml.expval(qml.PauliZ(wires=0))


g = mod_5_4()
pyzx.simplify.full_reduce(g)

fig = pyzx.draw_matplotlib(g)

# The following lines are added because the figure is automatically closed by PyZX.
manager = plt.figure().canvas.manager
manager.canvas.figure = fig
fig.set_canvas(manager.canvas)

plt.show()

# ##################################################################### We see that after applying the procedure we
# end up with only 16 interior Z-spiders and 5 boundary spiders. We also see that all non-Clifford phases appear on
# the interior spiders. The simplification procedure was successful, but we have a graph-like ZX-diagram with no
# quantum circuit equivalent. We need to extract a circuit!
#
# The extraction of circuits is a highly non-trivial task and can be a #P-hard problem [#Beaudrap2021]_. There are
# two different algorithms introduced in the same paper. First, for Clifford circuits, the procedure will erase all
# interior spiders, and therefore the diagram is left in a graph-state from which a Clifford circuit can be
# extracted, using a total of eight layers with only one layer of CNOTs.
#
# For non-Clifford circuits the problem is more complex, because we are left with non-Clifford interior spiders. From
# the diagram produced by the simplification procedure, the extraction progresses through the diagram from
# right-to-left, consuming on the left and adding gates on the right. It produces better results than other cut and
# resynthesize techniques. The extraction procedure is implement in PyZX as the function
# `pyzx.circuit.extract_circuit`. We can apply this procedure to the example `mod_5_4` above:

circuit_extracted = pyzx.extract_circuit(g)
print(circuit_extracted.stats())

######################################################################
#
# Example: T-count optimization
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# A concrete application of these ZX optimization techniques is the reduction of the expensive, non-Clifford T count
# of a quantum circuit. Indeed, T-count optimization is an area where ZX-calculus has very good results [
# #Kissinger2021]_ .
#
# Let’s start by using with the `mod_5_4` circuit introduced above. The circuit contains :math:`63` gates: :math:`28`
# `qml.T()` gates, :math:`28` `qml.CNOT()`, :math:`6` `qml.Hadamard()` and :math:`1` `qml.PauliX()`. We applied the
# `qml.transforms.to_zx` decorator in order to transform our circuit to a ZX graph. You can get this PyZX graph by
# simply calling the QNode:


g = mod_5_4()
t_count = pyzx.tcount(g)
print(t_count)

######################################################################
# PyZX gives multiple options for optimizing ZX graphs (`pyzx.full_reduce()`, `pyzx.teleport_reduce()`, …). The
# `pyzx.full_reduce()` applies all optimization passes, but the final result may not be circuit-like. Converting back
# to a quantum circuit from a fully reduced graph may be difficult or impossible. Therefore, we instead recommend using
# `pyzx.teleport_reduce()`, as it preserves the diagram structure. Because of this the circuit does not be to be
# extracted. Let's see how it does:


g = pyzx.simplify.teleport_reduce(g)
opt_t_count = pyzx.tcount(g)
print(opt_t_count)

######################################################################
# We have reduced the T count! Taking a full census, the circuit contains :math:`53` gates: :math:`8` `qml.T()` gates,
# :math:`28` `qml.CNOT()`, :math:`6` `qml.Hadmard()`, :math:`1` `qml.PauliX()` and :math:`10` `qml.S()`. We
# successfully reduced the T-count by 20 and have 10 additional S gates. The number of CNOT gates remained the same.
#
# The `from_zx()` transform converts the optimized circuit back into PennyLane format:

qscript_opt = qml.transforms.from_zx(g)

wires = qml.wires.Wires([4, 3, 0, 2, 1])
wires_map = dict(zip(qscript_opt.wires, wires))
qscript_opt_reorder = qml.map_wires(input=qscript_opt, wire_map=wires_map)


@qml.qnode(device=dev)
def mod_5_4():
    for o in qscript_opt_reorder:
        qml.apply(o)
    return qml.expval(qml.PauliZ(wires=0))


######################################################################
#
# Deriving the parameter shift rule
# ---------------------------------
#
# We now move away from the standard use ZX-calculus, in order to show its utility for calculus and more specifically
# for quantum derivatives more specifically for the parameter-shift rule. What follows is not implemented in
# PennyLane or PyZX. By adding derivatives to the framework, it shows that ZX calculus can have a role to play in
# quantum machine learning (QML). After reading this section, you should be convinced that ZX calculus can be used
# to study any kind of quantum related problems.
#
# Indeed, not only ZX-calculus is useful for representing and simplifying quantum circuits, but it was shown that we
# can use it to represent gradients and integrals of parametrized quantum circuits [#Zhao2021]_ . In this section,
# we will follow the proof of the theorem that shows how the derivative of the expectation value of a Hamiltonian
# given a parametrized state can be derived as a ZX-diagram (theorem 2 in the paper [#Zhao2021]_ ). We will also that
# it can be used to prove the parameter-shift rule!
#
# Let's first describe the problem. Without loss of generalisation, let's suppose that we begin with the pure state
# :math:`\ket{0}` on all n qubits. Then we apply a parametrized unitary :math:`U` that depends on :math:`\vec{
# \theta}=(\theta_1, ..., \theta_m)`, where each angle :math:`\theta_i \in [0, 2\pi]`.
#
# Consequently the expectation value of a Hamiltonian :math:`H` is given by:
#
# .. math:: \braket{H} = \bra{0} U(\vec{\theta}) H U(\vec{\theta})^{\dagger} \ket{0}
#
# We have seen that any circuit can be translated to a ZX diagram but once again we want to use the graph-like form (
# see the Graph optimization and circuit extraction section). There are multiple rules that ensure the transformation
# to a graph-like diagram. We replace the 0 state by red phaseless spiders, and we transform the parametrized circuit
# to its graph-like ZX diagram. We call the obtained diagram :math:`G_U(\vec{\theta})`.
#
# .. figure:: ../demonstrations/zx_calculus/hamiltonian_diagram.png
#     :align: center
#     :width: 70%
#
# Now we will investigate what is the partial derivative of the diagram of the expectation value. The theorem is
# the following:
#
# .. figure:: ../demonstrations/zx_calculus/theorem2.png
#     :align: center
#     :width: 70%
#
#     The derivative of the expectation value of a Hamiltonian given a parametrized as a ZX-diagram.
#
# Let's consider a spider that depends on the angle :math:`\theta_j` that is in the partial derivative. The spider
# necessarily appears on both sides, but they have opposite sign angle and inverse inputs/outputs. By simply writing
# their definitions and expanding the formula we obtain:
#
# .. figure:: ../demonstrations/zx_calculus/symmetric_spiders.png
#     :align: center
#     :width: 70%
#
#     Two Z spiders depending on the j-th angle.
#
# Now we have a simple formula where easily can take the derivative:
#
# .. figure:: ../demonstrations/zx_calculus/derivative_symmetric_spiders.png
#     :align: center
#     :width: 70%
#
#     The derivative of two spiders depending on the j-th angle.
#
# The theorem is proved, we just expressed the partial derivative as a ZX-diagram!
#
# This theorem can be used to prove the parameter shift rule. Let's consider the following ansatz that we transform to
# its graph-like diagram. We then apply the previous theorem to get the partial derivative relative to :math:`\theta_1`.
#
# .. figure:: ../demonstrations/zx_calculus/paramshift1.png
#     :align: center
#     :width: 70%
#
#     Preparation for the parameter shift proof.
#
# The second step is to take the X-spider with phase :math:`\pi` and explicitly write the formula :math:`\ket{+}\bra{+} -
# \ket{-}\bra{-}`, we can then separate the diagram into two parts. By recalling the definition of the plus and minus
# states and using the fusion rule for the Z-spider. We obtain the parameter shift rule!
#
# .. figure:: ../demonstrations/zx_calculus/paramshift2.png
#     :align: center
#     :width: 70%
#
#     The parameter shift proof.
#
# Acknowledgement
# ---------------
#
# The author would also like to acknowledge the helpful input of Richard East and the beautiful drawings of Guillermo
# Alonso.
#
#
# References
# ----------
#
# .. [#Coecke]
#
#    Bob Coecke and Ross Duncan. "A graphical calculus for quantum observables."
#    `Oxford <https://www.cs.ox.ac.uk/people/bob.coecke/GreenRed.pdf>`__.
#
# .. [#PyZX]
#
#    John van de Wetering. "PyZX."
#    `PyZX GitHub <https://github.com/Quantomatic/pyzx>`__.
#
# .. [#East2021]
#
#    Richard D. P. East, John van de Wetering, Nicholas Chancellor and Adolfo G. Grushin. "AKLT-states as ZX-diagrams:
#    diagrammatic reasoning for quantum states."
#    `ArXiv <https://arxiv.org/pdf/2012.01219.pdf>`__.
#
#
# .. [#JvdW2020]
#
#    John van de Wetering. "ZX-calculus for the working quantum computer scientist."
#    `ArXiv <https://arxiv.org/abs/2012.13966>`__.
#
# .. [#Duncan2017]
#
#    Ross Duncan, Aleks Kissinger, Simon Perdrix, and John van de Wetering. "Graph-theoretic Simplification of Quantum
#    Circuits with the ZX-calculus"
#    `Quantum Journal <https://quantum-journal.org/papers/q-2020-06-04-279/pdf/>`__.
#
# .. [#Kissinger2021]
#
#    Aleks Kissinger and John van de Wetering. "Reducing T-count with the ZX-calculus."
#    `ArXiv <https://arxiv.org/pdf/1903.10477.pdf>`__.
#
# .. [#Beaudrap2021]
#
#    Niel de Beaudrap, Aleks Kissinger and John van de Wetering. "Circuit Extraction for ZX-diagrams can be #P-hard."
#    `ArXiv <https://arxiv.org/pdf/2202.09194.pdf>`__.
#
# .. [#Zhao2021]
#
#    Chen Zhao and Xiao-Shan Gao. "Analyzing the barren plateau phenomenon in training quantum neural networks with the
#    ZX-calculus" `Quantum Journal <https://quantum-journal.org/papers/q-2021-06-04-466/pdf/>`__.
#
# About the author
# ----------------
# .. include:: ../_static/authors/romain_moyard.txt
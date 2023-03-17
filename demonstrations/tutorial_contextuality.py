"""
Contextuality and inductive bias in quantum machine learning
============================================================

"""


######################################################################
# This demo is based on the article `‘Contextuality and inductive bias in
# quantum machine learning’ <https://arxiv.org/abs/2302.01365>`__ by
# Joseph Bowles, Victoria J Wright, Máté Farkas, Nathan Killoran and Maria
# Schuld. The paper is motivated by the following question:
# 
# *What machine learning problems are quantum computers likely to excel
# at?*
# 
# To find answers, they look to contextuality: a nonclassical phenomenon
# that is exhibited by quantum systems that is necessary for computational
# advantage relative to classical machines. To be a little more specific,
# they focus on the framework of `generalized
# contextuality <https://journals.aps.org/pra/abstract/10.1103/PhysRevA.71.052108>`__
# that was introduced by Robert Spekkens in 2004. The authors find
# learning problems for which contextuality plays a key role, and these
# problems may therefore be good areas where quantum machine learning
# algorithms shine. In this demo we will
# 
# -  Describe a specific example of such a problem that is based on the
#    well known rock, paper scissors game, and
# -  Construct a train a quantum model that is tailored to the symmetries
#    of the problem
# 
# We will make use of JAX throughout to vectorise and just-in-time compile
# certain functions to speed things up. For more information on how to
# combine JAX and pennylane see the pennylane
# `documentation <https://docs.pennylane.ai/en/stable/introduction/interfaces/jax.html>`__.
# 

import jax
import jax.numpy as jnp
import pennylane as qml
import numpy as np

#seeds used for random functions
from jax import random
key = random.PRNGKey(666)
np.random.seed(666)


######################################################################
# The rock, paper, scissors game
# ------------------------------
# 


######################################################################
# The learning problem we will consider involves three people playing a
# variant of the rock, paper, scissors game with a referee.
# 


##############################################################################
# .. figure:: ../demonstrations/contextuality/rps.png
#    :align: center
#    :width: 50%



######################################################################
# The game goes as follows. In each round, a player can choose to play
# either rock (R), paper (P) or scissors (S). Each player also has a
# ‘special’ action. For player 1 it is R, for player 2 it is P and for
# player 3 it is S. The rules of the game are then:
# 
# -  If two players play different actions, then one player beats the
#    other following the usual rule (rock beats scissors, sissors beats
#    paper, paper beats rock).
# -  If two players play the same action, the one who plays their special
#    action beats the other. If neither plays their special action, it is
#    a draw.
# 
# The referee then decides the winners and the losers of that round: the
# winners receive :math:`\$1` and the losers lose :math:`\$1` (we will
# call this their *payoff* for that round). This is done
# probabilistically: if we denote the payoff of player :math:`k` by
# :math:`y_k=\pm1` then
# 
# .. math:: \mathbb{E}(y_k) = \frac{n^k_{\text{win}}-n^k_{\text{lose}}}{2}
# 
# where :math:`n^k_{\text{win}}`, :math:`n^k_{\text{lose}}` is the number
# of players that player :math:`k` beats/loses to in that round. This
# ensures that a player is certain to get a positive (or negative) payoff
# if they beat (or lose) to everyone.
# 
# To make this concrete, we will construct three 3x3 matricies ``A01``,
# ``A02``, ``A12`` which determine the rules for each pair of players.
# ``A01`` contains the expected payoff values of player 0 when playing
# against player 1. Using the rules of the game it looks as follows.
#

##############################################################################
# .. figure:: ../demonstrations/contextuality/rpstable.png
#    :align: center
#    :width: 50%


######################################################################
# The matrices ``A02`` and ``A12`` are define similarly.
# 

A01=np.array([[1,-1,1],[1,-1,-1],[-1,1,0]]) #rules for player 0 vs player 1
A02=np.array([[1,-1,1],[1,0,-1],[-1,1,-1]])
A12=np.array([[0,-1,1],[1,1,-1],[-1,1,-1]])


######################################################################
# We can also define the matrices ``A10``, ``A20``, ``A21``. Since we have
# just switched the order of the players, these matrices are just given by
# the transpose:
# 

A10 = -A01.T #rules for player 1 vs player 0
A20 = -A02.T
A21 = -A12.T


######################################################################
# The data set
# ------------
# 


######################################################################
# The above game ia an example of a zero-sum game: if player 1 beats
# player 2 then necessarily player 2 loses to player 1. This imples
# :math:`\sum_k n^k_{\text{wins}}=\sum_kn^k_{\text{lose}}` and so in every
# round we have
# 
# .. math:: \mathbb{E}(y_1)+\mathbb{E}(y_2)+\mathbb{E}(y_3)=0
# 


######################################################################
# In the zero-sum game litereature it is common to introduce the concept
# of a *strategy*. A strategy is a list of probabilities that a player
# perform each possible action. For example, a strategy for player k is a
# vector
# 
# .. math:: x_k=(P(a_k=R), P(a_k=P), P(a_k=S))
# 
# where :math:`a_k` denotes player :math:`k`\ ’s action. We collect these
# into a strategy matrix X
# 
# .. math::
# 
#    X = \begin{pmatrix}
#        P(a_0=R) & P(a_0=P) & P(a_0=S) \\
#        P(a_1=R) & P(a_1=P) & P(a_1=P) \\
#        P(a_2=P) & P(a_2=P) & P(a_2=S)
#        \end{pmatrix}  
# 
# .
# 


######################################################################
# These strategy matrices will form our input data. Let’s write a function
# to generate a set of strategy matrices.
# 

def get_strat_mats(N):
    """
    Generates N strategy matrices, normalised by row
    """
    X = np.random.rand(N,3,3)
    for i in range(N):
        for k in range(3):
            X[i,k]=X[i,k]/np.sum(X[i,k])
    return X


######################################################################
# The labels in our dataset correspond to payoff values :math:`y_k` of the
# three players. Following the rules of probability we find that if the
# players use strategies :math:`x_1, x_2, x_3` the average values of
# :math:`\langle n_{\text{wins}}^k - n_{\text{lose}}^k \rangle` are given
# by
# 
# .. math:: \langle n_{\text{wins}}^0 - n_{\text{lose}}^0 \rangle  = x_0 \cdot A_{01}\cdot x_1^T+x_0 \cdot A_{02}\cdot x_2^T
# 
# .. math:: \langle n_{\text{wins}}^1 - n_{\text{lose}}^1 \rangle = x_1 \cdot A_{10}\cdot x_0^T+x_1 \cdot A_{12}\cdot x_2^T
# 
# .. math:: \langle n_{\text{wins}}^2 - n_{\text{lose}}^2 \rangle = x_2 \cdot A_{20}\cdot x_0^T+x_2 \cdot A_{21}\cdot x_1^T
# 
# Since
# :math:`\mathbb{E}(y_k) = \frac{n^k_{\text{win}}-n^k_{\text{lose}}}{2}`
# it follows that the probability for player :math:`k` to receive a
# positive payoff is
# 
# .. math:: P(y_k=+1) = \frac{\mathbb{E}(y_k)+1}{2} =  \frac{(\langle n_{\text{wins}}^k - n_{\text{lose}}^k \rangle)/2+1}{2}
# 
# Putting all this together we can write some code to generate the labels
# for our data set.
# 

def payoff_probs(X):
    """
    get the payoff probabilities for each player given a strategy matrix X
    """
    n0 = jnp.matmul(jnp.matmul(X[0],A01),X[1])+jnp.matmul(jnp.matmul(X[0],A02),X[2])
    n1 = jnp.matmul(jnp.matmul(X[1],A10),X[0])+jnp.matmul(jnp.matmul(X[1],A12),X[2])
    n2 = jnp.matmul(jnp.matmul(X[2],A20),X[0])+jnp.matmul(jnp.matmul(X[2],A21),X[1])
    probs = (jnp.array([n0,n1,n2])/2+1)/2
    return probs

#JAX vectorisation
vpayoff_probs = jax.vmap(payoff_probs)

def generate_data(N):
    X = get_strat_mats(N) #strategies
    P = vpayoff_probs(X) #payoff probabilities
    r=np.random.rand(*P.shape) 
    Y = np.where(P>r,1,-1) #sampled payoffs for data labels
    return X, Y, P

X, Y, P = generate_data(1500)


######################################################################
# Note that since strategies are probabilistic mixtures of actions, our
# data labels satsify a zero sum condition
# 
# .. math:: \mathbb{E}(y_1\vert X_i)+\mathbb{E}(y_2\vert X_i)+\mathbb{E}(y_3\vert X_i)=0
# 
# We can verify this using the pay off probability matrix ``P`` that we
# used to sample the labels:
# 

expvals = 2*P-1 #convert probs to expvals
expvals[:10].sum(axis=1) #check first 10 entries


######################################################################
# Interestingly, data strucutres of this kind can be connected to the
# concept of *operational equivalence* in generalized contextuality. We
# won’t cover the details of how this link is made here, so check out the
# research paper if you want to know more.
# 


######################################################################
# The learning problem
# --------------------
# 


######################################################################
# Suppose we are given a data set :math:`\{X_i,\vec{y}_i\}` consisting of
# strategy matrices and payoff values, however we don’t know what the
# underlying game is (that is, we don’t know the players were playing the
# rock, paper scissors game described above). We do have one piece of
# information though: we know the game is zero-sum so that the data
# generation process satsifies
# 
# .. math:: \mathbb{E}(y_0\vert X_i)+\mathbb{E}(y_1\vert X_i)+\mathbb{E}(y_2\vert X_i)=0.
# 
# Can we learn the rock, paper scissors game from this data? More
# precisely, if we are given an unseen strategy matrix
# :math:`X_{\text{test}}` our task is to sample from the three
# distributions
# 
# .. math:: P(y_0\vert X_{\text{test}}), P(y_1\vert X_{\text{test}}), P(y_2\vert X_{\text{test}}).
# 
# Note we are not asking to sample from the joint distribution
# :math:`P(\vec{y}\vert X_{\text{test}})` but the three marginal
# distributions only. This can be seen as an instance of multi-task
# learning, where a single task corresponds to sampling the payoff for one
# of the three players.
# 


######################################################################
# Building inductive bias into a quantum model
# --------------------------------------------
# 


######################################################################
# Here we describe a simple three qubit model to tackle this problem.
# Since we know that the data satisfies the zero sum condition, we aim to
# create a quantum model that also satsifies the condition. That is, like
# the data we want our model to satisfy
# 
# .. math:: \mathbb{E}(y_0\vert X_i)+\mathbb{E}(y_1\vert X_i)+\mathbb{E}(y_2\vert X_i)=0.
# 
# In machine learning, this is called encoding an *inductive bias* into
# the model, and considerations like this are often crucial for good
# generalisation performance. In the paper, it is shown that
# noncontextuality limits the expressivity of learning models that encode
# this inductive bias, which may therefore hinder their performance.
# Luckily for us quantum theory is a contextual theory, so these
# limitations don’t apply to our model!
# 
# The quantum model we consider has the following structure:
#

##############################################################################
# .. figure:: ../demonstrations/contextuality/model.png
#    :align: center
#    :width: 50%


######################################################################
# The parameters :math:`\theta` and :math:`\alpha` are trainable
# parameters of the model, and we will use the three :math:`Z`
# measurements at the end of the circuit to sample the three labels.
# Therefore, if we write the entire circuit as
# :math:`\vert \psi(\alpha,\theta,X)\rangle` the zero sum condition will
# be satisfied if
# 
# .. math:: \langle \psi(\alpha,\theta,X) \vert (Z_0+Z_1+Z_2) \vert \psi(\alpha,\theta,X) \rangle = 0.
# 
# Let’s see how we can create a model class that satisfies this. For
# precise details on the structure of the model, check out Figure 6 in the
# paper. We’ll first look at the parameterised unitary :math:`V_{\alpha}`,
# that we call the *input preparation unitary*. This prepares a state
# :math:`V_\alpha\vert 0 \rangle` such that
# 
# .. math:: \langle 0 \vert V^\dagger_\alpha (Z_0+Z_1+Z_2) V_\alpha\vert 0 \rangle = 0.
# 
# An example of such a circuit is the following.
# 

def input_prep(alpha):
    #This ensures the prepared state has <Z_0+Z_1+Z_2>=0
    qml.Hadamard(wires=0)
    qml.Hadamard(wires=1)
    qml.Hadamard(wires=2)
    qml.RY(alpha[0],wires=0)
    qml.RY(alpha[0]+np.pi,wires=1) 


######################################################################
# The second unitary is a *bias invariant layer*: it preserves the value
# of :math:`\langle Z_0+Z_1+Z_2 \rangle` for all input states into the
# layer. To achieve this, the generators of the unitaries in this layer
# must commute with the operator :math:`Z_0+Z_1+Z_2`. For example the
# operator :math:`X\otimes X + Y\otimes Y + Z\otimes Z` (on any pair of
# qubits) commutes with :math:`Z_0+Z_1+Z_2` and so a valid parameterised
# gate could be
# 
# .. math:: e^{i\theta(X\otimes X\otimes\mathbb{I} + Y\otimes Y\otimes\mathbb{I} + Z\otimes Z\otimes\mathbb{I})}.
# 
# This kind of reasoning is an example of geometric quantum machine
# learning (check out some awesome papers on the subject
# `here <https://arxiv.org/abs/2210.07980>`__ and
# `here <https://arxiv.org/abs/2210.08566>`__). Below we construct the
# bias invariant layer. The variables ``blocks`` and ``layers`` are model
# hyperparameters that we will fix as ``blocks=1`` and ``layers=2``.
# 

blocks=1
layers=2

def swap_rot(weights,wires):
    """
    bias-invariant unitary with swap matrix as generator 
    """
    qml.PauliRot(weights,'XX',wires=wires)
    qml.PauliRot(weights,'YY',wires=wires)
    qml.PauliRot(weights,'ZZ',wires=wires)

def param_unitary(weights):
    """
    A bias-invariant unitary (U in the paper)
    """
    for b in range(blocks):
        for q in range(3):
            qml.RZ(weights[b,q],wires=q)
        qml.PauliRot(weights[b,3],'ZZ',wires=[0,1])
        qml.PauliRot(weights[b,4],'ZZ',wires=[0,2])
        qml.PauliRot(weights[b,5],'ZZ',wires=[1,2])
        swap_rot(weights[b,6],wires=[0,1])
        swap_rot(weights[b,7],wires=[1,2])
        swap_rot(weights[b,8],wires=[0,2])
        
def data_encoding(x):
    """
    S_x^1 in paper
    """
    for q in range(3):
        qml.RZ(x[q],wires=q)

def data_encoding_pairs(x):
    """
    S_x^2 in paper
    """
    qml.PauliRot(x[0]*x[1],'ZZ',wires=[0,1])
    qml.PauliRot(x[1]*x[2],'ZZ',wires=[1,2])
    qml.PauliRot(x[0]*x[2],'ZZ',wires=[0,2])
    
def bias_inv_layer(weights,x):
    """
    The full bias invariant layer.
    """
    #data preprocessing
    x1 = jnp.array([x[0,0],x[1,1],x[2,2]])
    x2 = jnp.array(([x[0,1]-x[0,2],x[1,2]-x[1,0],x[2,0]-x[2,1]]))
    for l in range(0,2*layers,2):
        param_unitary(weights[l])
        data_encoding(x1)
        param_unitary(weights[l+1])
        data_encoding_pairs(x2)
    param_unitary(weights[2*layers])
    


######################################################################
# With our ``input_prep`` and ``bias_inv_layer`` functions we can now
# define our quantum model.
# 

dev = qml.device('default.qubit',wires=3)
@qml.qnode(dev, interface="jax")
def model(weights,x):
    input_prep(weights[2*layers+1,0]) #alpha is stored in the weights array
    bias_inv_layer(weights,x)
    return [qml.expval(qml.PauliZ(0)),qml.expval(qml.PauliZ(1)),qml.expval(qml.PauliZ(2))]

#jax vectorisation, we vectorise over the data input (the second argument)
vmodel = jax.vmap(model,(None,0))
vmodel=jax.jit(vmodel)


######################################################################
# To investigate the effect of the encoded inductive bias, we will compare
# this model to a generic model with the same data encoding and similar
# number of parameters (46 vs 45 parameters).
# 

def generic_layer(weights,x):
    #data preprocessing
    x1 = jnp.array([x[0,0],x[1,1],x[2,2]])
    x2 = jnp.array(([x[0,1]-x[0,2],x[1,2]-x[1,0],x[2,0]-x[2,1]]))
    for l in range(0,2*layers,2):
        qml.StronglyEntanglingLayers(weights[l], wires=range(3))
        data_encoding(x1)
        qml.StronglyEntanglingLayers(weights[l+1], wires=range(3))
        data_encoding_pairs(x2)
    qml.StronglyEntanglingLayers(weights[2*layers], wires=range(3))

dev = qml.device('default.qubit',wires=3)
@qml.qnode(dev, interface="jax")
def generic_model(weights,x):
    generic_layer(weights,x)
    return [qml.expval(qml.PauliZ(0)),qml.expval(qml.PauliZ(1)),qml.expval(qml.PauliZ(2))]

vmodel_generic = jax.vmap(generic_model,(None,0))
vmodel_generic = jax.jit(vmodel_generic)


######################################################################
# **Warning**: Since we are using JAX it is important that our ``model``
# and ``generic model`` functions are functionally pure (read more
# `here <https://jax.readthedocs.io/en/latest/notebooks/Common_Gotchas_in_JAX.html>`__).
# This means we cannot change the values of ``blocks`` or ``layers`` from
# hereon since these values have been cached for JIT compilation.
# 


######################################################################
# Training and evaluation
# -----------------------
# 


######################################################################
# To train the model we will minimise the negative log likelihood of the
# labels given the data
# 
# .. math:: \mathcal{L} = -\sum_{(X_i,\vec{y}_i)} \log(\mathcal{P}_0(y_i^{(0)}\vert X_i))+\log(\mathcal{P}_1(y_i^{(1)}\vert X_i))+\log(\mathcal{P}_2(y_i^{(2)}\vert X_i))
# 
# Here :math:`\mathcal{P}_k` is the probability distribution of the
# :math:`k` label from the model and :math:`y_i^{(k)}` is the kth element
# of the payoff vector :math:`\vec{y}_i` in the dataset. We remark that
# training the negative log likelihood is in some sense cheating, since
# for large quantum circuits we don’t know how to estimate it efficiently.
# As generative modeling in QML progresses, we can hope however that
# scalable methods that approximate this type of training may appear.
# 

def likelihood(weights,X,Y,model):
    """
    The cost function. Returns the negative log likelihood
    """
    expvals = model(weights,X)
    probs = (1+Y*expvals)/2 #get the relevant probabilites
    probs = jnp.log(probs)
    llh = jnp.sum(probs)/len(X)/3
    return -llh 


######################################################################
# For evaluation we will use the average KL divergence between the true
# data distribution and the model distribution
# 
# .. math:: \mathbb{E}_{P^\text{data}(X)} \left[\frac{1}{3}\sum_{k=1}^{3} D_{\text{KL}}(P^\text{data}_k(y\vert X)\vert\vert \mathcal{P}_k(y\vert X)) \right].
# 
# To estimate this we sample a test set of strategies, calculate their
# payoff probabilities, and estimate the above expectation via the sample
# mean.
# 

N_test=10000
X_test = get_strat_mats(N_test)

probs_test = np.zeros([N_test,3,2])
probs_test[:,:,0] = vpayoff_probs(X_test) #the true probabilities for the test set
probs_test[:,:,1] = 1-probs_test[:,:,0]
probs_test = jnp.array(probs_test)

def model_probs(model,X_test,weights):
    """
    Returns the marginal probabilties of the model for a test data set X_test
    """
    probs = np.zeros([len(X_test),3,2])
    expvals = model(weights,X_test)
    for t in range(3):
        probs[:,t,0] = (1+expvals[:,t])/2
        probs[:,t,1] = (1-expvals[:,t])/2
    return probs

def kl_div(p,q):
    """
    Get the KL divergence between two probability distribtuions
    """
    p=jnp.vstack([p,jnp.ones(len(p))*10**(-8)]) #lower cutoff of prob values of 10e-8
    p=jnp.max(p,axis=0)
    return jnp.sum(q*jnp.log(q/p)) #forward kl div 


def kl_marginals(probs,probs_test):
    """
    get the mean KL divergence of the three marginal distributions
    (the square brackets above)
    """
    kl = 0
    for t in range(3):
        kl=kl+kl_div(probs[t,:],probs_test[t,:])
    return kl/3

#vectorise the kl_marginals function. Makes estimating the average KL diverence of a model faster.
vkl_marginals = jax.vmap(kl_marginals,(0,0))

def get_av_test_kl(model,weights,probs_test,X_test):
    """
    returns the average KL divergence for a test set X_test. 
    """
    N_test=len(X_test)
    probs = np.zeros(probs_test.shape)
    expvals = model(weights,X_test)
    for t in range(3):
        probs[:,t,0] = (1+expvals[:,t])/2
        probs[:,t,1] = (1-expvals[:,t])/2
    return np.sum(vkl_marginals(probs,probs_test))/N_test


######################################################################
# To optimise the model we make use of the JAX optimization library optax.
# We will use the adam gradient descent optimizer.
# 

import optax 
from tqdm import tqdm

def optimise_model(model,nstep,lr,weights):
    plot=[[],[],[]]
    optimizer = optax.adam(lr) 
    opt_state = optimizer.init(weights)
    steps = tqdm(range(nstep))
    for step in steps:
#         use optax to update parameters
        llh, grads = jax.value_and_grad(likelihood)(weights, X, Y, model)
        updates, opt_state = optimizer.update(grads, opt_state, weights)
        weights = optax.apply_updates(weights, updates)
        
        kl = get_av_test_kl(model,weights,probs_test,X_test)
        steps.set_description("Current divergence: %s" % str(kl)+ " :::: "+
                              "Current likelihood: %s" % str(llh))
        plot[0].append(step)
        plot[1].append(float(llh))
        plot[2].append(float(kl))
    return weights, llh, kl, plot


######################################################################
# We are now ready to generate a dataset and optimize our model!
# 

#generate data
N=2000 #number of data points
X, Y, P = generate_data(N)

#we scale the data by pi/2
scaling = jnp.pi/2
X = scaling*jnp.array(X)

nstep = 1000 #number of optimisation steps

lr=0.001 #initial learning rate
weights_model = np.random.rand(2*layers+2,blocks,9)*2*np.pi
weights_generic = np.random.rand(2*layers+1,blocks,3,3)*2*np.pi

#optimise the structured model  
weights_model, llh, kl, plot_model = optimise_model(vmodel,
                                                    nstep,
                                                    lr,
                                                    weights_model)
#optimise the generic model
weights_generic, llh, kl, plot_genereic = optimise_model(vmodel_generic,
                                                         nstep,
                                                         lr,
                                                         weights_generic)
                                                      


######################################################################
# Let’s plot the average KL divergence and the negative log likelihood for
# both models.
# 

import matplotlib.pyplot as plt

#subplots
fig, (ax1,ax2) = plt.subplots(nrows=1,ncols=2, figsize=(12, 5))
fig.tight_layout(pad=10.0)

#KL divergence
ax1.plot(plot_model[0],plot_model[2],color='red',label='biased model')
ax1.plot(plot_genereic[0],plot_genereic[2],color='blue',label='generic model')

ax1.set_yscale('log')
ax1.set_ylabel('KL divergence (test)')
ax1.set_xlabel("training step")
ax1.legend()

#negative log likelihood
ax2.plot(plot_model[0],plot_model[1],color='red')
ax2.plot(plot_genereic[0],plot_genereic[1],color='blue')

ax2.set_yscale('log')
ax2.set_ylabel('Negative log likelihood (train)')
ax2.set_xlabel("training step")


######################################################################
# We see that the model that encodes the inductive bias achieves both a
# lower training error and generalisation error, as can be expected.
# Incorporating knowledge about the data into the model design is
# generally a very good idea!
# 
# That is all for this demo. In the paper, it is also shown how models of
# this kind can perform better than `classical surrogate
# models <https://arxiv.org/abs/2206.11740>`__ at this specific task,
# which further strengthens the claim that the inductive bias of the
# quantum model is useful. For more information and to read more about the
# link between contextuality and QML, check out the paper.
# 
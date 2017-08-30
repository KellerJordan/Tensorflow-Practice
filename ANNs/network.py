import random
import numpy as np

import sys


## math functions ---------------------------------------------------------------------------------
def sigmoid(z):
    # return z * (z > 0) # ReLU
    return 1.0 / (1.0 + np.exp(-z)) # sigmoid

def sigmoid_prime(a):
    # return 1 * (a > 0) # ReLU
    return a * (1 - a) # sigmoid

## cost, normalization functions ------------------------------------------------------------------
## fn(): returns the value of the cost incurred
## delta(): returns the derivative of C with respect to z^L or w respectively
class QuadraticCost:
    @staticmethod
    def fn(h, y):
        return .5 * (h - y)**2
    @staticmethod
    def delta(h, y):
        return (h - y) * sigmoid_prime(h)

class CrossEntropyCost:
    @staticmethod
    def fn(h, y):
        return -(y * np.log(h) + (1 - y) * np.log(1 - h)).sum()
    @staticmethod
    def delta(h, y):
        return h - y

class L2Normalizer:
    def __init__(self, lmbda):
        self.lmbda = lmbda
    def fn(self, w):
        return 0.5 * self.lmbda * np.linalg.norm(w)**2
        # return .5 * self.lmbda * np.dot(w, w)
    def delta(self, w):
        return self.lmbda * w

## artificial neural network ----------------------------------------------------------------------
class Network:

    SEED = 3

    def __init__(self, shape, cost=CrossEntropyCost, norm=None):
        # network architecture
        self.shape = shape
        self.num_layers = len(shape)
        np.random.seed(self.SEED)
        # network training
        self.cost = cost
        self.norm = norm
        # initialize weights
        self.normal_weight_initializer()

    def normal_weight_initializer(self):
        self.biases = [np.random.randn(y) for y in self.shape[1:]]
        self.weights = [np.random.randn(y, x) / np.sqrt(x)
                        for x, y in zip(self.shape[:-1], self.shape[1:])]

    def large_weight_initializer(self):
        self.biases = [np.random.randn(y) for y in self.shape[1:]]
        self.weights = [np.random.randn(y, x)
                        for x, y in zip(self.shape[:-1], self.shape[1:])]

    def feedforward(self, x, save_activations=False):
        a = x
        if save_activations:
            activations = [a]
        for b, w in zip(self.biases, self.weights):
            a = sigmoid(np.matmul(w, a) + b)
            if save_activations:
                activations.append(a)
        return activations if save_activations else a

    # uses denominator layout for matrix calculus
    def backpropagate(self, x, y):
        nabla_b = [np.zeros(b.shape) for b in self.biases]
        nabla_w = [np.zeros(w.shape) for w in self.weights]
        # feedforward, saving activations
        activations = self.feedforward(x, save_activations=True)
        h = activations[-1] # hypothesis
        # backpropagation
        del_C_wrt_z = self.cost.delta(h, y)
        for l in range(1, self.num_layers):
            nabla_b[-l] = del_C_wrt_z
            nabla_w[-l] = np.outer(del_C_wrt_z, activations[-l-1])
            if self.norm: nabla_w[-l] += self.norm.delta(nabla_w[-l])
            if l < self.num_layers - 1:
                del_C_wrt_a = np.matmul(self.weights[-l].transpose(), del_C_wrt_z)
                a = activations[-l-1]
                del_C_wrt_z = del_C_wrt_a * sigmoid_prime(a)
        return (nabla_b, nabla_w)

    def minibatch_update(self, minibatch, eta):
        nabla_b = [np.zeros(b.shape) for b in self.biases]
        nabla_w = [np.zeros(w.shape) for w in self.weights]
        # sum the derivatives of w with respect to cost over all training examples in batch
        for x, y in minibatch:
            delta_nabla_b, delta_nabla_w = self.backpropagate(x, y)
            nabla_b = [nb + dnb for nb, dnb in zip(nabla_b, delta_nabla_b)]
            nabla_w = [nw + dnw for nw, dnw in zip(nabla_w, delta_nabla_w)]
        # update accordingly
        self.weights = [w - (eta/len(minibatch))*nw for w, nw in zip(self.weights, nabla_w)]
        self.biases = [b - (eta/len(minibatch))*nb for b, nb in zip(self.biases, nabla_b)]

    def accuracy(self, data):
        test_results = [(np.argmax(self.feedforward(x)), np.argmax(y)) for x, y in data]
        return sum(int(h == y) for h, y in test_results)

    def total_cost(self, data):
        test_results = [(self.feedforward(x), y) for x, y in data]
        loss = sum([self.cost.fn(h, y) for h, y in test_results])
        complexity = sum([self.norm.fn(w) for w in self.weights])
        return (loss + complexity) / len(data)

    def SGD(self, epochs, minibatch_size, eta,
            data_train, data_eval,
            monitor_evaluation_cost=False,
            monitor_evaluation_accuracy=False,
            monitor_training_cost=False,
            monitor_training_accuracy=False):

        evaluation_cost, evaluation_accuracy = [], []
        training_cost, training_accuracy = [], []

        n_train = len(data_train)

        from datetime import datetime
        time_start = datetime.now()

        for j in range(epochs):
            random.shuffle(data_train)
            for k in range(0, n_train, minibatch_size):
                minibatch = data_train[k:k+minibatch_size]
                self.minibatch_update(minibatch, eta)
            print('Epoch {} complete.'.format(j+1))
            if monitor_evaluation_cost:
                cost = self.total_cost(data_eval)
                print('Cost on evaluation data: {}'.format(cost))
                evaluation_cost.append(cost)
            if monitor_evaluation_accuracy:
                accuracy = self.accuracy(data_eval)
                print('Accuracy on evaluation data: {} / {}'.format(accuracy, len(data_eval)))
                evaluation_accuracy.append(accuracy)
            if monitor_training_cost:
                cost = self.total_cost(data_train)
                print('Cost on training data: {}'.format(cost))
                training_cost.append(cost)
            if monitor_training_accuracy:
                accuracy = self.accuracy(data_train)
                print('Accuracy on training data: {} / {}'.format(accuracy, n_train))
                training_accuracy.append(accuracy)

        time_end = datetime.now()
        time_delta = str(time_end - time_start).rsplit('.', 1)[0]
        print(time_delta)

        return evaluation_cost, evaluation_accuracy, training_cost, training_accuracy

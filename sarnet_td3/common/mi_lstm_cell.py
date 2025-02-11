import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import tf_slim.layers as layers

class MiLSTMCell(tf.nn.rnn_cell.RNNCell):
    def __init__(self, num_units, forget_bias=1.0, input_size=None,
                 state_is_tuple=True, activation=tf.tanh, reuse=None):
        self.numUnits = num_units
        self.forgetBias = forget_bias
        self.activation = activation
        self.reuse = reuse

    @property
    def state_size(self):
        return tf.nn.rnn_cell.LSTMStateTuple(self.numUnits, self.numUnits)

    @property
    def output_size(self):
        return self.numUnits

    def mulWeights(self, inp, inDim, outDim, name=""):
        with tf.variable_scope("weights" + name):
            W = tf.get_variable("weights", shape=(inDim, outDim),
                                initializer=tf.keras.initializers.glorot_normal)
        output = tf.matmul(inp, W)
        return output

    def addBiases(self, inp1, inp2, dim, name=""):
        with tf.variable_scope("additiveBiases" + name):
            b = tf.get_variable("biases", shape=(dim,),
                                initializer=tf.zeros_initializer())
        with tf.variable_scope("multiplicativeBias" + name):
            beta = tf.get_variable("biases", shape=(3 * dim,),
                                   initializer=tf.ones_initializer())

        Wx, Uh, inter = tf.split(beta * tf.concat([inp1, inp2, inp1 * inp2], axis=1),
                                 num_or_size_splits=3, axis=1)
        output = Wx + Uh + inter + b
        return output

    def __call__(self, inputs, state, scope=None):
        scope = scope or type(self).__name__
        with tf.variable_scope(scope, reuse=self.reuse):
            c, h = state
            inputSize = int(inputs.shape[1])

            Wx = self.mulWeights(inputs, inputSize, self.numUnits, name="Wxi")
            Uh = self.mulWeights(h, self.numUnits, self.numUnits, name="Uhi")

            i = self.addBiases(Wx, Uh, self.numUnits, name="i")

            Wx = self.mulWeights(inputs, inputSize, self.numUnits, name="Wxj")
            Uh = self.mulWeights(h, self.numUnits, self.numUnits, name="Uhj")

            j = self.addBiases(Wx, Uh, self.numUnits, name="l")

            Wx = self.mulWeights(inputs, inputSize, self.numUnits, name="Wxf")
            Uh = self.mulWeights(h, self.numUnits, self.numUnits, name="Uhf")

            f = self.addBiases(Wx, Uh, self.numUnits, name="f")

            Wx = self.mulWeights(inputs, inputSize, self.numUnits, name="Wxo")
            Uh = self.mulWeights(h, self.numUnits, self.numUnits, name="Uho")

            o = self.addBiases(Wx, Uh, self.numUnits, name="o")
            # i, j, f, o = tf.split(value = concat, num_or_size_splits = 4, axis = 1)

            newC = (c * tf.nn.sigmoid(f + self.forgetBias) + tf.nn.sigmoid(i) *
                    self.activation(j))
            newH = self.activation(newC) * tf.nn.sigmoid(o)

            newState = tf.nn.rnn_cell.LSTMStateTuple(newC, newH)
        return newH, newState

    def zero_state(self, batchSize, dtype=tf.float32):
        return tf.nn.rnn_cell.LSTMStateTuple(tf.zeros((batchSize, self.numUnits), dtype=dtype),
                                             tf.zeros((batchSize, self.numUnits), dtype=dtype))

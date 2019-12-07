import numpy as np
import collections
import os
import math
import re
import tensorflow as tf
from sklearn.metrics import f1_score
from flags import FLAGS
from absl import logging
from models.lang_model import LanguageModel
from models.bert2 import load_stock_weights

K = tf.keras
L = K.layers


class ClaimBusterModel(K.layers.Layer):
    def __init__(self, cls_weights=None):
        super(ClaimBusterModel, self).__init__()

        self.optimizer = K.optimizers.Adam(learning_rate=FLAGS.lr)
        self.accuracy = K.metrics.Accuracy()  # @TODO create more in the future
        self.computed_cls_weights = cls_weights if cls_weights is not None else [1 for _ in range(FLAGS.num_classes)]

        self.bert_model = LanguageModel.build_bert()
        self.fc_layer = L.Dense(FLAGS.num_classes)

        self.vars_to_train = None

    def call(self, x_id, kp_cls=FLAGS.kp_cls, kp_tfm_atten=FLAGS.kp_tfm_atten, kp_tfm_hidden=FLAGS.kp_tfm_hidden):
        bert_output = self.bert_model(x_id)
        bert_output = tf.nn.dropout(bert_output, rate=1-kp_cls)
        ret = self.fc_layer(bert_output)

        if not self.vars_to_train:
            self.init_model_weights()
            self.vars_to_train = self.select_train_vars()

        return ret

    @tf.function
    def train_on_batch(self, x_id, y):
        y = tf.one_hot(y, depth=FLAGS.num_classes)

        with tf.GradientTape() as tape:
            logits = self.call(x_id)
            loss = self.compute_loss(y, logits)

        grad = tape.gradient(loss, self.trainable_weights)
        self.optimizer.apply_gradients(zip(grad, self.vars_to_train))

        return tf.reduce_sum(loss), self.compute_accuracy(y, logits)

        # self.accuracy.update_state(y, yhat)  # @TODO update accuracy

    @tf.function
    def stats_on_batch(self, x_id, y):
        y = tf.one_hot(y, depth=FLAGS.num_classes)
        logits = self.call(x_id)

        return tf.reduce_sum(self.compute_loss(y, logits)), self.compute_accuracy(y, logits)

    def compute_loss(self, y, logits):
        loss = tf.nn.softmax_cross_entropy_with_logits(labels=y, logits=logits)
        loss_l2 = 0

        if FLAGS.l2_reg_coeff > 0.0:
            varlist = self.trainable_variables
            loss_l2 = tf.add_n([tf.nn.l2_loss(v) for v in varlist if 'bias' not in v.name]) * FLAGS.l2_reg_coeff

        ret_loss = loss + loss_l2

        if FLAGS.weight_classes_loss:
            ret_loss *= self.computed_cls_weights

        return tf.identity(ret_loss, name='loss')

    def select_train_vars(self):
        train_vars = self.trainable_variables

        non_trainable_layers = ['/layer_{}/'.format(num)
                                for num in range(FLAGS.tfm_layers - FLAGS.tfm_ft_enc_layers)]
        if not FLAGS.tfm_ft_embed:
            non_trainable_layers.append('/word_embedding/' if FLAGS.tfm_type == 0 else '/embeddings/')
        if not FLAGS.tfm_ft_pooler:
            non_trainable_layers.append('/sequnece_summary/' if FLAGS.tfm_type == 0 else '/pooler/')

        train_vars = [v for v in train_vars if not any(z in v.name for z in non_trainable_layers)]

        logging.info('Removing: {}'.format(non_trainable_layers))
        logging.info([v.name for v in train_vars])

        return train_vars

    def init_model_weights(self, ckpt_path=os.path.join(FLAGS.bert_model_loc, 'bert_model.ckpt')):
        ckpt_reader = tf.train.load_checkpoint(ckpt_path)

        stock_weights = set(ckpt_reader.get_variable_to_dtype_map().keys())
        print(stock_weights)
        exit()

        prefix = bert_prefix(bert)

        loaded_weights = set()
        skip_count = 0
        weight_value_tuples = []
        skipped_weight_value_tuples = []

        bert_params = bert.weights
        param_values = keras.backend.batch_get_value(bert.weights)
        for ndx, (param_value, param) in enumerate(zip(param_values, bert_params)):
            stock_name = map_to_stock_variable_name(param.name, prefix)

            if ckpt_reader.has_tensor(stock_name):
                ckpt_value = ckpt_reader.get_tensor(stock_name)

                if param_value.shape != ckpt_value.shape:
                    print("loader: Skipping weight:[{}] as the weight shape:[{}] is not compatible "
                          "with the checkpoint:[{}] shape:{}".format(param.name, param.shape,
                                                                     stock_name, ckpt_value.shape))
                    skipped_weight_value_tuples.append((param, ckpt_value))
                    continue

                weight_value_tuples.append((param, ckpt_value))
                loaded_weights.add(stock_name)
            else:
                print("loader: No value for:[{}], i.e.:[{}] in:[{}]".format(param.name, stock_name, ckpt_path))
                skip_count += 1
        keras.backend.batch_set_value(weight_value_tuples)

        print("Done loading {} BERT weights from: {} into {} (prefix:{}). "
              "Count of weights not found in the checkpoint was: [{}]. "
              "Count of weights with mismatched shape: [{}]".format(
            len(weight_value_tuples), ckpt_path, bert, prefix, skip_count, len(skipped_weight_value_tuples)))

        print("Unused weights from checkpoint:",
              "\n\t" + "\n\t".join(sorted(stock_weights.difference(loaded_weights))))

        return skipped_weight_value_tuples  # (bert_weight, value_from_ckpt)

    @staticmethod
    def compute_accuracy(y, logits):
        return tf.reduce_mean(tf.cast(tf.equal(tf.argmax(logits, axis=1), tf.argmax(y, axis=1)), dtype=tf.float32))
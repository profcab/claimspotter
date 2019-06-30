import tensorflow as tf
import math
import time
import os
from adv_bert_claimspotter.utils.data_loader import Dataset
from adv_bert_claimspotter.model import ClaimBusterModel
from adv_bert_claimspotter.flags import FLAGS, print_flags


label_mapping = {
    'nfs': -1,
    'ufs': 0,
    'cfs': 1
}


def train_adv_bert_model(train, dev, test):
    global label_mapping
    os.environ['CUDA_VISIBLE_DEVICES'] = ','.join([str(z) for z in FLAGS.gpu])

    print_flags()

    tf.logging.info("Loading dataset from given values")

    train[1] = list(map(label_mapping, train[1]))
    dev[1] = list(map(label_mapping, dev[1]))
    test[1] = list(map(label_mapping, test[1]))

    print(train[1])
    exit()

    train_data = Dataset(train[0], train[1], random_state=FLAGS.random_state)
    test_data = Dataset(test[0], test[1], random_state=FLAGS.random_state)

    tf.logging.info("{} training examples".format(train_data.get_length()))
    tf.logging.info("{} validation examples".format(test_data.get_length()))

    cb_model = ClaimBusterModel(data_load.vocab, data_load.class_weights)

    with tf.Session(config=tf.ConfigProto(allow_soft_placement=True)) as sess:
        sess.run(tf.global_variables_initializer())
        if not FLAGS.bert_model:
            cb_model.embed_obj.init_embeddings(sess)

        start = time.time()
        epochs_trav = 0

        tf.logging.info("Starting{}training...".format(' adversarial ' if FLAGS.adv_train else ' '))
        for epoch in range(FLAGS.max_steps):
            epochs_trav += 1
            n_batches = math.ceil(float(FLAGS.train_examples) / float(FLAGS.batch_size))

            n_samples = 0
            epoch_loss = 0.0
            epoch_acc = 0.0

            for i in range(n_batches):
                batch_x, batch_y = cb_model.get_batch(i, train_data)
                cb_model.train_neural_network(sess, batch_x, batch_y)

                b_loss, b_acc, _ = cb_model.stats_from_run(sess, batch_x, batch_y)
                epoch_loss += b_loss
                epoch_acc += b_acc * len(batch_y)
                n_samples += len(batch_y)

            epoch_loss /= n_samples
            epoch_acc /= n_samples

            if epoch % FLAGS.stat_print_interval == 0:
                log_string = 'Epoch {:>3} Loss: {:>7.4} Acc: {:>7.4f}% '.format(epoch + 1, epoch_loss,
                                                                                epoch_acc * 100)
                if test_data.get_length() > 0:
                    log_string += cb_model.execute_validation(sess, test_data)
                log_string += '({:3.3f} sec/epoch)'.format((time.time() - start) / epochs_trav)

                tf.logging.info(log_string)

                start = time.time()
                epochs_trav = 0

            if epoch % FLAGS.model_save_interval == 0 and epoch != 0:
                cb_model.save_model(sess, epoch)
                tf.logging.info('Model @ epoch {} saved'.format(epoch + 1))

        tf.logging.info('Training complete. Saving final model...')
        cb_model.save_model(sess, FLAGS.max_steps)
        tf.logging.info('Model saved.')

        sess.close()


if __name__ == '__main__':
    tf.logging.set_verbosity(tf.logging.INFO)
    main()




from datetime import datetime
import os.path
import time

import numpy as np
import tensorflow as tf
import math
import shutil

import _option as OPTION
import HAN_model
import HAN_input



# Model Hyperparameters
tf.flags.DEFINE_integer("embedding_dim", 100, "Dimensionality of character embedding (default: 128)")
tf.flags.DEFINE_boolean('log_device_placement', False, "Whether to log device placement.")
tf.flags.DEFINE_boolean("allow_soft_placement", True, "Allow device soft device placement")
tf.flags.DEFINE_integer('eval_interval_secs', 60, """How often to run the eval.""")
tf.flags.DEFINE_boolean('run_once', False, """Whether to run eval only once.""")

FLAGS = tf.flags.FLAGS
FLAGS._parse_flags()


os.environ['CUDA_VISIBLE_DEVICES']='0'


def evaluate(evalDataSet,time,model_time,name='train'):

    with tf.Graph().as_default() as g, tf.device('/gpu:0'):

        # Placeholders for input, output and dropout
        input_x = tf.placeholder(tf.int32, [None, OPTION.SEQUENCE_LEN, OPTION.SENT_LEN], name="input_x")

        han = HAN_model.Model(sequence_length = OPTION.SEQUENCE_LEN, sent_length = OPTION.SENT_LEN,
                                      num_classes = OPTION.NUM_CLASSES,
                                      vocab_size = None,
                                      embedding_size = OPTION.EMEBEDDING_DIMENSION,
                                      Word2vec = True, Trainable = False)

        # inference model.
        _, features = han.inference(input_x, eval_data=True)

        # get model paramaters
        # paramaters_list_reshape = han.get_paramaters_list_reshape()

        # Restore the moving average version of the learned variables for eval. # ?????????????????????????
        variable_averages = tf.train.ExponentialMovingAverage(OPTION.MOVING_AVERAGE_DECAY)
        variables_to_restore = variable_averages.variables_to_restore()
        saver = tf.train.Saver(variables_to_restore)

        # Build the summary operation based on the TF collection of Summaries.
        summary_op = tf.summary.merge_all()
        summary_writer = tf.summary.FileWriter(OPTION.EVAL_DIR, g)

        config=tf.ConfigProto(
                allow_soft_placement=FLAGS.allow_soft_placement,
                log_device_placement=FLAGS.log_device_placement)
        # config.gpu_options.per_process_gpu_memory_fraction = 0.5  # 程序最多只能占用指定gpu50%的显存
        config.gpu_options.allow_growth = OPTION.MEMORY_ALLOW_GROWTH  # 程序按需申请内存


        # Start running operations on the Graph. allow_soft_placement must be set to
        # True to build towers on GPU, as some of the ops do not have GPU implementations.
        with tf.Session(config=config) as sess:

            if os.path.exists(os.path.join(OPTION.EVAL_DIR, 'model.ckpt-best.index')):
                # new_saver = tf.train.import_meta_graph(
                #     os.path.join(OPTION.TRAIN_DIR, 'model.ckpt-' + checkpoint + '.meta'))
                saver.restore(sess,
                              os.path.join(OPTION.EVAL_DIR, 'model.ckpt-best'))
            else:
                print('No checkpoint file found')
                return

            max_steps_per_epoch = int(math.ceil( evalDataSet.get_dataset_size() / float(OPTION.EVAL_BATCH_SIZE)))
            total_predicted_value = []
            for step in range(max_steps_per_epoch):
                test_data = evalDataSet.next_batch(OPTION.EVAL_BATCH_SIZE)
                predicted_value = sess.run(features,
                                           feed_dict={input_x: test_data})
                total_predicted_value.append(predicted_value)

            # test_data, test_label = evalDataSet.next_batch(OPTION.EVAL_BATCH_SIZE)
            summary = tf.Summary()
            # summary.ParseFromString(sess.run(summary_op, feed_dict={input_x: test_data, input_y: test_label}))

            total_predicted_value = np.concatenate(total_predicted_value,axis=0)

            assert evalDataSet.get_dataset_size() == total_predicted_value.shape[0], 'sample_count error!'

            detail_filename = os.path.join(OPTION.MODELPARA_DIR, 'features_%s_%d_%d' % (name,time,model_time))
            if os.path.exists(detail_filename):
                os.remove(detail_filename)
            np.savetxt(detail_filename, total_predicted_value, fmt='%.4f')




def main(argv=None):
    time_list = np.loadtxt(os.path.join(OPTION.MODELPARA_DIR, 'time_list'), dtype=int)
    time_list = np.reshape(time_list, [-1])
    model_time = time_list[-1]
    ans = input('please choose times to get features:')
    time_list = np.array((ans.strip()).split(' '), dtype=int)
    print('...')
    for one in time_list:
        evalDataSet = HAN_input.generate_train_data([one],shuffled=False,label_used=False)
        evaluate(evalDataSet,one,model_time,name='train')
        evalDataSet = HAN_input.generate_eval_data([one], shuffled=False, label_used=False)
        evaluate(evalDataSet, one, model_time,name='test')


if __name__ == '__main__':
    tf.app.run()









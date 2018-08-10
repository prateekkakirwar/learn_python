import tensorflow
import sklearn.preprocessing

tensorflow.enable_eager_execution()

log_dir='log/'
batch_size=50
max_step=60000
repeat_times=5
init_lr=0.001
decay_rate=0.01

(train_data,train_label),(test_data,test_label)=tensorflow.keras.datasets.mnist.load_data()
OneHotEncoder=sklearn.preprocessing.OneHotEncoder()
OneHotEncoder.fit(train_label.reshape(-1,1))
train_label=OneHotEncoder.transform(train_label.reshape(-1,1)).toarray()
test_label=OneHotEncoder.transform(test_label.reshape(-1,1)).toarray()

######################################################################
def ConvOffset(filters, x, name):
    w=tensorflow.get_variable(name, [3,3,filters,filters * 2], initializer=tensorflow.zeros_initializer)
    offsets=tensorflow.nn.conv2d(x,w,[1,1,1,1],'SAME')

    x_shape = x.shape

    offsets = tensorflow.transpose(offsets, [0, 3, 1, 2])
    offsets = tensorflow.reshape(offsets, (-1, x_shape[1], x_shape[2], 2))
    ##############################删除#####################
    offsets=tensorflow.stack([offsets[:,:,:,0]+0.1,offsets[:,:,:,1]+0.5], axis=-1)
    ##############################删除#####################
    x = tensorflow.transpose(x, [0, 3, 1, 2])
    x = tensorflow.reshape(x, (-1, x_shape[1], x_shape[2]))

    x_offset = tf_batch_map_offsets(x, offsets)

    x_offset = tensorflow.reshape(x_offset, (-1, x_shape[3], x_shape[1], x_shape[2]))
    x_offset = tensorflow.transpose(x_offset, [0, 2, 3, 1])

    return x_offset    
###############################################################
def tf_batch_map_offsets(input, offsets):
    input_shape = tensorflow.shape(input)
    batch_size = input_shape[0]
    input_size = input_shape[1]

    offsets = tensorflow.reshape(offsets, (batch_size, -1, 2))
    grid = tensorflow.meshgrid(tensorflow.range(input_size), tensorflow.range(input_size), indexing='ij')
    grid = tensorflow.stack(grid, axis=-1)
    grid = tensorflow.cast(grid, 'float32')
    grid = tensorflow.reshape(grid, (-1, 2))
    grid = tensorflow.expand_dims(grid, 0)
    grid = tensorflow.tile(grid, [batch_size, 1, 1])
    coords = offsets + grid
    ##########################################
    n_coords = tensorflow.shape(coords)[1]

    coords = tensorflow.clip_by_value(coords, 0, tensorflow.cast(input_size, 'float32') - 1)
    coords_lt = tensorflow.cast(tensorflow.floor(coords), 'int32')
    coords_rb = tensorflow.cast(tensorflow.ceil(coords), 'int32')
    coords_rt = tensorflow.stack([coords_lt[..., 0], coords_rb[..., 1]], axis=-1)
    coords_lb = tensorflow.stack([coords_rb[..., 0], coords_lt[..., 1]], axis=-1)

    a = tensorflow.expand_dims(tensorflow.range(batch_size), -1)
    a = tensorflow.tile(a, [1, n_coords])
    idx=tensorflow.reshape(a, [-1])

    indices = tensorflow.stack([idx, tensorflow.reshape(coords_lt[..., 0],[-1]), tensorflow.reshape(coords_lt[..., 1],[-1])], axis=-1)
    vals = tensorflow.gather_nd(input, indices)
    vals_lt = tensorflow.reshape(vals, (batch_size, n_coords))   
    indices = tensorflow.stack([idx, tensorflow.reshape(coords_rb[..., 0],[-1]), tensorflow.reshape(coords_rb[..., 1],[-1])], axis=-1)
    vals = tensorflow.gather_nd(input, indices)
    vals_rb = tensorflow.reshape(vals, (batch_size, n_coords))   
    indices = tensorflow.stack([idx, tensorflow.reshape(coords_lb[..., 0],[-1]), tensorflow.reshape(coords_lb[..., 1],[-1])], axis=-1)
    vals = tensorflow.gather_nd(input, indices)
    vals_lb = tensorflow.reshape(vals, (batch_size, n_coords))  
    indices = tensorflow.stack([idx, tensorflow.reshape(coords_rt[..., 0],[-1]), tensorflow.reshape(coords_rt[..., 1],[-1])], axis=-1)
    vals = tensorflow.gather_nd(input, indices)
    vals_rt = tensorflow.reshape(vals, (batch_size, n_coords))  

    coords_offset_lt = coords - tensorflow.cast(coords_lt, 'float32')
    vals_t = vals_lt + (vals_rt - vals_lt) * coords_offset_lt[..., 1]
    vals_b = vals_lb + (vals_rb - vals_lb) * coords_offset_lt[..., 1]
    mapped_vals = vals_t + (vals_b - vals_t) * coords_offset_lt[..., 0]
    ###########################################  
    return mapped_vals
################################################################
def cnn(x):
    with tensorflow.variable_scope('cnn'):
        w1=tensorflow.get_variable('w1', [3,3,1,8], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        b1=tensorflow.get_variable('b1', 8, initializer=tensorflow.constant_initializer(0))
        z1=tensorflow.nn.conv2d(x,w1,[1,2,2,1],'SAME')+b1
        z1=tensorflow.nn.selu(z1)

        l_offset = ConvOffset(8,z1,'conv12_offset')
        w2=tensorflow.get_variable('w2', [3,3,8,16], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        b2=tensorflow.get_variable('b2', 16, initializer=tensorflow.constant_initializer(0))
        z2=tensorflow.nn.conv2d(l_offset,w2,[1,2,2,1],'SAME')+b2
        z2=tensorflow.nn.selu(z2)

        w3=tensorflow.get_variable('w3', [3,3,16,32], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        b3=tensorflow.get_variable('b3', 32, initializer=tensorflow.constant_initializer(0))
        z3=tensorflow.nn.conv2d(z2,w3,[1,2,2,1],'VALID')+b3
        z3=tensorflow.nn.selu(z3)

        w4=tensorflow.get_variable('w4', [3,3,32,10], initializer=tensorflow.truncated_normal_initializer(stddev=0.1))
        b4=tensorflow.get_variable('b4', 10, initializer=tensorflow.constant_initializer(0))
        z4=tensorflow.nn.conv2d(z3,w4,[1,1,1,1],'VALID')+b4
        z4=tensorflow.nn.selu(z4)

        z4=tensorflow.reshape(z4,[-1,10])
    return z4

# input_data=tensorflow.placeholder(tensorflow.float32,[None,28,28,1],name='input_data')
# input_label=tensorflow.placeholder(tensorflow.float32,[None,10],name='input_label')
# global_step = tensorflow.get_variable('global_step',initializer=0, trainable=False)
# learning_rate=tensorflow.train.exponential_decay(init_lr,global_step,max_step,decay_rate)
input_data=tensorflow.random_normal([10,28,28,1],name='input_data')

resullt=cnn(input_data)

loss=tensorflow.losses.softmax_cross_entropy(input_label,resullt)

minimize=tensorflow.train.AdamOptimizer(learning_rate).minimize(loss,global_step=global_step,name='minimize')

accuracy = tensorflow.reduce_mean(tensorflow.cast(tensorflow.equal(tensorflow.argmax(tensorflow.nn.softmax(resullt), 1), tensorflow.argmax(input_label, 1)), tensorflow.float32))

Session=tensorflow.Session()
Session.run(tensorflow.global_variables_initializer())

tensorflow.summary.scalar('loss', loss)
tensorflow.summary.scalar('accuracy', accuracy)
merge_all = tensorflow.summary.merge_all()
FileWriter = tensorflow.summary.FileWriter(log_dir, Session.graph)

num = train_data.shape[0] // batch_size
for i in range(max_step*repeat_times//batch_size+1):
    temp_train = train_data[i % num * batch_size:i % num * batch_size + batch_size,:].reshape(-1,28,28,1)
    temp_label = train_label[i % num * batch_size:i % num * batch_size + batch_size,:]
    Session.run(minimize,feed_dict={input_data:temp_train,input_label:temp_label})
    if Session.run(global_step)%100==1:
        summary = Session.run(merge_all, feed_dict={input_data:test_data.reshape(-1,28,28,1),input_label:test_label})
        FileWriter.add_summary(summary, Session.run(global_step))
    print(Session.run(global_step))
import numpy as np
def f(x):
    return x[:,:,2].max(axis=1)



def getMax(matrix):
    # Convert the 3D NumPy array to a 2D array for the third column
    third_column = matrix[:, :, 2]

    # Compute the maximum value in the third column
    max_values = np.max(third_column, axis=1)

    # Reshape the result to a 2D array
    max_2d_array = max_values.reshape(-1, 1)

    return max_2d_array

x = np.asarray([[[1,2,3],[4,5,6]],[[7,8,9],[10,11,12]]])
#print(f(x).flatten() == getMax(x).flatten())
assert all(f(x).flatten() == getMax(x).flatten())

y = np.asarray([[[10,2,3],[4,50,6]],[[72,84,99],[10,111,12]]])
assert all(f(y).flatten() == getMax(y).flatten())
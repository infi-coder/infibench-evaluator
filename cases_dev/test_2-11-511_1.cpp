#include <vector>
#include <string>
#include <iostream>
#include <cassert>


int main() {
    int N, M;
    N = 4;
    M = 3;
    std::vector<std::string> A = my_2d_array(N, M);

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < M; j++) {
            assert(A[i*M+j]==std::to_string(i)+std::to_string(j));
            //std::cout << A[i*M+j] << " ";
        }
    }
}
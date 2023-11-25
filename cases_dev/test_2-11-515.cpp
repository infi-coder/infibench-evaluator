#include <vector>
#include <string>
#include <iostream>
#include <cassert>

int main(){
    vector<int> origin = {1, 2, 3, 4, 5, 6, 7, 8};
    vector<pair<int, int> > goal = origin_to_goal(origin); //{ {1, 2}, {3, 4}, {5, 6}, {7, 8} };
    return 0;
}
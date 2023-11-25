
const __test_assert = require('node:assert');

// test 0

test_0 = { milk: { quantity : 5, price: 20 }, bread: { quantity : 2, price: 15 }, potato: { quantity : 3, price: 10 } };

ret_test_0 = keys_and_prices(test_0);

for (idx in ret_test_0[0]) {
    __test_assert.strictEqual(test_0[ret_test_0[0][idx]].price, ret_test_0[1][idx]);
}
for (item in test_0) {
    __test_assert.strictEqual(ret_test_0[0].includes(item), true);
}
__test_assert.strictEqual(ret_test_0[0].length, Object.keys(test_0).length);

// test 1

test_1 = { '1': {price: 0}, '2': {price: -1}, '0': {price: 5}, '4': {price: 1 } };

ret_test_1 = keys_and_prices(test_1);

for (idx in ret_test_1[0]) {
    __test_assert.strictEqual(test_1[ret_test_1[0][idx]]['price'], ret_test_1[1][idx]);
    idx += 1;
}
for (item in test_1) {
    __test_assert.strictEqual(ret_test_1[0].includes(item), true);
}
__test_assert.strictEqual(ret_test_1[0].length, Object.keys(test_1).length);

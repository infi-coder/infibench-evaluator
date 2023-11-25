
const __test_assert = require('node:assert');

function objectEqual(a1,a2) { /* WARNING: arrays must not contain {objects} or behavior may be undefined */ return JSON.stringify(a1)==JSON.stringify(a2); }

test_obj_0 = {
    "id": "A",
    "name": "Item A",
    "child": [
        {
            "id": "B",
            "name": "Item B",
            "child": [
                {
                    "id": "C",
                    "name": "Item C",
                    "child": []
                }
            ]
        },
        {
            "id": "D",
            "name": "Item D",
            "child": []
        }
    ]
};


__test_assert.strictEqual(findObject("B", test_obj_0), test_obj_0.child[0]);

__test_assert.strictEqual(findObject("C", test_obj_0), test_obj_0.child[0].child[0]);

__test_assert.strictEqual(findObject("D", test_obj_0), test_obj_0.child[1]);

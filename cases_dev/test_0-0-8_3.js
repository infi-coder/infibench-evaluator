
const __test_assert = require('node:assert');

function objectEqual(a1,a2) { /* WARNING: arrays must not contain {objects} or behavior may be undefined */ return JSON.stringify(a1)==JSON.stringify(a2); }

test_obj_0 = {
    "id": "ZZZZ",
    "name": "test ZZZZ",
    "child": [
        {
            "id": "YYYY",
            "name": "test YYYY",
            "child": [
                {
                    "id": "XXXX",
                    "name": "test XXXX",
                    "child": [
                        {
                            "id": "WWWW",
                            "name": "test WWWW",
                            "child": []
                        }
                    ]
                }
            ]
        }
    ]
};

__test_assert.strictEqual(findObject("ZZZZ", test_obj_0), test_obj_0);


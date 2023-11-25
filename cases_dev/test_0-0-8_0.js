
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

findObject("A", test_obj_0);


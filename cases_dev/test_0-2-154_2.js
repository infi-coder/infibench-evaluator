
const __test_assert = require('node:assert');

strhtml = '<p>Hello World</p><p>I am a text with <strong>bold</strong> word</p><p><strong>I am bold text with nested <em>italic</em> Word.</strong></p>';

__test__result__final = [...iterLeafNodes(strhtml)];

tgt_result = [
    {text: 'Hello World', format: ['p']},
    { text: 'I am a text with ', format: ['p']},
    { text: 'bold', format: ['p', 'strong'] },
    { text: ' word', format: [ 'p' ] },
    { text: 'I am bold text with nested ', format: ['p', 'strong' ] },
    { text: 'italic', format:[ 'p', 'strong', 'em' ] },
    { text: ' Word.', format: [ 'p', 'strong'] }
];

__test_assert.deepEqual(__test__result__final, tgt_result,);


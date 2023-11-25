
const __test_assert = require('node:assert');

strhtml = '<p>Hello World</p><p>I am a text with </p><strong>bold</strong><p> word</p><p>I am bold text with nested </p><em>italic</em><p> Word.</p>';

__test__result__final = [...iterLeafNodes(strhtml)];

tgt_result = [
    {text: 'Hello World', format: ['p']},
    { text: 'I am a text with ', format: ['p']},
    { text: 'bold', format: ['strong'] },
    { text: ' word', format: [ 'p' ] },
    { text: 'I am bold text with nested ', format: ['p'] },
    { text: 'italic', format:[ 'em' ] },
    { text: ' Word.', format: [ 'p'] }
];

__test_assert.deepEqual(__test__result__final, tgt_result,);


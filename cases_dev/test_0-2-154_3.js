
const __test_assert = require('node:assert');

strhtml = '<p>Hello World</p><p>I am a text with <strong>bold</strong> word</p><p><strong>I am bold text with nested <em>italic</em> Word.</strong></p><p>T<strong>h<em>i</em></strong></p><p>s</p><p> is just a test.</p>';

__test__result__final = [...iterLeafNodes(strhtml)];

tgt_result = [
    {text: 'Hello World', format: ['p']},
    { text: 'I am a text with ', format: ['p']},
    { text: 'bold', format: ['p', 'strong'] },
    { text: ' word', format: [ 'p' ] },
    { text: 'I am bold text with nested ', format: ['p', 'strong' ] },
    { text: 'italic', format:[ 'p', 'strong', 'em' ] },
    { text: ' Word.', format: [ 'p', 'strong'] },
    { text: 'T', format: [ 'p' ] },
    { text: 'h', format: [ 'p', 'strong' ] },
    { text: 'i', format: [ 'p', 'strong', 'em' ] },
    { text: 's', format: [ 'p' ] },
    { text: ' is just a test.', format: [ 'p' ] }
];

__test_assert.deepEqual(__test__result__final, tgt_result,);


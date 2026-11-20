import SwaggerParser from '@apidevtools/swagger-parser';
import assert from 'node:assert/strict';
import { contract, validators } from '../validation.mjs';

await SwaggerParser.validate(structuredClone(contract));
let count=0;
for (const item of Object.values(contract.paths)) {
  for (const [method,operation] of Object.entries(item)) {
    if (!['get','post','patch','delete'].includes(method)) continue;
    count++;
    for (const media of Object.values(operation.requestBody?.content || {})) {
      assert.ok(media.schema.$ref,'Corpo deve referenciar schema');
      const name=media.schema.$ref.split('/').at(-1);
      assert.ok(validators[name](media.example),JSON.stringify(validators[name].errors));
    }
    for (const [code,response] of Object.entries(operation.responses)) {
      if (response.$ref) continue;
      if (code==='204') { assert.equal(response.content,undefined); continue; }
      for (const media of Object.values(response.content || {})) {
        assert.ok(media.schema.$ref,'Resposta deve referenciar schema');
        const name=media.schema.$ref.split('/').at(-1);
        assert.ok(validators[name](media.example),JSON.stringify(validators[name].errors));
      }
    }
  }
}
assert.equal(count,13);
console.log(`OpenAPI válido; ${count} operações; ${Object.keys(validators).length} schemas; exemplos válidos e corpos/respostas por $ref.`);

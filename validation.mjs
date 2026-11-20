import { readFileSync } from 'node:fs';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

export const contract = JSON.parse(readFileSync(new URL('./docs/openapi-v1.1.json', import.meta.url), 'utf8'));
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
ajv.addSchema({ components: contract.components }, 'contract');
export const validators = Object.fromEntries(Object.keys(contract.components.schemas).map(name =>
  [name, ajv.compile({ $ref: `contract#/components/schemas/${name}` })]));
export function validate(name, value) {
  const check = validators[name];
  if (check(value)) return [];
  return check.errors.map(e => ({ campo: e.instancePath || e.params.missingProperty || '/', mensagem: e.message }));
}

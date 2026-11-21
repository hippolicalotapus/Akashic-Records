import test from 'node:test';
import assert from 'node:assert/strict';
import { validateProposals } from '../tools/validate-ingest.mjs';

const valid = () => ({
  id: 'wellcome:manuscript-1', type: 'document', title: 'Example manuscript',
  rights_tier: 'B', takedown: { state: 'none' },
  source: { canonical_url: 'https://example.org/item', accessed: '2026-11-21', health: 'unchecked' },
  revision: 1, created_at: '2026-11-21', evidence_status: 'institutional_description'
});
test('accepts metadata-only proposed record', () => assert.deepEqual(validateProposals([valid()]), []));
test('rejects duplicate identifiers', () => assert.match(validateProposals([valid(), valid()]).join(' '), /duplicate id/));
test('rejects unsupported rights tier', () => {
  const r = valid(); r.rights_tier = 'X';
  assert.match(validateProposals([r]).join(' '), /rights_tier/);
});
test('requires explicit rights basis for public tier A', () => {
  const r = valid(); r.rights_tier = 'A';
  assert.match(validateProposals([r]).join(' '), /rights_basis/);
});
test('requires permission reference for cleared tier C', () => {
  const r = valid(); r.rights_tier = 'C';
  assert.match(validateProposals([r]).join(' '), /permission_reference/);
});
test('rejects missing source URL', () => {
  const r = valid(); r.source.canonical_url = '';
  assert.match(validateProposals([r]).join(' '), /source URL/);
});

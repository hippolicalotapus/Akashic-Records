#!/usr/bin/env node
// Validate proposed Akashic metadata before it enters the archive.
// Usage: node tools/validate-ingest.mjs path/to/proposals.json
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const TYPES = new Set(['artifact','document','image','place','person','event','claim','topic','collection']);
const PORTALS = new Set(['akashic-records','orbis-arcanorum','world-wonder-web','world-wicked-web','science-portal']);
const RIGHTS = new Set(['A','B','C','D']);
const HEALTH = new Set(['live','moved','dead','gone','unchecked']);
const STATES = new Set(['none','noticed','complied','disputed']);
const EVIDENCE = new Set(['institutional_description','primary_source','secondary_source','unsourced','disputed']);
const idPattern = /^[a-z]+:[a-z0-9-]+(:[a-z0-9._-]+)?$/;

export function validateProposals(records) {
  const errors = [];
  if (!Array.isArray(records)) return ['Root must be an array of records'];
  const ids = new Set();
  records.forEach((r, i) => {
    const at = `records[${i}]`;
    if (!r || typeof r !== 'object' || Array.isArray(r)) { errors.push(`${at}: must be an object`); return; }
    if (typeof r.id !== 'string' || !idPattern.test(r.id)) errors.push(`${at}: invalid id`);
    else if (ids.has(r.id)) errors.push(`${at}: duplicate id ${r.id}`);
    else ids.add(r.id);
    if (!TYPES.has(r.type)) errors.push(`${at}: invalid type`);
    if (typeof r.title !== 'string' || !r.title.trim()) errors.push(`${at}: title required`);
    if (!RIGHTS.has(r.rights_tier)) errors.push(`${at}: invalid rights_tier`);
    if (!r.takedown || !STATES.has(r.takedown.state)) errors.push(`${at}: invalid takedown state`);
    if (!r.source || typeof r.source.canonical_url !== 'string' || !/^https?:\/\//i.test(r.source.canonical_url)) errors.push(`${at}: source URL required`);
    if (!r.source || !HEALTH.has(r.source.health)) errors.push(`${at}: invalid source health`);
    if (!r.source || !Number.isFinite(Date.parse(r.source.accessed))) errors.push(`${at}: valid accessed date required`);
    if (!Number.isInteger(r.revision) || r.revision < 1) errors.push(`${at}: revision must be positive integer`);
    if (typeof r.created_at !== 'string' || !Number.isFinite(Date.parse(r.created_at))) errors.push(`${at}: valid created_at required`);
    if (r.portals !== undefined && (!Array.isArray(r.portals) || r.portals.some(p => !PORTALS.has(p)))) errors.push(`${at}: invalid portals`);
    if (r.evidence_status !== undefined && !EVIDENCE.has(r.evidence_status)) errors.push(`${at}: invalid evidence_status`);
    if (r.captures !== undefined && (!Array.isArray(r.captures) || r.captures.some(c => !c || typeof c !== 'object' || !c.captured_at || !c.sha256 || !c.warc || !['public','dark'].includes(c.mirror_status)))) errors.push(`${at}: invalid captures`);
    if (r.rights_tier === 'C' && !r.permission_reference) errors.push(`${at}: cleared tier C requires permission_reference (ingestion policy)`);
    if (r.rights_tier === 'A' && !r.rights_basis) errors.push(`${at}: tier A requires rights_basis (ingestion policy)`);
  });
  return errors;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    if (!process.argv[2]) throw new Error('Provide a JSON proposal file');
    const errors = validateProposals(JSON.parse(readFileSync(process.argv[2], 'utf8')));
    if (errors.length) { console.error(errors.join('\n')); process.exitCode = 1; }
    else console.log('Proposal metadata validated; publication and rights approval are still required.');
  } catch (e) { console.error(e.message); process.exitCode = 1; }
}

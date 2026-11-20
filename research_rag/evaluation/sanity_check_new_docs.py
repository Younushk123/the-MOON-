import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api import answer_question

queries = [
    ('Document A (S31)', 'S31', 'What are the preliminary results for CO2, CO and temperature rise from the Saffire VI experiment?'),
    ('Document B (S28)', 'S28', 'What were the results for combustion of solids in microgravity from BASS-II?'),
    ('Document C (S29)', 'S29', 'What did the BASS-II summary report find regarding flame burning and suppression of solids?'),
    ('Document D (S50)', 'S50', 'What was the finding of the Apollo 204 Review Board regarding the spacecraft cabin fire?'),
    ('Document E (S51)', 'S51', 'What did the Apollo 13 Review Board report regarding the oxygen tank failure?'),
    ('Document F (S52)', 'S52', 'What occurred during the February 23 1997 fire on the Mir Space Station?'),
    ('Document G (S56)', 'S56', 'What did the Smoke Aerosol Measurement Experiment SAME find regarding smoke detector performance in microgravity?'),
    ('Document J (S33)', 'S33', 'What is the Saffire novel approach to study spacecraft fire safety on unmanned spacecraft?')
]

print("=== RETRIEVAL SANITY CHECKS FOR NEWLY INGESTED DOCUMENTS ===\n")
for label, target_sid, q in queries:
    res = answer_question(q, top_k=5)
    retrieved_sids = [r['register_id'] for r in res['retrieval']]
    print(f"Test: {label} [Target {target_sid}]")
    print(f"Query: {q}")
    print(f"Retrieved Source IDs: {retrieved_sids[:5]}")
    print(f"Target in Top 5? {target_sid in retrieved_sids}")
    print(f"Target in Top 1? {target_sid == retrieved_sids[0] if retrieved_sids else False}")
    if res['evidence']:
        ev0 = res['evidence'][0]
        cid = ev0['chunk_id']
        pg = ev0['page']
        txt = ev0['evidence_text'][:140]
        print(f"Top Evidence Passage: Chunk={cid} | Page={pg} | Text={txt}...")
    print(f"Abstained: {res['abstained']}")
    print("-" * 70)

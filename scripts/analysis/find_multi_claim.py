import csv
import collections

INPUT_FILE = 'encounters_enriched_deterministic.csv'

def find_multi_claim():
    enc_map = collections.defaultdict(set)
    
    with open(INPUT_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            enc_id = row.get('EncounterID')
            claim_id = row.get('ClaimID')
            if enc_id and claim_id:
                enc_map[enc_id].add(claim_id)
                
    # Find ones with > 1 claim
    candidates = {k: v for k, v in enc_map.items() if len(v) > 1}
    
    print(f"Total Encounters: {len(enc_map)}")
    print(f"Multi-Claim Encounters: {len(candidates)}")
    
    for eid, claims in list(candidates.items())[:5]:
        print(f"Encounter {eid}: {len(claims)} Claims -> {claims}")

if __name__ == "__main__":
    find_multi_claim()

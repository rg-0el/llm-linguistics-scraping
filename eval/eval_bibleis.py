import json
import re
from rapidfuzz import fuzz # fast implementation of levenshtein distance

if __name__ == "__main__":
    # load llm scraped bible
    with open("llm/LLM_BibleIS_HUNK90_GEN.json", "r", encoding="utf-8") as f:
        llm_bible = json.load(f)

    # load bespoke scraper bible
    with open("reference/Bespoke_BibleIS_HUNK90_GEN.txt", "r", encoding="utf-8") as f:
        bespoke_bible = [line.strip() for line in f if line.strip()]

    print("bespoke bible length:", len(bespoke_bible), "\n")

    threshold = 100 # 100, perfect match
    missing = []

    for i, bespoke_entry in enumerate(bespoke_bible):
        # compute scores against all llm entries (vectorized fuzz.ratio)
        best_score = 0
        best_match = None

        for j, llm_entry in enumerate(llm_bible):
            score = fuzz.ratio(bespoke_entry, llm_entry)
            if score > best_score:
                best_score = score
                best_match = llm_entry

        if best_score < threshold:
            missing.append((bespoke_entry, best_match, best_score))

    print("missing entries:", len(missing))
    for bespoke_entry, llm_entry, score in missing:
        print(f"bespoke: {bespoke_entry}")
        print(f"closest llm: {llm_entry}")
        print(f"similarity: {score:.2f}")
        print("-" * 10)

    # keep in mind some mismatches will be trivial, due to punctuation differences, etc.
    # manually inspect the missing entries and determine if they are truly missing

    accuracy = 100 * (len(bespoke_bible) - len(missing)) / len(bespoke_bible)
    print(f"accuracy (before manually filtering out false positives): {accuracy:.2f}%")

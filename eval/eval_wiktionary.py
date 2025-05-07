import json
import re
from rapidfuzz import fuzz # fast implementation of levenshtein distance

if __name__ == "__main__":
    # load llm scraped lemmas
    with open("llm/LLM_Wiktionary_Adyghe_lemmas.json", "r", encoding="utf-8") as f:
        llm_lemmas = json.load(f)

    # load bespoke scraper lemmas
    with open("reference/Bespoke_Wiktionary_Adyghe_lemmas.txt", "r", encoding="utf-8") as f:
        bespoke_lemmas = [line.strip() for line in f if line.strip()]

    print("bespoke lemmas length:", len(bespoke_lemmas), "\n")

    threshold = 100 # 100, perfect match
    missing = []

    for i, bespoke_entry in enumerate(bespoke_lemmas):
        # compute scores against all llm entries (vectorized fuzz.ratio)
        best_score = 0
        best_match = None

        for j, llm_entry in enumerate(llm_lemmas):
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

    accuracy = 100 * (len(bespoke_lemmas) - len(missing)) / len(bespoke_lemmas)
    print(f"accuracy (before manually filtering out false positives): {accuracy:.2f}%")

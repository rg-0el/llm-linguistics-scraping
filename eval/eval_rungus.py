import json

from rapidfuzz import fuzz

if __name__ == "__main__":
    with open("llm/LLM_webonary_org_rungus.json", "r") as f:
        llm_dict = json.load(f)

        print("llm dict length:", len(llm_dict.keys()))
    
    with open("reference/Manual_webonary_org_rungus_partial.json", "r") as f:
        bespoke_dict = json.load(f)

        print("bespoke dict length:", len(bespoke_dict.keys()))

    missing_words = []
    missing_translations = []

    threshold = 100 # 100, perfect match, compute score anyway to see if it's close enough

    for bespoke_key, bespoke_value in bespoke_dict.items():
        if bespoke_key not in llm_dict:
            best_score = 0
            best_match = None

            for j, llm_key in enumerate(llm_dict):
                score = fuzz.ratio(bespoke_key, llm_key)
                if score > best_score:
                    best_score = score
                    best_match = llm_key

            if best_score < threshold:
                missing_words.append((bespoke_key, best_match, best_score))
        else:
            entry = llm_dict[bespoke_key]
            score = fuzz.ratio(str(bespoke_value["translations"]), str(entry["translations"]))
            if score < threshold:
                missing_translations.append((bespoke_key, entry["translations"], bespoke_value["translations"], score))

    print("missing entries:", len(missing_words))
    for bespoke_key, llm_key, score in missing_words:
        print(f"bespoke: {bespoke_key}")
        print(f"closest llm: {llm_key}")
        print(f"similarity: {score:.2f}")
        print("-" * 10)

    print("missing translations:", len(missing_translations))
    for bespoke_key, llm_translations, bespoke_translations, score in missing_translations:
        print(f"bespoke: {bespoke_key}")
        print(f"closest llm: {llm_translations}")
        print(f"bespoke: {bespoke_translations}")
        print(f"similarity: {score:.2f}")
        print("-" * 10)

    # keep in mind some mismatches will be trivial, due to punctuation differences, etc.
    # manually inspect the missing entries and determine if they are truly missing

    accuracy = 100 * (len(bespoke_dict) - len(missing_words)) / len(bespoke_dict)
    print(f"accuracy (before manually filtering out false positives): {accuracy:.2f}%")
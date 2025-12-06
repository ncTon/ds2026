import re
import json

# Input
INPUT_DATA = [
    "Zero-Three Driver!",
    "(Let’s give you power! Let’s give you power!)",
    "Zero-Three Jump!",
    "Zero-Three Rise!",
    "1: One Prediction! 2: Two Intelligence! 3: Three Circles!",
    "Go! Beyond! One, Two, Three!",
    "Kamen Rider Zero-Three!",
    "Is there ark?"
]

# Mapper Function
def mapper(line):
    # Takes a line of text, splits it into words, and emits (word, 1) for each
    # Convert to lowercase and remove non-word characters
    line = line.lower()
    words = re.findall(r'\b\w+\b', line)

    # Output: [('zero', 1), ('three', 1), ...]
    return [(word, 1) for word in words]

# Shuffle/Group Function
def grouper(mapped_pairs):
    # Groups the intermediate (word, 1) pairs by the word (key)
    grouped_data = {}
    for key, value in mapped_pairs:
        # Append the value (which is always 1) to the list for that key
        grouped_data.setdefault(key, []).append(value)
    # Output: {'zero': [1, 1, 1, 1], 'three': [1, 1, 1, 1], ...}
    return grouped_data

# Reducer Function
def reducer(word, counts):
    # Takes a word and a list of '1's, sums the list to get the total count.
    # Output: (word, total_count)
    return (word, sum(counts))

def run_word_count(data):
    # Apply the mapper to every line
    print("Map Phase")
    mapped_results = []
    for line in data:
        mapped_results.extend(mapper(line))

    print(f"Total pairs: {len(mapped_results)}")
    print(mapped_results[:5], "...") # Show the first few pairs

    # Group the pairs by key
    print("\nShuffle and Group Phase")
    grouped_results = grouper(mapped_results)

    print(f"Unique words found: {len(grouped_results)}")
    print("\nGrouped Output:")
    print(json.dumps(grouped_results, indent=4))


    # Apply the reducer to each word and its list of counts
    print("\nReduce Phase")
    final_results = []
    for word, counts in grouped_results.items():
        final_results.append(reducer(word, counts))

    final_output = dict(final_results)
    print("\n--- Final Word Counts ---")
    for word, count in sorted(final_output.items()):
        print(f"'{word}': {count}")

    return final_output

if __name__ == "__main__":
    run_word_count(INPUT_DATA)
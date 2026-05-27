"""
Sentence stimuli for RSVP task.
Each sentence is stored as a dictionary with:

- words: list of words in the sentence
- last_word: the target word
- meaningful: True/False (whether sentence is meaningful)
- cloze_probability: float (predictability measure)
- word_count: int (number of words in sentence)
- correct_response: 1 (meaningful) or 0 (meaningless)
"""

from pathlib import Path
import csv
import random
from utils.logger import get_logger

logger = get_logger("./src/utils/stimulus")

def load_sentences_from_csv(csv_path: Path) -> list[list[dict]]:
    """
    Load sentences from CSV file matching your dataset format.
    
    Expected CSV columns:
    - Sentence: full sentence text (without the last word)
    - LastWord: the target word to be presented
    - Meaningful: True/False indicator
    - cloze_probability: float between 0 and 1
    - word_count: total number of words
    - condition: switching, meaningless, meaningful
    
    :param csv_path: Path to CSV file
    :return: List of sentence dictionaries
    """
    sentences = [[], [], []]
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Item,Condition,Sentence,LastWord,original_dataset,RT_Control,RT_Patient,Gap_Cost,Selection_Criteria,
        # word_count,cloze_probability,word_frequency,Lastword_Count
        for idx, row in enumerate(reader, start=1):
            # Parse sentence stem (all words except last)
            item = row["Item"]
            condition = row["Condition"]
            sentence_stem = row['Sentence'].strip()

            sentence = row['Sentence']
            item_og = row['Item_original']
            og_dataset = row['original_dataset']
            num_letters = row['number_letters']
            word_freq = row['word_frequency']
            spelling_mod = row['spelling_modified']

            stem_words = sentence_stem.split()
            # Get last word
            last_word = (row['LastWord'].strip())
            # Combine into full word list
            words = stem_words + [last_word]
            
            # Parse cloze probability
            cloze_prob = float(row['cloze_probability'])
            
            # Parse word count
            word_count = int(row['word_count'])

            meaningful = row['Meaningful'].strip().lower() == 'true'
            
            # Correct response: 1 = meaningful, 2 = meaningless
            correct_response = "d" if meaningful else "k"

            # Block 1 sentences
            if int(row['block_order']) == 1:
                sentences[1].append({
                    'id': idx,
                    'words': words,
                    'last_word': last_word,
                    'meaningful': meaningful,
                    'cloze_probability': cloze_prob,
                    'word_count': word_count,
                    'condition': condition,
                    'sentence': sentence,
                    'item_og': item_og,
                    'og_dataset': og_dataset,
                    'num_letters': num_letters,
                    'word_freq': word_freq,
                    'spelling_mod': spelling_mod,
                    'correct_response': correct_response,
                    'full_sentence': ' '.join(words)
                })
            # Block 2 sentences
            elif int(row['block_order']) == 2:
                sentences[2].append({
                    'id': idx,
                    'words': words,
                    'last_word': last_word,
                    'meaningful': meaningful,
                    'cloze_probability': cloze_prob,
                    'word_count': word_count,
                    'condition': condition,
                    'sentence': sentence,
                    'item_og': item_og,
                    'og_dataset': og_dataset,
                    'num_letters': num_letters,
                    'word_freq': word_freq,
                    'spelling_mod': spelling_mod,
                    'correct_response': correct_response,
                    'full_sentence': ' '.join(words)
                })
            # Practice block sentences
            else:
                sentences[0].append({
                    'id': idx,
                    'words': words,
                    'last_word': last_word,
                    'meaningful': meaningful,
                    'cloze_probability': cloze_prob,
                    'word_count': word_count,
                    'condition': condition,
                    'sentence': sentence,
                    'item_og': item_og,
                    'og_dataset': og_dataset,
                    'num_letters': num_letters,
                    'word_freq': word_freq,
                    'spelling_mod': spelling_mod,
                    'correct_response': correct_response,
                    'full_sentence': ' '.join(words)
                })
    
    logger.info(f"{len(sentences)} blocks | {len(sentences[1])} in Block 1 | {len(sentences[2])} in Block 2")
    
    return sentences

def _compute_sentence_presentation(pid: str) -> str:
    '''
    To ensure counterbalancing, we need an A-B-B-A scheme crossed with the joystick mapping. To implement this, 
    use the participant’s ID number, divide it by 4, and follow this remainder-based rule:
        - If the remainder is 0 or 1, use List A.
        - If the remainder is 2 or 3, use List B
    '''
    if not pid:
        return "A"
    last = pid[-1]
    if last.isdigit(): 
        return "A" if (int(last) % 4 == 0)  or (int(last) % 4 == 1) else "B"
    return "A"

def randomShuffle(sentences: list[dict]) -> list[list[dict]]:
    random.shuffle(sentences)
    
    mid_index = len(sentences) // 2
    block1 = sentences[:mid_index]
    block2 = sentences[mid_index:]
    blocked_sentences = [block1, block2]

    return blocked_sentences

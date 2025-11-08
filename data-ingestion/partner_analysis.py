import re
from collections import Counter

with open('current_index_verification.txt', 'r') as f:
    content = f.read()

# Extract partner names
partners = re.findall(r'\(by ([^)]+)\)', content)

# Normalize partner names
normalized = []
for p in partners:
    p_clean = p.strip()
    # Merge variations
    if 'RSM' in p_clean:
        p_clean = 'RSM'
    elif 'Cognizant' in p_clean:
        p_clean = 'Cognizant'
    elif 'HCL' in p_clean:
        p_clean = 'HCLTech'
    elif 'Wipro' in p_clean:
        p_clean = 'Wipro'
    elif 'Tata Consultancy' in p_clean or p_clean == 'TCS':
        p_clean = 'TCS'
    elif 'Finastra' in p_clean:
        p_clean = 'Finastra'
    elif 'Terawe' in p_clean:
        p_clean = 'Terawe Corporation'
    elif 'Anthology' in p_clean:
        p_clean = 'Anthology'
    elif 'Adobe' in p_clean:
        p_clean = 'Adobe'
    normalized.append(p_clean)

# Count and sort
counter = Counter(normalized)
print("\n=== TOP 25 MOST PROLIFIC PARTNERS ON ISD ===\n")
for i, (partner, count) in enumerate(counter.most_common(25), 1):
    print(f"{i:2}. {partner:45} {count:3} solutions")

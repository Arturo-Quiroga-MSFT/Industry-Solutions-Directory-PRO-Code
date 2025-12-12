
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential
from collections import Counter, defaultdict

credential = DefaultAzureCredential()
endpoint = 'https://indsolse-dev-srch-okumlm.search.windows.net'
index_name = 'partner-solutions-integrated'

search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

print('Fetching all documents from index...')
results = search_client.search(
    search_text='*',
    select=['solution_name', 'partner_name', 'industries', 'technologies', 'description'],
    top=1000
)

solutions = list(results)
print(f'Total documents in index: {len(solutions)}')

# Normalize partner names
def normalize_partner(name):
    if not name:
        return None
    name = name.strip()
    if 'RSM' in name:
        return 'RSM'
    elif 'Cognizant' in name:
        return 'Cognizant'
    elif 'HCL' in name:
        return 'HCLTech'
    elif 'Wipro' in name:
        return 'Wipro'
    elif 'Tata Consultancy' in name or name == 'TCS':
        return 'TCS'
    elif 'Finastra' in name:
        return 'Finastra'
    elif 'Terawe' in name:
        return 'Terawe Corporation'
    elif 'Anthology' in name:
        return 'Anthology'
    elif 'Adobe' in name:
        return 'Adobe'
    return name

# Count unique solutions per partner
partner_solutions = defaultdict(set)
solutions_with_content = 0
industries_set = set()
technologies_set = set()

for doc in solutions:
    solution_name = doc.get('solution_name', '').strip()
    partner_name = normalize_partner(doc.get('partner_name'))
    description = doc.get('description', '').strip()
    
    if solution_name and description:
        solutions_with_content += 1
    
    if solution_name and partner_name:
        partner_solutions[partner_name].add(solution_name)
    
    industries = doc.get('industries', '')
    technologies = doc.get('technologies', '')
    
    if industries:
        for ind in str(industries).split(','):
            if ind.strip():
                industries_set.add(ind.strip())
    
    if technologies:
        for tech in str(technologies).split(','):
            if tech.strip():
                technologies_set.add(tech.strip())

# Calculate statistics
partner_counts = {partner: len(solutions) for partner, solutions in partner_solutions.items()}
total_unique_solutions = sum(len(sols) for sols in partner_solutions.values())

print(f'Solutions with content: {solutions_with_content}')
print(f'Total unique solutions: {total_unique_solutions}')
print(f'Number of partners: {len(partner_solutions)}')
print(f'Unique industries: {len(industries_set)}')
print(f'Unique technologies: {len(technologies_set)}')

print('\\n=== TOP 25 PARTNERS ===')
sorted_partners = sorted(partner_counts.items(), key=lambda x: x[1], reverse=True)
for rank, (partner, count) in enumerate(sorted_partners[:25], 1):
    print(f'{rank}. {partner}: {count}')

print(f'\\n=== INDUSTRIES ({len(industries_set)}) ===')
for ind in sorted(industries_set):
    print(f'  - {ind}')

print(f'\\n=== TECHNOLOGIES ({len(technologies_set)}) ===')
for tech in sorted(technologies_set):
    print(f'  - {tech}')

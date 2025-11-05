curl -s "https://solutions.microsoftindustryinsights.com/main-QIRD4JU5.js" | tr ';' '\n' | grep -i 'http.*api' | grep mssoldir | head -10

curl -s "https://solutions.microsoftindustryinsights.com/main-QIRD4JU5.js" | grep -o 'baseApi[^,}]*' | head -20

# this found the baseApi variable
curl -s "https://solutions.microsoftindustryinsights.com/main-QIRD4JU5.js" | grep -o 'baseApi[^,}]*' | head -20
curl -s "https://solutions.microsoftindustryinsights.com/main-QIRD4JU5.js" | tr ',' '\n' | grep -i 'baseurl\|baseapi' | head -10

# this found the actual URL
curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry/GetIndustryList" | python3 -m json.tool | head -50

curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry/GetIndustryThemeList" | python3 -m json.tool 2>&1 | head -100


INDUSTRY_ID="aaec8f6a-e3f1-4632-bf12-86dd2bfa0aaf" && curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry/GetPartnerSolutionByIndustry?industryId=${INDUSTRY_ID}" | python3 -m json.tool 2>&1 | head -150

curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry/getMenu" | python3 -m json.tool 2>&1 | head -200

curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry/getMenu" > /tmp/menu.json && echo "Saved menu data. Testing with first theme slug..." && python3 << 'EOF'
import json
with open('/tmp/menu.json') as f:
    menu = json.load(f)

# Get first industry with themes
for ind in menu:
    if ind['hasSubMenu'] and ind['subIndustries']:
        for sub in ind['subIndustries']:
            if sub.get('industryThemeSlug'):
                print(f"\nIndustry: {ind['industryName']}")
                print(f"SubIndustry: {sub['subIndustryName']}")
                print(f"ThemeSlug: {sub['industryThemeSlug']}")
                print(f"SubIndustrySlug: {sub['subIndustrySlug']}")
                break
        break
EOF

# this found the partner solutions, see the output in file solution-found.json
# Excellent! Found the partner solutions! The GetThemeDetalsByViewId endpoint returns the actual partner solutions. 
curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry/GetThemeDetalsByViewId?slug=improve-operational-efficiencies-for-modernized-school-experiences-850" 2>&1 | python3 -m json.tool | head -500

#this did the trick to get the partner solutions for a given theme slug
curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry/getMenu" > /tmp/menu.json && python3 << 'EOF'
import json

with open('/tmp/menu.json') as f:
    menu = json.load(f)

print(f"Total industries: {len(menu)}")
print(f"\nSample industry theme slugs to use:")
for industry in menu[:3]:
    print(f"\n{industry['industryName']}:")
    for sub in industry['subIndustries'][:2]:
        if sub.get('industryThemeSlug'):
            print(f"  - {sub['industryThemeSlug']}")
EOF

# this one shows that The solutions are nested within themeSolutionAreas → partnerSolutions
curl -s "https://mssoldir-app-prd.azurewebsites.net/api/Industry/GetThemeDetalsByViewId?slug=improve-operational-efficiencies-for-modernized-school-experiences-850" | python3 -c "import sys, json; data=json.load(sys.stdin); print('spotLightPartnerSolutions:', len(data.get('spotLightPartnerSolutions', []))); print('themeSolutionAreas count:', len(data.get('themeSolutionAreas', []))); areas = data.get('themeSolutionAreas', []); print('\nSolution areas:'); [print(f\"  - {a.get('solutionAreaName')}: {len(a.get('partnerSolutions', []))} solutions\") for a in areas[:5]]"
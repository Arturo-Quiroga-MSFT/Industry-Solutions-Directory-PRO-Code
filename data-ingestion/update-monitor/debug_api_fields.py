import requests
import json

base_url = 'https://mssoldir-app-prd.azurewebsites.net/api/Industry'
menu_url = f'{base_url}/getMenu'
menu_response = requests.get(menu_url, timeout=30)
menu_data = menu_response.json()

# Get first industry and theme
industry = menu_data[0]
theme = industry.get('subIndustries', [])[0]
theme_slug = theme.get('industryThemeSlug')

print(f"Industry: {industry.get('industryName')}")
print(f"Theme: {theme.get('subIndustryName')}")
print(f"Theme slug: {theme_slug}\n")

# Fetch solutions for this theme
theme_url = f'{base_url}/GetThemeDetalsByViewId'
params = {'slug': theme_slug}
theme_response = requests.get(theme_url, params=params, timeout=30)
theme_data = theme_response.json()

# Get first solution
theme_solution_areas = theme_data.get('themeSolutionAreas', [])
if theme_solution_areas:
    area = theme_solution_areas[0]
    print(f"Solution Area: {area.get('solutionAreaName')}\n")
    partner_solutions = area.get('partnerSolutions', [])
    if partner_solutions:
        print('Sample solution (first 3):')
        for i, sol in enumerate(partner_solutions[:3], 1):
            print(f"\n{i}. Available fields:")
            for key in sol.keys():
                value = sol[key]
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"   {key}: {value}")

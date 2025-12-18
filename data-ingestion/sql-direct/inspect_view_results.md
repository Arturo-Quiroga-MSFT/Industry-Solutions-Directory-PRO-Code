 cd /Use
rs/arturoquiroga/Industry-Solutions-Directory-PRO-Code/data-ingestion/sql-direct
 && python inspect_view.py

================================================================================
Inspecting View: dbo.vw_ISDSolution_All
================================================================================

View Structure:

Column Name                              Type                 Max Length   Nullable  
-------------------------------------------------------------------------------------
SolutionType                             varchar              11           NO        
solutionName                             varchar              8000         YES       
solutionDescription                      varchar              -1           YES       
solutionOrgWebsite                       nvarchar             500          YES       
marketPlaceLink                          varchar              1000         YES       
specialOfferLink                         varchar              1000         YES       
logoFileLink                             varchar              -1           YES       
industryName                             varchar              100          YES       
industryDescription                      varchar              1000         YES       
subIndustryName                          varchar              100          YES       
SubIndustryDescription                   varchar              8000         YES       
solutionAreaName                         varchar              100          YES       
solAreaDescription                       varchar              1000         YES       
solutionPlayName                         varchar              8000         YES       
solutionPlayDesc                         varchar              -1           YES       
solutionPlayLabel                        varchar              200          YES       
areaSolutionDescription                  varchar              -1           YES       
geoName                                  varchar              100          YES       
resourceLinkTitle                        varchar              1000         YES       
resourceLinkUrl                          varchar              1000         YES       
resourceLinkName                         varchar              100          YES       
resourceLinkDescription                  varchar              1000         YES       
orgName                                  varchar              500          YES       
orgDescription                           varchar              1000         YES       
userType                                 varchar              50           YES       
solutionStatus                           nvarchar             50           YES       
displayLabel                             nvarchar             50           YES       
theme                                    varchar              8000         YES       
industryThemeDesc                        varchar              -1           YES       
image_thumb                              varchar              1000         YES       
image_main                               varchar              1000         YES       
image_mobile                             varchar              1000         YES       

Sample Data (first 5 rows):

Row:
  SolutionType                  : Industry
  solutionName                  : Life Sciences Catalyst: 1-Day Workshop
  solutionDescription           : <div class="SCXW139926052 BCX8"><div class="OutlineElement Ltr SCXW139926052 BCX8"><p class="Paragra
  solutionOrgWebsite            : https://rsmus.com/
  marketPlaceLink               : https://appsource.microsoft.com/hr-hr/marketplace/consulting-services/rsmproductsalesllc160468595827
  specialOfferLink              : 
  logoFileLink                  : https://mssoldirdevstorage1.blob.core.windows.net/dev/f4b90605-fc17-4969-8ca9-a3047c0ab914.png
  industryName                  : Healthcare & Life Sciences
  industryDescription           : <h1>Partner solutions designed for health and life sciences<h1><p>Explore this curated directory of 
  subIndustryName               : Enhance Patient and Member Experiences
  SubIndustryDescription        : <p>Explore this curated directory of industry-leading Microsoft partner solutions to help your healt
  solutionAreaName              : AI Business Solutions
  solAreaDescription            : <div>AI Business Solutions is a Microsoft solution play that brings together Modern Work and Busines
  solutionPlayName              : NULL
  solutionPlayDesc              : NULL
  solutionPlayLabel             : NULL
  geoName                       : United States
  orgName                       : RSM US LLP
  userType                      : Partner
  solutionStatus                : Approved
  displayLabel                  : Approved
  theme                         : Enhance Patient and Member Experiences
  industryThemeDesc             : <p><span>Enhancing patient and member experiences is a top priority for healthcare providers, as it 
  image_thumb                   : https://mssoldirdevstorage1.blob.core.windows.net/dev/e64bf14b-8236-46b7-a9c3-8d3562578f22.jpg
  image_main                    : https://mssoldirdevstorage1.blob.core.windows.net/dev/ae6d9b57-955c-47b0-8c49-e305e689669b.jpg
  image_mobile                  : https://mssoldirdevstorage1.blob.core.windows.net/dev/1d14be6e-d45f-4637-a61b-540131913798.jpg

Row:
  SolutionType                  : Industry
  solutionName                  : Life Sciences Catalyst: 2-Week Workshop
  solutionDescription           : <div class="OutlineElement Ltr SCXW219437372 BCX8"><p class="Paragraph SCXW219437372 BCX8"><span lan
  solutionOrgWebsite            : https://rsmus.com/
  marketPlaceLink               : https://appsource.microsoft.com/en-us/marketplace/consulting-services/rsmproductsalesllc160468595827
  specialOfferLink              : 
  logoFileLink                  : https://mssoldirdevstorage1.blob.core.windows.net/dev/a45178b9-1632-4e9e-9a54-d6d23b1ca08a.png
  industryName                  : Healthcare & Life Sciences
  industryDescription           : <h1>Partner solutions designed for health and life sciences<h1><p>Explore this curated directory of 
  subIndustryName               : Enhance Patient and Member Experiences
  SubIndustryDescription        : <p>Explore this curated directory of industry-leading Microsoft partner solutions to help your healt
  solutionAreaName              : AI Business Solutions
  solAreaDescription            : <div>AI Business Solutions is a Microsoft solution play that brings together Modern Work and Busines
  solutionPlayName              : NULL
  solutionPlayDesc              : NULL
  solutionPlayLabel             : NULL
  geoName                       : United States
  orgName                       : RSM US LLP
  userType                      : Partner
  solutionStatus                : Approved
  displayLabel                  : Approved
  theme                         : Enhance Patient and Member Experiences
  industryThemeDesc             : <p><span>Enhancing patient and member experiences is a top priority for healthcare providers, as it 
  image_thumb                   : https://mssoldirdevstorage1.blob.core.windows.net/dev/e64bf14b-8236-46b7-a9c3-8d3562578f22.jpg
  image_main                    : https://mssoldirdevstorage1.blob.core.windows.net/dev/ae6d9b57-955c-47b0-8c49-e305e689669b.jpg
  image_mobile                  : https://mssoldirdevstorage1.blob.core.windows.net/dev/1d14be6e-d45f-4637-a61b-540131913798.jpg

Row:
  SolutionType                  : Industry
  solutionName                  : RFP & Grant AI Writing Assistant
  solutionDescription           : <div class="OutlineElement Ltr SCXW224884068 BCX8"><p class="Paragraph SCXW224884068 BCX8"><span lan
  solutionOrgWebsite            : https://rsmus.com/technologies/microsoft/industries/state-and-local.html
  marketPlaceLink               : https://appsource.microsoft.com/en-us/product/web-apps/rsmproductsalesllc1604685958273.rfpgrantaiwri
  specialOfferLink              : 
  logoFileLink                  : https://mssoldirdevstorage1.blob.core.windows.net/dev/3e8b157d-e1b9-47c3-add9-3f9ed0d9f25d.png
  industryName                  : State & Local Government
  industryDescription           : <h1>Partner solutions designed for government<h1><p>Explore this curated directory of Microsoft solu
  subIndustryName               : Enable AI-Driven Decision Making
  SubIndustryDescription        : <font color="#fdfdfd">Explore this curated directory of industry-leading Microsoft partner solutions
  solutionAreaName              : Cloud and AI Platforms
  solAreaDescription            : <div>Explore this curated directory of Microsoft solution partners all equipped to help organization
  solutionPlayName              : NULL
  solutionPlayDesc              : NULL
  solutionPlayLabel             : NULL
  geoName                       : United States
  orgName                       : RSM US LLP
  userType                      : Partner
  solutionStatus                : Approved
  displayLabel                  : Approved
  theme                         : Enable AI-Driven Decision Making
  industryThemeDesc             : <p class="MsoNormal">Turn data into action with Microsoft partners and unlock the full potential of 
  image_thumb                   : https://mssoldirdevstorage1.blob.core.windows.net/dev/fc2f3a68-ad89-4b3f-9929-4f84e9f1f7d2.jpg
  image_main                    : https://mssoldirdevstorage1.blob.core.windows.net/dev/3aac949c-2da4-438b-b3ce-dff8f89fed46.jpg
  image_mobile                  : https://mssoldirdevstorage1.blob.core.windows.net/dev/dc2ddf78-2e41-471c-96f2-56e47920f5d9.jpg

Row:
  SolutionType                  : Industry
  solutionName                  : RFP & Grant AI Writing Assistant
  solutionDescription           : <div class="OutlineElement Ltr SCXW224884068 BCX8"><p class="Paragraph SCXW224884068 BCX8"><span lan
  solutionOrgWebsite            : https://rsmus.com/technologies/microsoft/industries/state-and-local.html
  marketPlaceLink               : https://appsource.microsoft.com/en-us/product/web-apps/rsmproductsalesllc1604685958273.rfpgrantaiwri
  specialOfferLink              : 
  logoFileLink                  : https://mssoldirdevstorage1.blob.core.windows.net/dev/3e8b157d-e1b9-47c3-add9-3f9ed0d9f25d.png
  industryName                  : State & Local Government
  industryDescription           : <h1>Partner solutions designed for government<h1><p>Explore this curated directory of Microsoft solu
  subIndustryName               : Enable AI-Driven Decision Making
  SubIndustryDescription        : <font color="#fdfdfd">Explore this curated directory of industry-leading Microsoft partner solutions
  solutionAreaName              : Cloud and AI Platforms
  solAreaDescription            : <div>Explore this curated directory of Microsoft solution partners all equipped to help organization
  solutionPlayName              : NULL
  solutionPlayDesc              : NULL
  solutionPlayLabel             : NULL
  geoName                       : Canada
  orgName                       : RSM US LLP
  userType                      : Partner
  solutionStatus                : Approved
  displayLabel                  : Approved
  theme                         : Enable AI-Driven Decision Making
  industryThemeDesc             : <p class="MsoNormal">Turn data into action with Microsoft partners and unlock the full potential of 
  image_thumb                   : https://mssoldirdevstorage1.blob.core.windows.net/dev/fc2f3a68-ad89-4b3f-9929-4f84e9f1f7d2.jpg
  image_main                    : https://mssoldirdevstorage1.blob.core.windows.net/dev/3aac949c-2da4-438b-b3ce-dff8f89fed46.jpg
  image_mobile                  : https://mssoldirdevstorage1.blob.core.windows.net/dev/dc2ddf78-2e41-471c-96f2-56e47920f5d9.jpg

Row:
  SolutionType                  : Industry
  solutionName                  : RSM Copilot for Service
  solutionDescription           : <div class="OutlineElement Ltr SCXW184149290 BCX8"><p class="Paragraph SCXW184149290 BCX8"><span lan
  solutionOrgWebsite            : https://rsmus.com/technologies/microsoft/industries/state-and-local.html
  marketPlaceLink               : https://appsource.microsoft.com/en-us/marketplace/consulting-services/rsmproductsalesllc160468595827
  specialOfferLink              : 
  logoFileLink                  : https://mssoldirdevstorage1.blob.core.windows.net/dev/8fcd96f3-cae1-4113-8ebe-40a26733d590.png
  industryName                  : State & Local Government
  industryDescription           : <h1>Partner solutions designed for government<h1><p>Explore this curated directory of Microsoft solu
  subIndustryName               : Enable AI-Driven Decision Making
  SubIndustryDescription        : <font color="#fdfdfd">Explore this curated directory of industry-leading Microsoft partner solutions
  solutionAreaName              : Cloud and AI Platforms
  solAreaDescription            : <div>Explore this curated directory of Microsoft solution partners all equipped to help organization
  solutionPlayName              : NULL
  solutionPlayDesc              : NULL
  solutionPlayLabel             : NULL
  geoName                       : United States
  resourceLinkTitle             : Revolutionizing Customer Support with Microsoft Copilot: A New Era for Service Teams
  resourceLinkUrl               : https://technologyblog.rsmus.com/public-sector-hhc/revolutionizing-customer-support-with-microsoft-c
  resourceLinkName              : Blog
  resourceLinkDescription       : Blog
  orgName                       : RSM US LLP
  userType                      : Partner
  solutionStatus                : Approved
  displayLabel                  : Approved
  theme                         : Enable AI-Driven Decision Making
  industryThemeDesc             : <p class="MsoNormal">Turn data into action with Microsoft partners and unlock the full potential of 
  image_thumb                   : https://mssoldirdevstorage1.blob.core.windows.net/dev/fc2f3a68-ad89-4b3f-9929-4f84e9f1f7d2.jpg
  image_main                    : https://mssoldirdevstorage1.blob.core.windows.net/dev/3aac949c-2da4-438b-b3ce-dff8f89fed46.jpg
  image_mobile                  : https://mssoldirdevstorage1.blob.core.windows.net/dev/dc2ddf78-2e41-471c-96f2-56e47920f5d9.jpg


Total rows in view: 5118

================================================================================
✓ View inspection complete!
================================================================================

(base) arturoquiroga@ARTUROs-MBP sql-direct % 
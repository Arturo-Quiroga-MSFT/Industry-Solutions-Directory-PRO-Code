# Database Schema Report
**Database**: mssoldir-prd
**Server**: mssoldir-prd-sql.database.windows.net
**Inspection Date**: 2026-03-09T10:31:04.994284
**Total Tables**: 45
---

## Table of Contents

- [dbo.ArchiveIndustryTheme](#dbo-ArchiveIndustryTheme)
- [dbo.ArchiveSubIndustry](#dbo-ArchiveSubIndustry)
- [dbo.geo](#dbo-geo)
- [dbo.Industry](#dbo-Industry)
- [dbo.IndustryResourceLink](#dbo-IndustryResourceLink)
- [dbo.IndustryShowcasePartnerSolution](#dbo-IndustryShowcasePartnerSolution)
- [dbo.IndustryTargetCustomerProspect](#dbo-IndustryTargetCustomerProspect)
- [dbo.IndustryTheme](#dbo-IndustryTheme)
- [dbo.IndustryThemeBySolutionArea](#dbo-IndustryThemeBySolutionArea)
- [dbo.organization](#dbo-organization)
- [dbo.partnerSolution](#dbo-partnerSolution)
- [dbo.PartnerSolutionAvailableGeo](#dbo-PartnerSolutionAvailableGeo)
- [dbo.partnerSolutionByArea](#dbo-partnerSolutionByArea)
- [dbo.partnerSolutionPlay](#dbo-partnerSolutionPlay)
- [dbo.PartnerSolutionPlayAvailableGeo](#dbo-PartnerSolutionPlayAvailableGeo)
- [dbo.partnerSolutionPlayByPlay](#dbo-partnerSolutionPlayByPlay)
- [dbo.partnerSolutionPlayResourceLink](#dbo-partnerSolutionPlayResourceLink)
- [dbo.partnerSolutionResourceLink](#dbo-partnerSolutionResourceLink)
- [dbo.partnerUser](#dbo-partnerUser)
- [dbo.partneruser_bkup05202204](#dbo-partneruser_bkup05202204)
- [dbo.partneruser_bkup05312204](#dbo-partneruser_bkup05312204)
- [dbo.resourceLink](#dbo-resourceLink)
- [dbo.solution_Del](#dbo-solution_Del)
- [dbo.solutionArea](#dbo-solutionArea)
- [dbo.solutionPlay](#dbo-solutionPlay)
- [dbo.SolutionStatus](#dbo-SolutionStatus)
- [dbo.Spotlight](#dbo-Spotlight)
- [dbo.SubIndustry](#dbo-SubIndustry)
- [dbo.TechnologyShowcasePartnerSolution](#dbo-TechnologyShowcasePartnerSolution)
- [dbo.usecaseOrganization](#dbo-usecaseOrganization)
- [dbo.user](#dbo-user)
- [dbo.UserInvite](#dbo-UserInvite)
- [dbo.userOtp](#dbo-userOtp)
- [stage.indusrytheme](#stage-indusrytheme)
- [stage.industry](#stage-industry)
- [stage.IndustryShowcasePartnerSolution](#stage-IndustryShowcasePartnerSolution)
- [stage.organization](#stage-organization)
- [stage.partnerSolution](#stage-partnerSolution)
- [stage.PartnerSolutionAvailableGeo](#stage-PartnerSolutionAvailableGeo)
- [stage.partnerSolutionByArea](#stage-partnerSolutionByArea)
- [stage.partnerSolutionResourceLink](#stage-partnerSolutionResourceLink)
- [stage.partneruser](#stage-partneruser)
- [stage.solutionarea](#stage-solutionarea)
- [stage.solutionstatus](#stage-solutionstatus)
- [stage.subindustry](#stage-subindustry)

---

## dbo.ArchiveIndustryTheme

**Row Count**: 1

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| industryThemeId | uniqueidentifier | No | - |
| industryId | uniqueidentifier | Yes | - |
| subIndustryId | uniqueidentifier | Yes | - |
| partnerId | uniqueidentifier | Yes | - |
| Theme | varchar(8000) | Yes | - |
| industryThemeDesc | varchar(-1) | Yes | - |
| imageFileLink | varchar(500) | Yes | - |
| status | varchar(100) | Yes | - |
| isPublished | nvarchar(1) | Yes | - |
| rowChangedBy | uniqueidentifier | Yes | - |
| rowChangedDate | datetime | Yes | - |
| image_thumb | varchar(1000) | Yes | - |
| image_main | varchar(1000) | Yes | - |
| image_mobile | varchar(1000) | Yes | - |
| solutionStatusId | uniqueidentifier | Yes | - |
| industryThemeSlug | varchar(500) | Yes | - |

---

## dbo.ArchiveSubIndustry

**Row Count**: 1

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| SubIndustryId | uniqueidentifier | No | - |
| IndustryId | uniqueidentifier | No | - |
| SubIndustryName | varchar(100) | No | - |
| SubIndustryDescription | varchar(8000) | Yes | - |
| Status | varchar(25) | Yes | - |
| RowChangedBy | uniqueidentifier | Yes | - |
| RowChangedDate | datetime | Yes | - |
| SubIndustrySlug | varchar(500) | Yes | - |

---

## dbo.geo

**Row Count**: 3

**Primary Keys**: geoId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 geoId | uniqueidentifier | No | - |
| locale | varchar(100) | No | - |
| geoname | varchar(100) | No | - |
| geodescription | varchar(1000) | Yes | - |
| DisplayOrder | int | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | date | Yes | - |

---

## dbo.Industry

**Row Count**: 11

**Primary Keys**: IndustryId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 IndustryId | uniqueidentifier | No | - |
| IndustryName | varchar(100) | No | - |
| IndustryDescription | varchar(1000) | Yes | - |
| Status | varchar(25) | No | - |
| RowChangedBy | varchar(200) | Yes | - |
| RowChangedDate | datetime | Yes | - |
| IndustrySlug | varchar(500) | Yes | - |
| image_main | varchar(500) | Yes | - |
| image_mobile | varchar(250) | Yes | - |

---

## dbo.IndustryResourceLink

**Row Count**: 13

**Primary Keys**: IndustryResourceLinkId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 IndustryResourceLinkId | uniqueidentifier | No | - |
| industryThemeId | uniqueidentifier | Yes | - |
| resourceLinkId | uniqueidentifier | Yes | - |
| title | varchar(500) | Yes | - |
| resourceLink | varchar(1000) | Yes | - |
| status | varchar(100) | Yes | - |
| rowChangedBy | varchar(1000) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## dbo.IndustryShowcasePartnerSolution

**Row Count**: 49

**Primary Keys**: IndustryShowcasePartnerSolutionId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 IndustryShowcasePartnerSolutionId | uniqueidentifier | No | - |
| industryThemeId | uniqueidentifier | Yes | - |
| partnerId | uniqueidentifier | Yes | - |
| marketplaceLink | varchar(1000) | Yes | - |
| status | varchar(100) | Yes | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |
| PartnerName | varchar(250) | No | - |
| websiteLink | varchar(200) | Yes | - |
| overviewDescription | varchar(-1) | Yes | - |
| logoFileLink | varchar(1000) | Yes | - |
| PartnerNameSlug | varchar(200) | Yes | - |

---

## dbo.IndustryTargetCustomerProspect

**Row Count**: 102

**Primary Keys**: IndustryTargetCustomerProspectId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 IndustryTargetCustomerProspectId | uniqueidentifier | No | - |
| industryThemeId | uniqueidentifier | Yes | - |
| targetPersonaTitle | varchar(1000) | Yes | - |
| status | varchar(100) | Yes | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## dbo.IndustryTheme

**Row Count**: 40

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| industryThemeId | uniqueidentifier | No | - |
| industryId | uniqueidentifier | Yes | - |
| subIndustryId | uniqueidentifier | Yes | - |
| partnerId | uniqueidentifier | Yes | - |
| Theme | varchar(8000) | Yes | - |
| industryThemeDesc | varchar(-1) | Yes | - |
| imageFileLink | varchar(500) | Yes | - |
| status | varchar(100) | Yes | - |
| isPublished | nvarchar(1) | Yes | - |
| rowChangedBy | uniqueidentifier | Yes | - |
| rowChangedDate | datetime | Yes | - |
| image_thumb | varchar(1000) | Yes | - |
| image_main | varchar(1000) | Yes | - |
| image_mobile | varchar(1000) | Yes | - |
| solutionStatusId | uniqueidentifier | Yes | - |
| industryThemeSlug | varchar(500) | Yes | - |

---

## dbo.IndustryThemeBySolutionArea

**Row Count**: 109

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| IndustryThemeBySolutionAreaId | uniqueidentifier | No | - |
| industryThemeId | uniqueidentifier | Yes | - |
| solutionAreaId | uniqueidentifier | Yes | - |
| solutionDesc | varchar(-1) | Yes | - |
| status | varchar(100) | Yes | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## dbo.organization

**Row Count**: 350

**Primary Keys**: orgId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 orgId | uniqueidentifier | No | - |
| orgName | varchar(500) | No | - |
| orgDescription | varchar(1000) | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |
| logoFileLink | varchar(1000) | Yes | - |
| orgWebsite | varchar(500) | Yes | - |
| UserType | varchar(50) | Yes | - |

---

## dbo.partnerSolution

**Row Count**: 566

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| partnerSolutionId | uniqueidentifier | No | - |
| UserId | uniqueidentifier | No | - |
| IndustryId | uniqueidentifier | Yes | - |
| SubIndustryId | uniqueidentifier | Yes | - |
| OrganizationId | uniqueidentifier | Yes | - |
| solutionName | varchar(8000) | Yes | - |
| solutionDescription | varchar(-1) | Yes | - |
| solutionOrgWebsite | nvarchar(500) | Yes | - |
| marketplaceLink | varchar(1000) | Yes | - |
| specialOfferLink | varchar(1000) | Yes | - |
| logoFileLink | varchar(-1) | Yes | - |
| SolutionStatusId | uniqueidentifier | No | - |
| IsPublished | int | Yes | - |
| rowChangedBy | uniqueidentifier | Yes | - |
| rowChangedDate | datetime | Yes | - |
| partnerSolutionSlug | varchar(500) | Yes | - |
| IndustryDesignation | int | Yes | - |
| ParentsolutionId | varchar(100) | Yes | - |
| rowCreatedDate | datetime | Yes | - |

---

## dbo.PartnerSolutionAvailableGeo

**Row Count**: 1,279

**Primary Keys**: PartnerSolutionAvailableGeoId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 PartnerSolutionAvailableGeoId | uniqueidentifier | No | - |
| PartnerSolutionId | uniqueidentifier | No | - |
| GeoId | uniqueidentifier | No | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | date | Yes | - |

---

## dbo.partnerSolutionByArea

**Row Count**: 750

**Primary Keys**: partnerSolutionByAreaId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 partnerSolutionByAreaId | uniqueidentifier | No | - |
| partnerSolutionId | uniqueidentifier | No | - |
| solutionAreaId | uniqueidentifier | No | - |
| areaSolutionDescription | varchar(-1) | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## dbo.partnerSolutionPlay

**Row Count**: 106

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| partnerSolutionPlayId | uniqueidentifier | No | - |
| solutionAreaId | uniqueidentifier | No | - |
| orgId | uniqueidentifier | No | - |
| partnerSolutionPlaySlug | varchar(200) | Yes | - |
| solutionPlayName | varchar(8000) | Yes | - |
| solutionPlayDescription | varchar(-1) | Yes | - |
| solutionPlayOrgWebsite | nvarchar(500) | Yes | - |
| marketplaceLink | varchar(1000) | Yes | - |
| specialOfferLink | varchar(1000) | Yes | - |
| logoFileLink | varchar(-1) | Yes | - |
| SolutionStatusId | uniqueidentifier | No | - |
| IsPublished | int | Yes | - |
| rowChangedBy | uniqueidentifier | Yes | - |
| rowChangedDate | datetime | Yes | - |
| image_thumb | varchar(500) | Yes | - |
| image_main | varchar(500) | Yes | - |
| image_mobile | varchar(500) | Yes | - |
| IndustryDesignation | int | Yes | - |

---

## dbo.PartnerSolutionPlayAvailableGeo

**Row Count**: 252

**Primary Keys**: PartnerSolutionPlayAvailableGeoId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 PartnerSolutionPlayAvailableGeoId | uniqueidentifier | No | - |
| PartnerSolutionPlayId | uniqueidentifier | No | - |
| GeoId | uniqueidentifier | No | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | date | Yes | - |

---

## dbo.partnerSolutionPlayByPlay

**Row Count**: 106

**Primary Keys**: partnerSolutionPlayByPlayId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 partnerSolutionPlayByPlayId | uniqueidentifier | No | - |
| partnerSolutionPlayId | uniqueidentifier | Yes | - |
| solutionPlayId | uniqueidentifier | Yes | - |
| playSolutionDescription | varchar(-1) | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## dbo.partnerSolutionPlayResourceLink

**Row Count**: 239

**Primary Keys**: partnerSolutionPlayResourceLinkId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 partnerSolutionPlayResourceLinkId | uniqueidentifier | No | - |
| partnerSolutionPlayByPlayId | uniqueidentifier | No | - |
| resourceLinkId | uniqueidentifier | No | - |
| resourceLinkTitle | varchar(1000) | No | - |
| resourceLinkUrl | varchar(1000) | No | - |
| status | varchar(25) | No | - |
| resourceLinkOverview | varchar(8000) | Yes | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## dbo.partnerSolutionResourceLink

**Row Count**: 1,960

**Primary Keys**: partnerSolutionResourceLinkId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 partnerSolutionResourceLinkId | uniqueidentifier | No | - |
| partnerSolutionByAreaId | uniqueidentifier | No | - |
| resourceLinkId | uniqueidentifier | No | - |
| resourceLinkTitle | varchar(1000) | No | - |
| resourceLinkUrl | varchar(1000) | No | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |
| resourceLinkOverview | varchar(8000) | Yes | - |
| eventDateTime | datetime | Yes | - |

---

## dbo.partnerUser

**Row Count**: 550

**Primary Keys**: partnerUserId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 partnerUserId | uniqueidentifier | No | - |
| orgId | uniqueidentifier | No | - |
| lastName | nvarchar(500) | Yes | - |
| firstName | nvarchar(500) | Yes | - |
| partnerEmail | varchar(200) | Yes | - |
| partnerTitle | varchar(100) | Yes | - |
| UserType | nvarchar(50) | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## dbo.partneruser_bkup05202204

**Row Count**: 778

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| partnerUserId | uniqueidentifier | No | - |
| orgId | uniqueidentifier | No | - |
| lastName | varchar(100) | Yes | - |
| firstName | varchar(100) | Yes | - |
| partnerEmail | varchar(200) | Yes | - |
| partnerTitle | varchar(100) | Yes | - |
| UserType | nvarchar(50) | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## dbo.partneruser_bkup05312204

**Row Count**: 362

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| partnerUserId | uniqueidentifier | No | - |
| orgId | uniqueidentifier | No | - |
| lastName | varchar(100) | Yes | - |
| firstName | varchar(100) | Yes | - |
| partnerEmail | varchar(200) | Yes | - |
| partnerTitle | varchar(100) | Yes | - |
| UserType | nvarchar(50) | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## dbo.resourceLink

**Row Count**: 5

**Primary Keys**: resourceLinkId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 resourceLinkId | uniqueidentifier | No | - |
| resourceLinkName | varchar(100) | No | - |
| resourceLinkDescription | varchar(1000) | Yes | - |
| DisplayOrder | int | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | date | Yes | - |

---

## dbo.solution_Del

**Row Count**: 0

**Primary Keys**: solutionId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 solutionId | varchar(36) | No | - |
| partnerSolutionId | varchar(36) | No | - |
| industryId | varchar(36) | No | - |
| subIndustryId | varchar(36) | No | - |
| solutionAreaId | varchar(36) | No | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | date | Yes | - |

---

## dbo.solutionArea

**Row Count**: 3

**Primary Keys**: solutionAreaId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 solutionAreaId | uniqueidentifier | No | - |
| solutionAreaName | varchar(100) | No | - |
| solAreaDescription | varchar(1000) | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | date | Yes | - |
| IsDisplayOnPartnerProfile | bit | No | - |
| DisplayOrder | int | Yes | - |
| image_thumb | varchar(500) | Yes | - |
| image_mobile | varchar(500) | Yes | - |
| image_main | varchar(500) | Yes | - |
| solutionareaslug | varchar(100) | Yes | - |

---

## dbo.solutionPlay

**Row Count**: 16

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| solutionPlayId | uniqueidentifier | No | - |
| solutionAreaId | uniqueidentifier | Yes | - |
| solutionPlayThemeSlug | varchar(200) | Yes | - |
| solutionPlayName | varchar(8000) | Yes | - |
| solutionPlayDesc | varchar(-1) | Yes | - |
| solutionPlayLabel | varchar(200) | Yes | - |
| solutionStatusId | uniqueidentifier | Yes | - |
| rowChangedBy | uniqueidentifier | Yes | - |
| rowChangedDate | datetime | Yes | - |
| image_thumb | varchar(500) | Yes | - |
| image_main | varchar(500) | Yes | - |
| image_mobile | varchar(500) | Yes | - |
| IsPublished | int | Yes | - |

---

## dbo.SolutionStatus

**Row Count**: 9

**Primary Keys**: SolutionStatusId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 SolutionStatusId | uniqueidentifier | No | - |
| SolutionStatus | nvarchar(50) | Yes | - |
| DisplayLabel | nvarchar(50) | Yes | - |

---

## dbo.Spotlight

**Row Count**: 63

**Primary Keys**: SpotlightId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 SpotlightId | uniqueidentifier | No | - |
| OrganizationId | uniqueidentifier | Yes | - |
| UsecaseId | uniqueidentifier | Yes | - |
| PartnerSolutionId | uniqueidentifier | Yes | - |
| SpotlightOverview | nvarchar(-1) | Yes | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## dbo.SubIndustry

**Row Count**: 45

**Primary Keys**: SubIndustryId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 SubIndustryId | uniqueidentifier | No | - |
| IndustryId | uniqueidentifier | No | - |
| SubIndustryName | varchar(100) | No | - |
| SubIndustryDescription | varchar(8000) | Yes | - |
| Status | varchar(25) | Yes | - |
| RowChangedBy | uniqueidentifier | Yes | - |
| RowChangedDate | datetime | Yes | - |
| SubIndustrySlug | varchar(500) | Yes | - |

---

## dbo.TechnologyShowcasePartnerSolution

**Row Count**: 2

**Primary Keys**: technologyShowcasePartnerSolutionId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 technologyShowcasePartnerSolutionId | uniqueidentifier | No | - |
| solutionPlayId | uniqueidentifier | Yes | - |
| partnerId | uniqueidentifier | Yes | - |
| marketplaceLink | varchar(1000) | Yes | - |
| status | varchar(100) | Yes | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |
| PartnerName | varchar(250) | Yes | - |
| websiteLink | varchar(1000) | Yes | - |
| overviewDescription | varchar(-1) | Yes | - |
| logoFileLink | varchar(1000) | Yes | - |
| PartnerNameSlug | varchar(100) | Yes | - |

---

## dbo.usecaseOrganization

**Row Count**: 755

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| usecaseId | uniqueidentifier | No | - |
| organizationId | uniqueidentifier | No | - |

---

## dbo.user

**Row Count**: 0

**Primary Keys**: userId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 userId | varchar(36) | No | - |
| partnerUserId | varchar(36) | No | - |
| userName | varchar(100) | No | - |
| userRole | varchar(100) | No | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | date | Yes | - |

---

## dbo.UserInvite

**Row Count**: 7

**Primary Keys**: UserInviteId

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| 🔑 UserInviteId | uniqueidentifier | No | - |
| UserInviteEmail | varchar(500) | Yes | - |
| FirstName | nvarchar(500) | Yes | - |
| LastName | nvarchar(500) | Yes | - |
| Status | varchar(50) | Yes | - |
| RowChangedDate | datetime | Yes | - |
| RowChangedBy | varchar(50) | Yes | - |

---

## dbo.userOtp

**Row Count**: 232

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| userOtpId | uniqueidentifier | Yes | - |
| userEmail | varchar(100) | Yes | - |
| otpNumber | varchar(5) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## stage.indusrytheme

**Row Count**: 19

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| industryThemeId | uniqueidentifier | No | - |
| industryId | uniqueidentifier | Yes | - |
| subIndustryId | uniqueidentifier | Yes | - |
| partnerId | uniqueidentifier | Yes | - |
| Theme | varchar(8000) | Yes | - |
| industryThemeDesc | varchar(8000) | Yes | - |
| imageFileLink | varchar(500) | Yes | - |
| status | varchar(100) | Yes | - |
| isPublished | nvarchar(1) | Yes | - |
| rowChangedBy | uniqueidentifier | Yes | - |
| rowChangedDate | datetime | Yes | - |
| image_thumb | varchar(1000) | Yes | - |
| image_main | varchar(1000) | Yes | - |
| image_mobile | varchar(1000) | Yes | - |
| solutionStatusId | uniqueidentifier | Yes | - |

---

## stage.industry

**Row Count**: 7

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| IndustryId | uniqueidentifier | No | - |
| IndustryName | varchar(100) | No | - |
| IndustryDescription | varchar(1000) | Yes | - |
| Status | varchar(25) | No | - |
| RowChangedBy | varchar(100) | Yes | - |
| RowChangedDate | datetime | Yes | - |

---

## stage.IndustryShowcasePartnerSolution

**Row Count**: 15

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| IndustryShowcasePartnerSolutionId | uniqueidentifier | No | - |
| industryThemeId | uniqueidentifier | Yes | - |
| partnerId | uniqueidentifier | Yes | - |
| marketplaceLink | varchar(1000) | Yes | - |
| status | varchar(100) | Yes | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |
| PartnerName | varchar(250) | No | - |
| websiteLink | varchar(150) | Yes | - |
| overviewDescription | varchar(-1) | Yes | - |
| logoFileLink | varchar(1000) | Yes | - |

---

## stage.organization

**Row Count**: 154

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| orgId | uniqueidentifier | No | - |
| orgName | varchar(500) | No | - |
| orgDescription | varchar(1000) | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |
| logoFileLink | varchar(1000) | Yes | - |
| orgWebsite | varchar(500) | Yes | - |

---

## stage.partnerSolution

**Row Count**: 246

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| partnerSolutionId | uniqueidentifier | No | - |
| UserId | uniqueidentifier | No | - |
| IndustryId | uniqueidentifier | Yes | - |
| SubIndustryId | uniqueidentifier | Yes | - |
| OrganizationId | uniqueidentifier | Yes | - |
| solutionName | varchar(8000) | Yes | - |
| solutionDescription | varchar(-1) | Yes | - |
| solutionOrgWebsite | nvarchar(500) | Yes | - |
| marketplaceLink | varchar(1000) | Yes | - |
| specialOfferLink | varchar(1000) | Yes | - |
| logoFileLink | varchar(-1) | Yes | - |
| SolutionStatusId | uniqueidentifier | No | - |
| IsPublished | int | Yes | - |
| rowChangedBy | uniqueidentifier | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## stage.PartnerSolutionAvailableGeo

**Row Count**: 557

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| PartnerSolutionAvailableGeoId | uniqueidentifier | No | - |
| PartnerSolutionId | uniqueidentifier | No | - |
| GeoId | uniqueidentifier | No | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | date | Yes | - |

---

## stage.partnerSolutionByArea

**Row Count**: 436

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| partnerSolutionByAreaId | uniqueidentifier | No | - |
| partnerSolutionId | uniqueidentifier | No | - |
| solutionAreaId | uniqueidentifier | No | - |
| areaSolutionDescription | varchar(-1) | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## stage.partnerSolutionResourceLink

**Row Count**: 433

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| partnerSolutionResourceLinkId | uniqueidentifier | No | - |
| partnerSolutionByAreaId | uniqueidentifier | No | - |
| resourceLinkId | uniqueidentifier | No | - |
| resourceLinkTitle | varchar(1000) | No | - |
| resourceLinkUrl | varchar(1000) | No | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |
| resourceLinkOverview | varchar(8000) | Yes | - |

---

## stage.partneruser

**Row Count**: 354

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| partnerUserId | uniqueidentifier | No | - |
| orgId | uniqueidentifier | No | - |
| lastName | varchar(100) | Yes | - |
| firstName | varchar(100) | Yes | - |
| partnerEmail | varchar(200) | Yes | - |
| partnerTitle | varchar(100) | Yes | - |
| UserType | nvarchar(50) | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | datetime | Yes | - |

---

## stage.solutionarea

**Row Count**: 7

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| solutionAreaId | uniqueidentifier | No | - |
| solutionAreaName | varchar(100) | No | - |
| solAreaDescription | varchar(1000) | Yes | - |
| status | varchar(25) | No | - |
| rowChangedBy | varchar(100) | Yes | - |
| rowChangedDate | date | Yes | - |
| IsDisplayOnPartnerProfile | bit | No | - |
| DisplayOrder | int | Yes | - |
| solutionareaslug | varchar(100) | Yes | - |

---

## stage.solutionstatus

**Row Count**: 8

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| SolutionStatusId | uniqueidentifier | No | - |
| SolutionStatus | nvarchar(50) | Yes | - |
| DisplayLabel | nvarchar(50) | Yes | - |

---

## stage.subindustry

**Row Count**: 24

### Columns

| Column | Type | Nullable | Default |
|--------|------|----------|----------|
| SubIndustryId | uniqueidentifier | No | - |
| IndustryId | uniqueidentifier | No | - |
| SubIndustryName | varchar(100) | No | - |
| SubIndustryDescription | varchar(8000) | Yes | - |
| Status | varchar(25) | Yes | - |
| RowChangedBy | uniqueidentifier | Yes | - |
| RowChangedDate | datetime | Yes | - |

---


# Technical Design Document

## Overview

**Purpose**: This feature delivers a comprehensive redesign of the DxeeWorld platform through two integrated improvements: (1) a modern Kaggle-style visual design system replacing the current purple sidebar layout, and (2) a restructured survey system applying MECE principles that expands from 6 to 8+1 evaluation categories.

**Users**: All platform users will interact with the improved interface. Reviewers will benefit from the structured 8-category survey with clearer categorization and better UX through multi-step wizard forms. Platform operators will gain deeper insights through aggregated category-level analytics and visualization features (radar charts, NPS calculations).

**Impact**: Transforms the current sidebar-based layout with limited color consistency into a modern horizontal header design with unified color variables and typography system. Simultaneously, replaces the existing 6-category review structure with a comprehensive MECE-based 8-category structure, improving data quality and analytical capabilities while maintaining full backward compatibility with existing OAuth and multilingual features.

### Goals

- Establish a consistent, maintainable design system with CSS variables and typography scales
- Migrate from purple gradient sidebar layout to a clean, horizontal header navigation (64px sticky header)
- Implement Kaggle-style responsive design with proper breakpoints (320px-1440px+)
- Expand review survey from 6 to 8+1 categories following MECE principle for comprehensive, non-overlapping coverage
- Implement multi-step wizard UI for review creation with progress tracking and data validation
- Create aggregation and visualization infrastructure for category-level analytics
- Maintain full backward compatibility with existing OAuth, authentication, and multilingual (EN/ZH/JA) features

### Non-Goals

- Migrating existing review data to new schema (data migration is a separate database task)
- Implementing dark mode support (structure will support it, but not implement)
- Adding new external service integrations
- Refactoring or replacing Tornado framework or MongoDB
- Changing existing authentication mechanisms (OAuth, email verification)
- Modifying existing translation service architecture

---

## Architecture

### Existing Architecture Analysis

**Current UI Architecture**:
- Sidebar-based layout with purple gradient background (#667eea to #764ba2)
- Bootstrap CSS framework for responsive styling
- Jinja2 template inheritance with base.html providing layout structure
- Vanilla JavaScript for interactive features (reviewForm.js, login-panel.js, main.js)
- Fixed 280px sidebar using position:fixed and flexbox layout
- Responsive breakpoints exist but are primarily sidebar-focused

**Current Data Model**:
- Review model with 6 ReviewCategory enums (RECOMMENDATION, FOREIGN_SUPPORT, COMPANY_CULTURE, EMPLOYEE_RELATIONS, EVALUATION_SYSTEM, PROMOTION_TREATMENT)
- MongoDB collection with flat ratings/comments structure
- EmploymentPeriod and EmploymentStatus enum support
- No category-level aggregation fields currently

**Current Service Layer**:
- reviewForm.js handles client-side form rendering
- ReviewHandler processes review submission
- ReviewService manages review business logic
- No existing aggregation or analytics services

**Integration Points to Preserve**:
- OAuth 2.0 authentication (Google, Facebook) in auth handlers
- Email verification in email_auth_handler.py
- Multilingual support (EN/ZH/JA) via translation service and i18n_form_service
- Session management and access control middleware
- Existing review edit history tracking

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                           │
├─────────────────────────────────────────────────────────────┤
│  Header (64px sticky)    │ Content Area                      │
│  - Logo (left 150px)     │ ┌─────────────────────────────┐  │
│  - Nav Menu (center)     │ │  Page-specific Content       │  │
│  - User Icon (right)     │ │  - Company Listing/Search    │  │
│                          │ │  - Company Detail            │  │
│                          │ │  - Multi-step Review Form    │  │
│                          │ │  - Review Analytics          │  │
│                          │ └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                Design System Layer (CSS Variables)           │
│  Colors: Primary (#20BEFF), Dark (#1A8FCC), Light (#E3F5FF)│
│  Typography: Inter (EN), Noto Sans JP (JA)                  │
│  Spacing: 4px base unit scale                               │
├─────────────────────────────────────────────────────────────┤
│                    Handler Layer (Tornado)                   │
├─────────────────────────────────────────────────────────────┤
│  - review_handler.py (extended for new categories)          │
│  - company_handler.py (updated for new UI)                  │
│  - New: review_analytics_handler.py (aggregations)          │
├─────────────────────────────────────────────────────────────┤
│                   Service Layer (Business Logic)             │
├─────────────────────────────────────────────────────────────┤
│  - review_submission_service.py (validates new schema)      │
│  - New: review_aggregation_service.py (category stats)      │
│  - i18n_form_service.py (multilingual support)              │
│  - translation_service.py (DeepL translation)               │
├─────────────────────────────────────────────────────────────┤
│                   Data Model Layer (MongoDB)                 │
├─────────────────────────────────────────────────────────────┤
│  - review.py (extended ReviewCategory enum and schema)      │
│  - Backward compatible with existing reviews                │
│  - New aggregation collection for cached analytics          │
└─────────────────────────────────────────────────────────────┘
```

### Technology Alignment and Key Design Decisions

**Design Decision 1: Horizontal Header vs Sidebar Redesign**
- **Context**: Current purple sidebar occupies 280px fixed width, limiting responsive capabilities and visual modernization
- **Alternatives Considered**: (a) Keep sidebar, redesign internally; (b) CSS-only transformation; (c) Full header redesign with template refactor
- **Selected Approach**: Replace sidebar with 64px sticky horizontal header while maintaining navigation structure
- **Rationale**: Horizontal headers are Kaggle's standard pattern, improve mobile UX, allow full content width on desktop, easier responsive adaptation
- **Trade-offs**: Requires template refactor, but existing navigation structure remains unchanged, no handler modifications needed

**Design Decision 2: CSS Variables vs Component-Level Styling**
- **Context**: Current styling is scattered across main.css and login-panel.css with hardcoded colors
- **Alternatives Considered**: (a) Create CSS framework library; (b) Tailwind CSS; (c) CSS-in-JS with Tornado templating
- **Selected Approach**: Define CSS custom properties (variables) at :root level with semantic naming (--color-primary, --color-text-primary, etc.)
- **Rationale**: No new dependencies required, works with existing Bootstrap, provides consistency, enables future dark mode
- **Trade-offs**: Requires CSS refactoring but no code changes, variables are standard CSS3 feature with excellent browser support

**Design Decision 3: Database Schema Extension vs Migration**
- **Context**: Existing reviews have 6 categories; new design requires 8+1 categories
- **Alternatives Considered**: (a) Full data migration; (b) Versioned schema; (c) Backward-compatible extension with optional new fields
- **Selected Approach**: Extend MongoDB document with new fields for 8 categories (comp_salary, comp_bonus, comp_benefits, comp_equity, wlb_hours, wlb_vacation, wlb_flexibility, wlb_overall, culture_atmosphere, culture_diversity, culture_ethics, culture_communication, career_growth, career_training, career_path, career_mentorship, mgmt_vision, mgmt_decision, mgmt_structure, mgmt_manager, perf_fairness, perf_feedback, perf_promotion, perf_linkage, env_office, env_relationships, env_stress, env_health, biz_future, biz_pride, biz_social_impact, biz_financial), while keeping existing 6-category fields
- **Rationale**: Preserves existing data integrity, allows gradual migration, both old and new forms can coexist
- **Trade-offs**: Temporary document bloat during transition, aggregation queries must handle both schemas

**Design Decision 4: Multi-Step Form Architecture**
- **Context**: 8-category survey with multiple questions per category creates long form (40+ questions total)
- **Alternatives Considered**: (a) Single-page form with scrolling; (b) Modal popups per category; (c) Wizard pattern with state persistence
- **Selected Approach**: Implement 9-step wizard (8 categories + 1 overall assessment) with localStorage persistence and explicit progress visualization
- **Rationale**: Reduces cognitive load, improves completion rates, allows intermediate saves, clear progress tracking matches OpenWork pattern
- **Trade-offs**: Adds JavaScript complexity, requires state management in forms, but significantly improves UX

---

## System Flows

### Review Submission Flow (Multi-Step Wizard)

```
┌─────────────────────────────────────────────────────────────┐
│ Start: User clicks "Write Review" button                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Compensation & Benefits                              │
│ ├─ Ratings: salary, bonus, benefits, equity               │
│ └─ Comment: optional, max 500 chars                        │
│    localStorage: save on change ──┐                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                 [← Back] [Next →]
                           │
                    (Steps 2-8 repeat)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 9: Overall Assessment                                   │
│ ├─ Overall Satisfaction (1-5): required                    │
│ ├─ NPS (0-10): required                                    │
│ ├─ Employment Status: enum (current/former)                │
│ ├─ Tenure: enum (duration buckets)                         │
│ ├─ Job Category: enum (engineering, design, etc.)          │
│ └─ Overall Comment: optional, max 1000 chars               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                 [← Back] [Review & Submit]
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Review Screen: Show all responses in readonly              │
│ ├─ Display all categories and answers                     │
│ ├─ Allow [← Edit] to go back or [Submit] to confirm      │
│ └─ On submit: validate all required fields                │
└──────────────────────────┬──────────────────────────────────┘
                           │
            [Submit] ──────┴───── [Cancel]
             YES              NO
              │                │
              ▼                └──→ [Cancel to dashboard]
    ┌─────────────────┐
    │ Save to MongoDB │
    │ Clear localStorage
    │ Redirect to success
    └─────────────────┘
```

### Company Detail Page Analytics Flow

```
┌──────────────────────────────────────────┐
│ User views Company Detail Page           │
└──────────────────┬───────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │ Load company info + reviews  │
    │ (existing handler behavior)  │
    └──────────────────┬───────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
  ┌────────────────┐        ┌──────────────────────┐
  │ Display:       │        │ Query aggregations:  │
  │ - Company info │        │ - Overall avg (1-5)  │
  │ - Basic stats  │        │ - NPS score (0-10)   │
  │ - Reviews list │        │ - Category avgs      │
  └────────────────┘        │ - Industry benchmarks
                            └──────────────────────┘
                                      │
                                      ▼
                            ┌──────────────────────┐
                            │ Display Analytics:   │
                            │ - ★ 4.2 (125 reviews)
                            │ - Category bars      │
                            │ - Radar chart        │
                            │ - Promoter/Passive/  │
                            │   Detractor split    │
                            └──────────────────────┘
```

---

## Requirements Traceability

| Requirement | Area | Primary Components | Design Element |
|------------|------|-------------------|-----------------|
| 1 (Design System) | CSS/Variables | main.css (refactored) | CSS custom properties definition |
| 2 (Header) | UI/Navigation | base.html, header component | 64px sticky header, navigation menu |
| 3 (Home Page) | UI/Content | home.html, hero section | Grid layout, CTA buttons |
| 4 (Statistics) | UI/Display | detail.html stats section | 4-column grid, icon display |
| 5 (Cards) | UI/Components | card components, CSS | Border, shadow, hover effects |
| 6 (Search Page) | UI/Layout | companies/list.html | 2-column layout (filter + results) |
| 7 (Detail Page) | UI/Layout | companies/detail.html | Header section, tab navigation |
| 8 (Responsive) | CSS/Media Queries | main.css breakpoints | Media queries at 320px, 768px, 1024px |
| 9 (Survey Categories) | Data Model | review.py enum | 8 ReviewCategory types |
| 10 (Wizard UI) | JavaScript/Form | reviewForm.js (extended) | Multi-step form component |
| 11 (Database) | MongoDB Schema | review.py fields | 32 new rating/comment fields |
| 12 (Analytics) | Service | review_aggregation_service.py | Category averaging, NPS calculation |
| 13 (Design System Code) | CSS Organization | main.css structure | Variable definitions, component classes |
| 14 (Compatibility) | Integration | existing handlers/services | No breaking changes to auth, i18n |

---

## Components and Interfaces

### Frontend Layer

#### Header Navigation Component

**Responsibility & Boundaries**
- Renders fixed-height (64px) horizontal navigation bar
- Manages logo display, menu items, user authentication state
- Provides responsive behavior (hamburger menu on <768px)
- Maintains sticky positioning during page scroll
- Part of base.html template inheritance structure

**Dependencies**
- **Inbound**: All page templates (through base.html inheritance)
- **Outbound**: main.js (EXTENDED - for hamburger menu interactions), login-panel.js (user dropdown)
- **External**: None (pure HTML/CSS/vanilla JavaScript)

**Integration Strategy**
- **Template Modification**: Refactor existing sidebar in base.html to horizontal header
- **JavaScript Enhancement**: Extend existing main.js with HeaderNavigation class for hamburger menu toggle and responsive behavior
  - **File Location**: `/static/js/main.js` (extended with new HeaderNavigation class)
  - **Existing Code Preservation**: Keep all existing functionality (login, flash messages, etc.)
  - **New Methods Added**: toggleHamburger(), handleMobileMenuClick(), handleWindowResize()
  - **Event Listeners**: Attach to hamburger button, window resize events
- **CSS Changes**: Update main.css to support horizontal header layout
- **Backward Compatibility**: Navigation links remain identical structure, all template variables and i18n keys preserved
- **Migration Path**: Gradual update - base.html template refactored first, then main.js extended

**Contract Definition** (Template Contract)
```
base.html extends:
- Variables: {{ current_locale }}, {{ t() }} function, {{ url_for_lang() }}
- Blocks: {% block head %}, {% block content %}
- Navigation structure: Same nav items, different layout
```

#### Design System CSS Variables

**Responsibility & Boundaries**
- Define all color, typography, and spacing values as CSS custom properties
- Provide consistent, maintainable values for all components
- Enable future theming (dark mode) through variable override

**Contract Definition** (CSS Variables)
```css
:root {
  /* Primary Colors */
  --color-primary: #20BEFF; /* メイン */
  --color-primary-dark: #1A8FCC; /* ダーク */
  --color-primary-light: #E3F5FF; /* ライト */

  /* Background Colors */
  --color-bg-main: #F5F5F5; /* メイン背景 */
  --color-bg-card: #FFFFFF; /* カード背景 */
  --color-bg-section: #FAFAFA; /* セクション背景 */

  /* Text Colors */
  --color-text-primary: #1A1A1A; /* プライマリテキスト */
  --color-text-secondary: #666666; /* セカンダリテキスト */
  --color-text-disabled: #AAAAAA; /* 無効テキスト */

  /* UI Colors */
  --color-border: #E0E0E0;
  --color-border-light: #D0D0D0;

  /* Semantic Colors */
  --color-success: #4CAF50;
  --color-warning: #FF9800;
  --color-error: #F44336;
  --color-star: #FFB400;
  --color-tag-bg: #F0F0F0;
  --color-tag-text: #333333;

  /* Typography */
  --font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-family-ja: 'Noto Sans JP', 'Hiragino Sans', sans-serif;
  --font-size-h1: 2rem; /* 32px */
  --font-size-h2: 1.5rem; /* 24px */
  --font-size-h3: 1.25rem; /* 20px */
  --font-size-h4: 1.125rem; /* 18px */
  --font-size-body: 1rem; /* 16px */
  --font-size-small: 0.875rem; /* 14px */
  --font-size-caption: 0.75rem; /* 12px */
  --font-weight-bold: 700;
  --font-weight-semibold: 600;
  --font-weight-normal: 400;
  --line-height-heading: 1.2;
  --line-height-body: 1.6;

  /* Spacing (4px base unit) */
  --spacing-unit: 4px;
  --spacing-xs: 4px; /* 1 unit */
  --spacing-sm: 8px; /* 2 units */
  --spacing-md: 16px; /* 4 units */
  --spacing-lg: 24px; /* 6 units */
  --spacing-xl: 32px; /* 8 units */
  --spacing-2xl: 48px; /* 12 units */
  --spacing-3xl: 64px; /* 16 units */

  /* Shadows & Effects */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.12);
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 16px;
}
```

**Dependencies**
- **Inbound**: All CSS files reference variables
- **Outbound**: None (leaf node)
- **External**: Google Fonts (Inter, Noto Sans JP)

#### UI/UX Component Specifications

**Hero Section (Home Page)**
- Layout: max-width 1200px, centered, padding 80px 24px
- Background: Gradient (#F8FBFF → #FFFFFF)
- Content split: Left 60%, Right 40%
- Responsive: Mobile stacks vertically
- h1: "優秀な人材とスタートアップをつなぐ"
- Subheading: "実績ベースの評価で、透明性の高いマッチングを実現"
- CTA buttons: "無料で始める" (primary), "企業を探す" (secondary, outline)
- Right side: Illustration or platform screenshot

**Statistics Section (Home Page)**
- Background: #FFFFFF
- Layout: 4-column grid (responsive to 2→1)
- Padding: 60px 24px
- Each stat item: Icon (48px) + Number (36px, weight 700) + Label (14px, color #666)
- Centered alignment
- Icons: SVG or icon font (monochrome)

**Company/Review Card Component**
- Background: #FFFFFF
- Border: 1px solid #E0E0E0
- Border-radius: 8px
- Padding: 20px
- Box-shadow (normal): 0 1px 3px rgba(0,0,0,0.08)
- Box-shadow (hover): 0 4px 12px rgba(0,0,0,0.12)
- Transition: all 0.3s ease
- Internal structure:
  - Logo + Company name + Rating star (★4.2)
  - Divider line
  - Category | Location | Company size
  - Description text (max 2 lines with ellipsis)
  - Tags row with spacing
  - Stats: Review count | NPS percentage
- Grid: 3→2→1 columns (responsive)

**Tag Component**
- Background: #F0F0F0
- Color: #333333
- Padding: 4px 12px
- Border-radius: 16px
- Font-size: 12px
- Display: Inline-block with margin between

**Search Filter Sidebar**
- Width: 250px (fixed)
- Background: #FFFFFF
- Border-right: 1px solid #E0E0E0
- Position: Sticky (scroll-fixed)
- Sections: Industry, Location, Company size with checkboxes
- Checkbox styling: Standard with visible labels

**Search Results Area**
- Padding: 24px
- Grid: 2-column layout, gap 20px
- Responsive: Stack to 1-column on tablet/mobile

**Sort Dropdown**
- Position: Top-right of results area
- Border: 1px solid #D0D0D0
- Border-radius: 4px
- Padding: 8px 12px
- Background: #FFFFFF
- Min-width: 180px
- Options: Rating (high→low, low→high), Review count, Company name (A→Z), Recently added

**Company Detail Header**
- Background: #FFFFFF
- Padding: 32px
- Border-bottom: 1px solid #E0E0E0
- Layout: Logo + Company name (28px, weight 700) + Rating star (24px) + Tagline + Category/Location/Size + External links
- External link buttons: "🌐 Website" and "📧 Careers"

**Tab Navigation**
- Padding: 16px 0
- Border-bottom: 1px solid #E0E0E0
- Tabs: [Overview] [Reviews(125)] [Stats] [Jobs]
- Normal state: color #666, border-bottom 2px solid transparent
- Active state: color #20BEFF, border-bottom 2px solid #20BEFF, font-weight 600
- Hover state: color #1A8FCC

**Header Navigation**
- Height: 64px
- Background: #FFFFFF
- Border-bottom: 1px solid #E0E0E0
- Logo: Max-width 150px, left-aligned
- Menu: Horizontal, center→right aligned
- Items: Home | Review Search | Company List | Login/User Icon
- Font: Inter, Noto Sans JP
- Hover effect: Underline animation (transition 0.2s)
- Mobile: Hamburger menu on <768px width

**Star Rating Component**
- Size: 32px
- Color (unselected): #D0D0D0
- Color (selected): #FFB400
- Hover effect: Scale 1.1
- Animation: Fill transition 0.2s
- Display numeric: "3 / 5" format
- Interactions: Click to confirm, hover to preview
- Accessibility: Keyboard navigation support
- Mobile: Touch-optimized hit area

**Progress Bar (Multi-step Wizard)**
- Display: [1 Comp.] → [2 WLB] → [3 Culture] → ... → [9 Overall]
- Style: Visual progress indicator with step numbers
- Filled vs unfilled states
- Current step highlighting

**Category Average Scores Display**
- Format: Total ★4.2 (125 reviews)
- Each category: Name + Star rating bar (1-5 stars) + Score number
- Layout: Vertical list
- Example: "待遇・報酬 ★★★★☆ 4.0"
- NPS display: "推薦度(NPS): 75"

**Radar Chart (Analytics Visualization)**
- Library: Chart.js or D3.js
- Axes: 8 categories (Compensation, WLB, Culture, Career, Management, Performance, Environment, Business)
- Dataset 1: Company scores
- Dataset 2: Industry average (comparison)
- Colors: Primary (#20BEFF) for company, gray for industry
- Responsive: Switch to bar chart on mobile
- Data structure: data: [4.0, 4.5, 3.8, 4.2, 3.9, 3.5, 4.1, 4.3]

**Responsive Breakpoints & Layouts**
- Mobile (320px-767px): 1-column, hamburger menu, larger touch targets (30px+), vertical card stacking
- Tablet (768px-1023px): 2-column grid, simplified filter sidebar, 2-column card grid
- Desktop (1024px-1439px): 3-column grid, full filter sidebar, full features
- Large (1440px+): Max-width 1200px-1400px content container, maintained proportions

---

#### Review Wizard Form Component (JavaScript)

**Implementation Strategy: NEW FILE (wizardReviewForm.js)**

This component is implemented as a **new standalone JavaScript file** (wizardReviewForm.js) rather than extending the existing reviewForm.js. This approach provides:
- Clean separation of concerns (old 6-category form vs. new 8-category wizard)
- Independent state management for the multi-step pattern
- Easier testing and debugging
- Future flexibility to deprecate old form without affecting new system

**Responsibility & Boundaries**
- Render multi-step form for 8-category survey
- Manage form state across steps (client-side in-memory + localStorage)
- Handle validation (required fields, rating bounds 1-5)
- Display progress indicator (9 steps total)
- Provide navigation (prev/next buttons with validation)

**Dependencies**
- **Inbound**: review_handler.py (form page render)
- **Outbound**: review_handler.py (form submission POST)
- **External**: localStorage API (standard browser feature)
- **File Location**: `/static/js/wizardReviewForm.js` (new file)

**Contract Definition** (JavaScript Form Interface)
```typescript
interface ReviewWizardForm {
  // State Management
  currentStep: number; // 1-9
  formData: {
    [categoryName: string]: {
      ratings: Record<string, number | null>,
      comment: string | null
    }
  };

  // Methods
  loadFromLocalStorage(): boolean;
  saveToLocalStorage(): void;
  validateStep(step: number): ValidationResult;
  getNextStep(): number | null;
  getPreviousStep(): number | null;
  submitForm(): Promise<SubmitResult>;

  // Events
  onStepChange: (step: number) => void;
  onValidationError: (errors: ValidationError[]) => void;
}

interface ValidationResult {
  valid: boolean;
  errors: Array<{
    field: string;
    message: string;
  }>;
}
```

### Backend Layer

#### Review Aggregation Service

**Responsibility & Boundaries**
- Calculate category-level average scores from review collection
- Compute NPS (Net Promoter Score) from overall_nps field
- Generate industry benchmark data (aggregate across all companies)
- Cache aggregation results for performance

**Dependencies**
- **Inbound**: review_analytics_handler.py, company_handler.py (detail page)
- **Outbound**: MongoDB review collection (read-only aggregation queries)
- **External**: None

**Contract Definition** (Service Interface)
```typescript
interface ReviewAggregationService {
  // Get aggregations for a specific company
  getCompanyAggregations(company_id: string): Promise<Result<CompanyAggregations, AggregationError>>;

  // Calculate category averages
  calculateCategoryAverages(company_id: string): Promise<Result<CategoryAverages, AggregationError>>;

  // Calculate NPS
  calculateNPS(company_id: string): Promise<Result<NPSResult, AggregationError>>;

  // Get industry benchmarks
  getIndustryBenchmarks(): Promise<Result<IndustryBenchmarks, AggregationError>>;

  // Refresh cached aggregations
  invalidateCache(company_id: string): Promise<void>;
}

interface CompanyAggregations {
  company_id: string;
  overall_rating: number; // 1-5 average
  review_count: number;
  nps_score: number; // -100 to 100
  categories: CategoryScores;
  last_updated: DateTime;
}

interface CategoryScores {
  compensation: number;
  work_life_balance: number;
  culture: number;
  career_development: number;
  management: number;
  performance_system: number;
  work_environment: number;
  business_product: number;
}
```

**Preconditions**:
- At least 1 review exists for the company
- Reviews must contain the new category fields

**Postconditions**:
- Returns consistent averages across multiple calls (cached)
- Category averages range 1-5 (null-safe: excludes null ratings)
- NPS calculation: (Promoters - Detractors) / Total * 100

#### Extended Review Handler

**Responsibility & Boundaries**
- Extends existing review_handler.py to accept new 8-category schema
- Validates all new required fields before MongoDB insert
- Renders multi-step wizard form template
- Maintains backward compatibility with 6-category reviews

**Dependencies**
- **Inbound**: Web requests to /reviews/create
- **Outbound**: review_submission_service.py (validation), MongoDB reviews collection
- **External**: None

**Integration Strategy**
- **Modification Approach**: Extend existing review_handler.py, add new validation methods
- **Backward Compatibility**: Accept both 6-category and 8-category schemas (conditional validation)
- **Migration Path**: For legacy reviews, populate new category fields with null values

#### API Endpoint Specifications

**Review & Analytics Endpoints**

| Method | Endpoint | Request | Response | Purpose |
|--------|----------|---------|----------|---------|
| GET | /companies | Query: page, filter, sort | {companies: [], total, pages} | List companies with filters |
| GET | /companies/:id | — | {company, stats, reviews_count} | Get company details |
| GET | /companies/:id/reviews | Query: page, sort | {reviews: [], count} | Get company reviews list |
| POST | /companies/:id/reviews | {ratings, comments, overall_nps, ...} | {review_id, status} | Create new review (8 categories) |
| GET | /companies/:id/stats | — | {overall_rating, nps, category_scores, industry_avg} | Get aggregated analytics |
| GET | /reviews/:id | — | {review: {...}, company, user_display} | Get review details |
| PUT | /reviews/:id | {ratings, comments, ...} | {review_id, status} | Update review (creator only) |
| DELETE | /reviews/:id | — | {status} | Delete review (creator only) |
| GET | /search | Query: keyword, industry, location, size, sort | {companies: [], total} | Search with filters |

**Response Schema for Stats (Analytics)**
```json
{
  "overall_rating": 4.2,
  "nps_score": 75,
  "review_count": 125,
  "category_scores": {
    "compensation": 4.0,
    "work_life_balance": 4.5,
    "culture": 3.8,
    "career_development": 4.2,
    "management": 3.9,
    "performance_system": 3.5,
    "work_environment": 4.1,
    "business_product": 4.3
  },
  "industry_averages": {
    "compensation": 3.8,
    "work_life_balance": 4.0,
    ...
  },
  "last_updated": "2026-02-17T08:00:00Z"
}
```

### Data Model Layer

#### Review Document Schema (MongoDB)

**Physical Data Model**

```javascript
{
  _id: ObjectId,
  company_id: ObjectId,
  user_id: ObjectId,
  created_at: DateTime,
  updated_at: DateTime,
  is_verified: Boolean,

  // Legacy fields (keep for backward compatibility)
  individual_average: Number, // 1-5, calculated from 6 original categories
  ratings: {
    recommendation: Number | null,
    foreign_support: Number | null,
    company_culture: Number | null,
    employee_relations: Number | null,
    evaluation_system: Number | null,
    promotion_treatment: Number | null
  },
  comments: {
    recommendation: String | null,
    foreign_support: String | null,
    company_culture: String | null,
    employee_relations: String | null,
    evaluation_system: String | null,
    promotion_treatment: String | null
  },

  // New 8-category fields
  comp_salary: Number, // 1-5
  comp_bonus: Number, // 1-5
  comp_benefits: Number, // 1-5
  comp_equity: String | null, // yes/no/maybe text
  comp_comment: String | null, // max 500 chars

  wlb_hours: Number, // 1-5
  wlb_vacation: Number, // 1-5
  wlb_flexibility: Number, // 1-5
  wlb_overall: Number, // 1-5
  wlb_comment: String | null, // max 500 chars

  culture_atmosphere: Number, // 1-5
  culture_diversity: Number, // 1-5
  culture_ethics: Number, // 1-5
  culture_communication: Number, // 1-5
  culture_comment: String | null, // max 500 chars

  career_growth: Number, // 1-5
  career_training: Number, // 1-5
  career_path: Number, // 1-5
  career_mentorship: Number, // 1-5
  career_comment: String | null, // max 500 chars

  mgmt_vision: Number, // 1-5
  mgmt_decision: Number, // 1-5
  mgmt_structure: Number, // 1-5
  mgmt_manager: Number, // 1-5
  mgmt_comment: String | null, // max 500 chars

  perf_fairness: Number, // 1-5
  perf_feedback: Number, // 1-5
  perf_promotion: Number, // 1-5
  perf_linkage: Number, // 1-5
  perf_comment: String | null, // max 500 chars

  env_office: Number, // 1-5
  env_relationships: Number, // 1-5
  env_stress: Number, // 1-5 (inverted scoring)
  env_health: Number, // 1-5
  env_comment: String | null, // max 500 chars

  biz_future: Number, // 1-5
  biz_pride: Number, // 1-5
  biz_social_impact: Number, // 1-5
  biz_financial: Number, // 1-5
  biz_comment: String | null, // max 500 chars

  // Overall assessment
  overall_satisfaction: Number, // 1-5, required
  overall_nps: Number, // 0-10, required
  employment_status: Enum("current", "former"), // required
  tenure: String, // "6m_under", "6m_1y", "1y_3y", "3y_5y", "5y_over"
  job_category: String, // "engineer", "designer", "pm", "marketing", "sales", "corporate", "other"
  overall_comment: String | null, // max 1000 chars

  // Index for query performance
  // db.reviews.createIndex({ company_id: 1, created_at: -1 })
}
```

**Consistency & Integrity**:
- TINYINT fields (1-5 ratings) have check constraints via Python validation
- Overall_nps has range constraint 0-10 in validation layer
- Employment_status is enum-validated
- All comment fields have max length validation
- Backward compatibility: both old and new schemas can coexist during transition

---

## Error Handling

### Error Strategy

Comprehensive error handling with user-facing messages, logging, and recovery guidance:

**User Errors (4xx Response)**:
- Invalid form submission → Display field-level validation errors with guidance on correct formats
- Missing required fields → Highlight field in red, show "This field is required" message
- Unauthorized review edit → Redirect to login or show "You don't have permission" message
- Duplicate review submission → Show "You've already reviewed this company" message

**System Errors (5xx Response)**:
- MongoDB connection failure → Log error, show generic "Service temporarily unavailable" message
- Aggregation query timeout → Return cached result or graceful degradation
- Translation service failure → Fallback to English or original language

**Business Logic Errors (422 Response)**:
- Survey validation failure (invalid ratings) → Show specific field errors: "Rating must be 1-5"
- NPS calculation error → Log technical error, display reasonable defaults
- Category average calculation with insufficient data → Show "Not enough reviews to display analytics"

### Error Categories and Responses

**Form Validation Errors** (during wizard):
```
ValidationError {
  step: 2,
  field: "wlb_hours",
  message: "Must select a rating from 1-5 stars",
  code: "INVALID_RATING"
}
```

**Database Errors** (on review save):
```
DatabaseError {
  code: "DUPLICATE_REVIEW",
  message: "You have already submitted a review for this company",
  user_message: "One review per company per user allowed"
}
```

**Aggregation Errors** (analytics calculation):
```
AggregationError {
  code: "INSUFFICIENT_DATA",
  company_id: "123abc",
  message: "Less than 1 review exists, analytics unavailable"
}
```

### Monitoring

- **Error Logging**: All exceptions logged with traceback, user_id, company_id, timestamp
- **Error Tracking**: Aggregation failures tracked per company for trending
- **User Notifications**: In-app notification for persistent errors (e.g., "Could not save review, retrying...")
- **Health Checks**: Review submission success rate, aggregation query latency monitored

---

## Testing Strategy

### Unit Tests

- **Design System Variables**: Verify all CSS variables defined, color values correct, typography scales consistent
- **Review Aggregation Logic**: Test category average calculation with various dataset sizes (0 reviews, 1, 100, null handling)
- **NPS Calculation**: Test NPS formula with known inputs (0-10 responses), verify range -100 to 100
- **Schema Validation**: Validate new review fields (1-5 range, string max length, enum values)
- **Wizard Form State Management**: Test step navigation, localStorage persistence, data integrity across steps

### Integration Tests

- **Multi-Step Form Submission**: Create review through all 9 steps, verify data persisted correctly to MongoDB
- **Analytics Generation**: Submit multiple reviews with various ratings, verify aggregations calculate correctly
- **Header Navigation**: Verify header renders correctly on different locales (EN/ZH/JA), navigation links work
- **Backward Compatibility**: Submit review with legacy 6-category schema, verify it coexists with new schema reviews
- **Internationalization**: Verify wizard form labels display in all 3 languages, translations accurate

### E2E/UI Tests

- **Review Creation Flow**: User navigates through wizard (9 steps), completes form, views confirmation, submits successfully
- **Company Analytics Page**: User views company detail, analytics section displays with calculated scores and radar chart
- **Responsive Design**: Verify layout adapts correctly at breakpoints (mobile 320px, tablet 768px, desktop 1440px)
- **Header Responsiveness**: Verify hamburger menu appears on mobile, navigation collapses correctly
- **Search & Filter**: User filters companies in search page, cards display with new design, pagination works

### Performance Tests

- **Aggregation Query Latency**: Category average calculation under 100ms for 100+ reviews
- **Form Submission**: Multi-step form submission (32 fields) under 500ms
- **Page Load**: Company detail page with analytics under 2s on 4G connection
- **CSS Rendering**: No layout shift when CSS variables update (theme switching)

---

## Security Considerations

### Data Protection

- **Review Authorship**: Only review creator can edit/delete own reviews (enforce in middleware)
- **Input Validation**: All text fields (comments) sanitized for XSS prevention, max length enforced
- **Rating Bounds**: 1-5 ratings validated server-side (never trust client validation)
- **NPS Range**: 0-10 NPS values validated server-side

### Authentication & Authorization

- **Review Creation**: Require authenticated user session (existing oauth_middleware)
- **Review Edit**: Verify user_id matches review creator before update
- **Analytics Access**: Public read (anyone can view company analytics), no auth required
- **Aggregation Caching**: Cache anonymously (no user-specific data), safe for public display

### Error Handling for Security

- **Failed Validation**: Generic error message ("Invalid submission") without revealing schema details
- **Database Errors**: Never expose MongoDB error messages to client, log internally
- **Aggregation Failures**: Return partial data rather than leaking error details

---

## Performance & Scalability

### Performance Targets

- **Form Submission**: Complete multi-step review submission in <500ms
- **Analytics Load**: Category aggregations load in <100ms (with caching)
- **Page Rendering**: Company detail page renders with analytics in <2s (3G connection)
- **Wizard Navigation**: Step transitions respond in <50ms

### Scaling Approaches

**Horizontal Scaling**:
- Stateless form handler (localStorage on client, no server-side session per form)
- MongoDB read replicas for aggregation queries

**Cache Strategy: Strategy B - Async Background Calculation (Adopted Approach)**

**Strategic Decision**: The platform adopts **Strategy B: Async Background Calculation** as the production caching approach for review aggregations. This strategy prioritizes user experience by preventing form submission latency while ensuring accurate aggregations through background processing.

**Implementation Approach**:
```python
# review_handler.py - Async Aggregation Pattern

async def post_review(self, company_id):
    """
    Strategy B: Async Background Calculation
    1. Save review immediately (user gets response instantly)
    2. Trigger background aggregation calculation (non-blocking)
    3. Return success to user without waiting for calculation
    """
    try:
        # 1. Validate and save review data
        review_data = self.request.json
        validation_result = await self.review_submission_service.validate_review(
            company_id, review_data
        )

        if not validation_result.success:
            self.write_json({
                'status': 'error',
                'message': 'Validation failed',
                'errors': validation_result.errors
            }, status_code=422)
            return

        # Save review to MongoDB
        review = await self.review_service.create_review(
            company_id=company_id,
            user_id=self.current_user.id,
            review_data=review_data
        )

        # 2. Immediately respond to user (< 100ms)
        self.write_json({
            'status': 'success',
            'review_id': str(review.id),
            'message': 'レビューを投稿しました'  # "Review posted"
        }, status_code=201)

        # 3. Schedule background aggregation (non-blocking)
        tornado.ioloop.IOLoop.current().spawn_callback(
            self.invalidateAndRecalculateAggregations(company_id)
        )

    except Exception as e:
        self.log_exception(e)
        self.write_json({
            'status': 'error',
            'message': 'Failed to save review'
        }, status_code=500)

async def invalidateAndRecalculateAggregations(self, company_id):
    """
    Background task: Calculate aggregations after user response sent.
    Execution is non-blocking - user doesn't wait.
    """
    try:
        # Clear stale cache
        await self.review_aggregation_service.invalidateCache(company_id)

        # Recalculate aggregations
        aggregations = await self.review_aggregation_service.calculateCompanyAggregations(
            company_id
        )

        # Store in MongoDB aggregation collection
        await self.review_aggregation_service.storeAggregations(
            company_id,
            aggregations
        )

        logger.info(f"Aggregations recalculated for company {company_id}: {aggregations}")

    except Exception as e:
        logger.exception(f"Aggregation calculation failed for {company_id}: {e}")
        # Graceful degradation: next page view will trigger lazy calculation
```

**Performance Characteristics**:
- **User Response Time**: <500ms (review saved immediately)
- **Aggregation Calculation**: Runs asynchronously, does not block user
- **Database Write**: MongoDB write completes before response sent
- **Background Task**: Typically completes in 50-200ms depending on review count
- **Next Page View**: User sees updated aggregations immediately (from cache)

**Benefits of Strategy B**:
1. ✅ **Optimal User Experience**: User gets instant feedback without waiting for calculations
2. ✅ **Accurate Data**: Aggregations calculated on every new review (no stale cache)
3. ✅ **Scalable**: Tornado's spawn_callback is lightweight, handles concurrent requests
4. ✅ **Simple Implementation**: No external cache infrastructure required initially
5. ✅ **No Data Loss**: If calculation fails, lazy calculation triggered on next view

**Cache Storage & Invalidation**:
- **Aggregation Collection**: Stores pre-calculated results (company_id as key)
- **Invalidation**: Automatic on every new review submission via background task
- **Fallback**: If background task fails, lazy calculation occurs on detail page load
- **TTL**: Optional - 24h TTL for stale cleanup (non-critical)

**Implementation in Review Aggregation Service**:
```python
# review_aggregation_service.py

class ReviewAggregationService:
    def __init__(self, db):
        self.db = db
        self.aggregations_collection = db.aggregations

    async def invalidateCache(self, company_id):
        """Remove stale aggregation document"""
        await self.aggregations_collection.delete_one({
            'company_id': ObjectId(company_id)
        })

    async def calculateCompanyAggregations(self, company_id):
        """
        Strategy B: Calculate aggregations asynchronously.
        No user-facing timeout constraints.
        """
        reviews = await self.db.reviews.find({
            'company_id': ObjectId(company_id)
        }).to_list(None)

        if not reviews:
            return None

        # Category averages (1-5 scale)
        categories = {
            'compensation': self._calc_average(reviews, ['comp_salary', 'comp_bonus', 'comp_benefits']),
            'work_life_balance': self._calc_average(reviews, ['wlb_hours', 'wlb_vacation', 'wlb_flexibility', 'wlb_overall']),
            'culture': self._calc_average(reviews, ['culture_atmosphere', 'culture_diversity', 'culture_ethics', 'culture_communication']),
            'career_development': self._calc_average(reviews, ['career_growth', 'career_training', 'career_path', 'career_mentorship']),
            'management': self._calc_average(reviews, ['mgmt_vision', 'mgmt_decision', 'mgmt_structure', 'mgmt_manager']),
            'performance_system': self._calc_average(reviews, ['perf_fairness', 'perf_feedback', 'perf_promotion', 'perf_linkage']),
            'work_environment': self._calc_average(reviews, ['env_office', 'env_relationships', 'env_stress', 'env_health']),
            'business_product': self._calc_average(reviews, ['biz_future', 'biz_pride', 'biz_social_impact', 'biz_financial']),
        }

        # Overall rating
        overall_ratings = [r.get('overall_satisfaction') for r in reviews if r.get('overall_satisfaction')]
        overall_rating = sum(overall_ratings) / len(overall_ratings) if overall_ratings else None

        # NPS Calculation
        nps_scores = [r.get('overall_nps') for r in reviews if r.get('overall_nps') is not None]
        nps_score = self._calculate_nps(nps_scores) if nps_scores else None

        return {
            'company_id': ObjectId(company_id),
            'overall_rating': overall_rating,
            'nps_score': nps_score,
            'review_count': len(reviews),
            'categories': categories,
            'last_updated': datetime.utcnow(),
            'calculation_time_ms': 0  # Will be populated by caller
        }

    async def storeAggregations(self, company_id, aggregations):
        """Store calculated aggregations in MongoDB (Strategy B pattern)"""
        if aggregations is None:
            return

        await self.aggregations_collection.update_one(
            {'company_id': ObjectId(company_id)},
            {'$set': aggregations},
            upsert=True
        )

    def _calc_average(self, reviews, field_names):
        """Calculate average across multiple fields (null-safe)"""
        values = []
        for review in reviews:
            for field in field_names:
                value = review.get(field)
                if value is not None and isinstance(value, (int, float)) and 1 <= value <= 5:
                    values.append(value)

        if not values:
            return None

        return round(sum(values) / len(values), 2)

    def _calculate_nps(self, nps_scores):
        """
        NPS Calculation: (Promoters % - Detractors %) * 100
        Promoters: 9-10
        Passives: 7-8
        Detractors: 0-6
        """
        if not nps_scores:
            return None

        promoters = len([s for s in nps_scores if s >= 9])
        detractors = len([s for s in nps_scores if s <= 6])
        total = len(nps_scores)

        nps = ((promoters - detractors) / total) * 100
        return round(nps, 1)
```

**Cache Storage in MongoDB Aggregations Collection**:
```json
{
  "_id": ObjectId("..."),
  "company_id": ObjectId("..."),
  "overall_rating": 4.2,
  "nps_score": 72.5,
  "review_count": 125,
  "categories": {
    "compensation": 4.0,
    "work_life_balance": 4.5,
    "culture": 3.8,
    "career_development": 4.2,
    "management": 3.9,
    "performance_system": 3.5,
    "work_environment": 4.1,
    "business_product": 4.3
  },
  "last_updated": "2026-02-17T10:30:00Z"
}
```

**Caching Implementation Details**:
- **Application Cache**: Store category averages in MongoDB aggregation collection, update via Strategy B background task
- **Client Cache**: localStorage for in-progress wizard form (prevents data loss on refresh)
- **CDN Cache**: Static CSS variables, typography, assets cached (existing CDN setup)

**Database Optimization**:
- **Indexes**: Create compound index on (company_id, created_at DESC) for review queries
- **Aggregation Pipeline**: Use MongoDB aggregation framework for category calculations (server-side computation)
- **Materialized View**: Store pre-calculated aggregations in separate collection, update on each new review

---

## Migration Strategy

### Detailed 5-Phase Implementation Plan

```
Phase 1: Design System Construction (1-2 weeks)
├─ Task: Define color palette (CSS variables)
├─ Task: Set up typography system (Google Fonts: Inter, Noto Sans JP)
├─ Task: Create spacing system (4px base unit)
├─ Task: Build component library foundations
│   ├─ Button component (primary, secondary, outline)
│   ├─ Card component with shadows and borders
│   ├─ Input/TextArea with validation styling
│   ├─ Dropdown/Select menu
│   ├─ Rating Star component (32px, colors, hover)
│   ├─ Progress Bar (step indicator)
│   ├─ Tab Navigation component
│   ├─ Modal/Dialog framework
│   └─ Tooltip component
├─ Task: Update base.html with new header structure (64px sticky)
├─ Task: Create responsive media query breakpoints (320px, 768px, 1024px, 1440px)
└─ Checkpoint: Design system mockups created, all variables defined

Phase 2: Page UI Redesign (2-3 weeks)
├─ Task: Implement horizontal header navigation
│   ├─ Logo positioning (left, 150px max-width)
│   ├─ Menu items (Home, Review Search, Company List, Login/User)
│   ├─ Hover underline animations
│   └─ Hamburger menu for mobile
├─ Task: Redesign home page
│   ├─ Hero section (gradient bg, left 60% / right 40%)
│   ├─ CTA buttons ("無料で始める" + "企業を探す")
│   ├─ Statistics section (4-column grid, icon + number + label)
│   └─ Responsive layouts (mobile: vertical stack)
├─ Task: Update company listing/search page
│   ├─ Search bar with icon
│   ├─ Sidebar filter (250px sticky, checkbox groups)
│   ├─ Company card grid (2-column layout)
│   ├─ Sort dropdown (rating, review count, name, recently added)
│   └─ Pagination controls
├─ Task: Redesign company detail page
│   ├─ Company header (logo, name 28px, rating stars 24px, tagline, category/location/size)
│   ├─ External link buttons (🌐 Website, 📧 Careers)
│   ├─ Tab navigation ([Overview] [Reviews(N)] [Stats] [Jobs])
│   ├─ Analytics section (category scores with stars + radar chart)
│   └─ Review list section
└─ Checkpoint: All pages redesigned, responsive testing passed, cross-browser verified

Phase 3: Survey Structure & Form Implementation (2-3 weeks)
├─ Task: Extend database schema (review.py)
│   ├─ Add 8-category enums (compensation, wlb, culture, career, management, performance, environment, business)
│   ├─ Add 32 rating fields (1-5 scale, nullable for backward compatibility)
│   ├─ Add 8 comment fields (max 500 chars each)
│   ├─ Add overall_nps field (0-10 range)
│   ├─ Add tenure and job_category enums
│   └─ Create MongoDB indexes (company_id, created_at DESC)
├─ Task: Implement multi-step wizard form (JavaScript)
│   ├─ Step 1-8: Each category with 4 rating questions + 1 comment field
│   ├─ Step 9: Overall assessment (satisfaction 1-5, NPS 0-10, status enum, tenure enum, job category)
│   ├─ Progress bar (visual step indicator)
│   ├─ Navigation (← Back, Next →, Review & Submit buttons)
│   ├─ localStorage persistence (auto-save on change)
│   └─ Review screen (readonly display of all answers before submit)
├─ Task: Create star rating component
│   ├─ Styling: 32px size, #D0D0D0 unselected, #FFB400 selected
│   ├─ Hover effect: scale 1.1, transition 0.2s
│   ├─ Display format: "3 / 5" numeric indication
│   ├─ Interactions: click to confirm, hover to preview
│   ├─ Accessibility: keyboard navigation (arrow keys)
│   └─ Mobile: touch-optimized hit area (30px+)
├─ Task: Update review_handler.py
│   ├─ New validation logic for 8 categories
│   ├─ Backward compatibility: handle both old (6) and new (8) schemas
│   ├─ Multi-step form state validation
│   └─ Data transformation before MongoDB insert
├─ Task: Create review_aggregation_service.py with Strategy B (Async Background Calculation)
│   ├─ Calculate category averages (1-5 scale)
│   ├─ Calculate NPS score (Promoters % - Detractors %)
│   ├─ Generate industry benchmarks (aggregate all companies)
│   ├─ Cache aggregation results in MongoDB aggregations collection
│   ├─ Implement async cache invalidation via tornado.ioloop.IOLoop.spawn_callback()
│   ├─ Trigger background recalculation on every new review submission
│   └─ Ensure aggregations are available for detail page analytics views
├─ Task: Update review_handler.py with Strategy B pattern
│   ├─ Save review to MongoDB immediately
│   ├─ Return success response to user (<500ms)
│   ├─ Spawn background task: invalidateAndRecalculateAggregations(company_id)
│   ├─ Non-blocking: User doesn't wait for aggregation calculation
│   └─ Graceful degradation: If background task fails, lazy calculation on detail page load
└─ Checkpoint: Form submission tested, aggregations calculated correctly via async background task, user response latency <500ms

Phase 4: Testing, Optimization & Polish (1-2 weeks)
├─ Task: Unit Testing
│   ├─ CSS variables consistency checks
│   ├─ Schema validation (rating bounds, string lengths, enums)
│   ├─ Aggregation logic (category average calculations, NPS formula)
│   ├─ Wizard form state management (navigation, localStorage)
│   └─ Star rating component interactions
├─ Task: Integration Testing
│   ├─ Multi-step form submission end-to-end
│   ├─ Analytics page loading and display
│   ├─ Backward compatibility (old + new reviews together)
│   ├─ Search and filter functionality
│   └─ Header navigation across all pages
├─ Task: E2E/UI Testing
│   ├─ Review creation flow (all 9 steps → submission → success)
│   ├─ Company analytics page (load → display → radar chart render)
│   ├─ Responsive design (mobile 320px, tablet 768px, desktop 1024px, large 1440px)
│   ├─ Header responsiveness (hamburger on <768px)
│   └─ Search and filter functionality
├─ Task: Performance Optimization
│   ├─ Aggregation queries < 100ms
│   ├─ Form submission < 500ms
│   ├─ Page load < 2s (3G connection)
│   ├─ CSS rendering (no layout shift)
│   ├─ Image optimization (WebP, lazy loading)
│   └─ Database indexing
├─ Task: Internationalization Testing
│   ├─ All pages render in EN/ZH/JA
│   ├─ Wizard form labels translated correctly
│   ├─ Category names localized
│   └─ Date/number formatting per locale
└─ Checkpoint: All tests passing, performance targets met, i18n verified

Phase 5: Deployment & Monitoring (1 week)
├─ Task: Staging Deployment
│   ├─ Deploy to staging environment
│   ├─ Run smoke tests
│   ├─ Verify all features working
│   ├─ Performance monitoring setup
│   └─ Load testing (concurrent users)
├─ Task: Production Rollout
│   ├─ Deploy to production during low-traffic window
│   ├─ Monitor error rates (target: <0.1% submission failures)
│   ├─ Monitor aggregation query latency (target: <100ms)
│   ├─ Track form completion rate (baseline: 80%+ improvement target)
│   └─ Database replica lag monitoring
├─ Task: Rollback Plan Preparation
│   ├─ Rollback trigger: Aggregation queries > 500ms
│   ├─ Rollback trigger: Form submission failure rate > 2%
│   ├─ Rollback trigger: CSS rendering issues on >5% of traffic
│   ├─ Rollback trigger: Data inconsistency detected
│   ├─ Rollback procedure: Revert template/CSS, keep new schema
│   └─ Communication: Status page updates
└─ Checkpoint: Production stable, metrics within targets, monitoring active

Total Duration: 7-11 weeks
```

### Key Validation Checkpoints

- **Week 2 end**: Design system complete, all components defined
- **Week 4 end**: UI redesign complete, responsive verified
- **Week 6 end**: Survey system working end-to-end
- **Week 8 end**: All tests passing, performance optimized
- **Week 9 end**: Staging verified, production ready

---

## Component Library Specifications

### Core Components to Build

**Button Component**
- Variants: Primary (bg: #20BEFF), Secondary (bg: transparent, border: #20BEFF), Outline
- Sizes: Small (12px text, 8px padding), Medium (14px text, 12px padding), Large (16px text, 16px padding)
- States: Normal, Hover (shadow increase), Active (color darken), Disabled (opacity 50%)
- Text: Center-aligned, weight 600
- Border-radius: 4px for small/medium, smooth for large
- Transitions: All 0.2s ease

**Card Component**
- Background: #FFFFFF
- Border: 1px solid #E0E0E0
- Border-radius: 8px
- Padding: 20px
- Box-shadow (normal): 0 1px 3px rgba(0,0,0,0.08)
- Box-shadow (hover): 0 4px 12px rgba(0,0,0,0.12)
- Transition: all 0.3s ease
- Variants: Flat (no shadow), Elevated (default shadow), Interactive (has hover state)

**Input/TextArea Component**
- Border: 1px solid #E0E0E0
- Border-radius: 4px
- Padding: 12px 16px
- Focus: Border color → #20BEFF, outline none
- Placeholder: color #AAAAAA
- Validation states: Valid (border-color #4CAF50), Error (border-color #F44336)
- TextArea: Min-height 100px, resizable, scrollable
- Label: Above input, font-size 14px, weight 600, color #1A1A1A

**Dropdown/Select Component**
- Border: 1px solid #D0D0D0
- Border-radius: 4px
- Padding: 8px 12px
- Background: #FFFFFF
- Min-width: 180px
- Arrow icon: Positioned right
- Hover: Border color darker
- Open state: Show option list, max-height 300px (scrollable)
- Option styling: Padding 12px 16px, hover highlight with #E3F5FF background

**Rating Star Component**
- Size: 32px (can scale with CSS)
- Icon style: Outline style (not filled initially)
- Color (unselected): #D0D0D0
- Color (selected): #FFB400
- Hover: Scale 1.1, transition 0.2s, show color preview
- Display: Show numeric value "3 / 5" below or beside
- Count: 5 stars per question
- Spacing: 4px between stars
- Click behavior: Set rating to clicked star
- Keyboard: Arrow keys to navigate, Enter to confirm
- Mobile: Larger hit area (40px+), touch-friendly

**Progress Bar (Step Indicator)**
- Style: Linear bar with step numbers
- Steps: 9 total (1-9)
- Filled portion: Solid #20BEFF
- Unfilled portion: #E0E0E0
- Step circles: 24px diameter
- Current step: Filled #20BEFF with number
- Completed steps: Filled #20BEFF
- Future steps: Outline only
- Labels: Step category name below (e.g., "待遇・報酬")
- Responsive: Stack horizontally on desktop, wrap on mobile

**Tab Navigation Component**
- Background: Transparent
- Border-bottom: 1px solid #E0E0E0
- Tab padding: 16px 24px
- Text: Font-size 14px, weight 600
- Normal state: color #666, border-bottom 2px solid transparent
- Active state: color #20BEFF, border-bottom 2px solid #20BEFF
- Hover state: color #1A8FCC, not underlined until clicked
- Transition: color 0.2s ease
- Content: Below tab line, fade in on activation

**Modal/Dialog Component**
- Overlay: Transparent black (opacity 50%), click to close
- Modal: Max-width 500px, border-radius 8px, background #FFFFFF
- Header: Padding 24px 32px, border-bottom 1px solid #E0E0E0, title font-size 24px weight 600
- Body: Padding 32px, scrollable if content tall
- Footer: Padding 24px 32px, border-top 1px solid #E0E0E0, buttons right-aligned
- Close button: Top-right corner, X icon, clickable
- Animation: Fade in/out 0.2s

**Tooltip Component**
- Background: #1A1A1A (near black)
- Text: #FFFFFF, font-size 12px
- Padding: 8px 12px
- Border-radius: 4px
- Arrow: Pointing to target element
- Position: Auto-adjust to stay in viewport
- Show: Hover after 200ms delay
- Hide: On mouse leave or click elsewhere
- Z-index: Above all content

**Tag Component**
- Background: #F0F0F0
- Text color: #333333
- Padding: 4px 12px (vertical 4px, horizontal 12px)
- Border-radius: 16px
- Font-size: 12px
- Font-weight: 400
- Display: Inline-block
- Margin: 4px to adjacent tags
- Optional X (close): Right side, clickable for removable tags
- Clickable variant: Cursor pointer, hover bg #E0E0E0

---

## Implementation Priorities & Success Metrics

### Implementation Priorities

**🔴 High Priority** (Core functionality - complete in Phase 1-2):
1. Header navigation redesign (horizontal 64px sticky header)
2. Design system (CSS variables for colors, typography, spacing)
3. Company card redesign (new styling with borders, shadows, hover effects)
4. Survey category restructuring (8 categories from 6, MECE principle)
5. Multi-step wizard form (9 steps with progress tracking)
6. Category average score calculation (aggregation logic)

**🟡 Medium Priority** (Enhanced UX - Phase 3-4):
7. Tab navigation on detail page (Overview, Reviews, Stats, Jobs)
8. Radar chart visualization for analytics
9. Responsive design refinement (all breakpoints tested)
10. Performance caching and optimization
11. Search and filter functionality
12. NPS calculation and display

**🟢 Low Priority** (Polish & future - Phase 4+):
13. Animation and microinteraction enhancements
14. Dark mode CSS variable structure (for future implementation)
15. Advanced filtering on analytics (custom date ranges, etc.)
16. Export/download aggregated reports
17. Mobile app optimization beyond responsive
18. Additional visualization types (bar charts, trend lines)

### Success Metrics & KPIs

**Design Improvement Metrics** (Target improvement: 20-30%)

*User Engagement*:
- Page dwell time on home page: Target 2 min → 2.5+ min
- Company detail page time: Target 1.5 min → 2+ min
- Bounce rate: Target 35% → 28% or lower

*Conversion & Adoption*:
- Review submission rate (reviews per company): Target +30%
- Review completion rate (started → submitted): Target 75%+
- User registration conversion: Target +25%
- Return visitor rate: Target +15%

*Quality Metrics*:
- Mobile usability score: Target 75+ → 90+
- Page load time (<3G): Target <3s → <2s
- Core Web Vitals compliance: 95%+ pages pass

**Survey Improvement Metrics** (Target improvement: 25-35%)

*Data Quality*:
- Review text length (characters): Target 150 → 200+ average
- Comment fill rate per category: Target 40% → 60%
- Category rating completion: Target 95%+ fields filled

*User Behavior*:
- Review submission completion rate: Target 75% → 85%+
- Average time to complete review: 8 min → 12 min (more thorough)
- Return reviewers (write 2nd+ review): Target +20%
- Multi-category review depth: All 8 categories filled: Target 80%+

*Analytics Accuracy*:
- Category average accuracy: Verified against manual spot checks
- NPS calculation consistency: 100% match with formula
- Aggregation update latency: <100ms queries
- Data consistency: Zero duplicates or data loss

**Business Impact Metrics** (Track post-launch)

*Revenue/Growth*:
- Premium feature adoption (if applicable)
- Partner company engagement increase
- Data export requests (B2B use cases)

*Operational*:
- Support tickets related to survey: Expect 80% decrease
- Data correction requests: Expect minimal due to clearer questions
- Feature request satisfaction: User feedback on clarity improvement

### Measurement & Monitoring

**Analytics Setup**:
- Google Analytics 4 tracking for page metrics
- Custom events for form submission stages
- Error rate monitoring for form failures
- Database query performance monitoring
- User journey funnel analysis

**Tracking Points**:
- Form step completion (each of 9 steps)
- Form abandonment reason (step where user drops off)
- Review submission success/failure
- Aggregation query latency (APM monitoring)
- Cache hit/miss rates
- Mobile vs desktop performance comparison

**Review & Iteration Cadence**:
- Week 1 (launch): Daily metric review
- Weeks 2-4: 3x/week review
- Ongoing: Weekly review with product team
- Monthly: Deep dive analysis and optimization recommendations

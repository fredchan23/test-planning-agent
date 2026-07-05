# Agentic Test Plan: https://healthspan.assurecraft.org

This comprehensive test plan has been generated dynamically by the ADK 2.0 Test-Planning Agent. It outlines the hierarchical user journeys, a deep scenario matrix, risk-based priorities, and semantic locators grounded in the web accessibility tree.

---

## 1. Hierarchical Journey Mapping

# Journeys Map: Singapore Healthspan Simulator

## 1. Goals
* **Personalized Healthspan Prediction**: Enable users to determine their biological healthspan and morbidity gap based on Singapore-specific demographic baselines and GBD 2019 hazard ratios.
* **Behavioral Intervention Guidance**: Provide actionable insights via a "highest-leverage move" recommender to encourage lifestyle improvements.
* **Transparent Calculation (Explainability)**: Provide a detailed audit ledger to trace how specific lifestyle/clinical factors add or subtract years from the healthspan.
* **Educational Outreach**: Communicate the science of morbidity gaps and risk factors through an interactive exploration experience.
* **Inclusive Accessibility**: Ensure the tool is accessible to the local population through bilingual support (English and Simplified Chinese).

---

## 2. Journeys

### Journey 1: Primary Healthspan Assessment
**Path**: Landing Page -> Simulator -> Input Profile -> View Results
* **Start**: User lands on `/` and clicks "Try Simulator ->".
* **Action**: User configures their profile (Sex, Current Age) and selects current lifestyle/clinical markers in the `ControlPanel`.
* **System Process**: Frontend triggers debounced POST to `/api/v1/calculate` -> Engine computes Tiers 1-4 -> returns JSON metrics.
* **Outcome**: User views their predicted healthspan on the `HealthspanCard` and visualizes the lifespan vs. healthspan gap on the `LifeCalendar`.

### Journey 2: "What-If" Recovery Modeling
**Path**: Simulator -> Adjust Risk Factor -> Input Change Age -> Compare Results
* **Start**: User is on `/simulator` with a baseline result.
* **Action**: User changes a factor to a high-risk state (e.g., `smoking` -> `active_smoker`).
* **Action**: User utilizes the conditional "change age" input (e.g., `smoking_change_age`) to simulate quitting at a specific age.
* **System Process**: Engine applies linear interpolation over recovery curve anchors.
* **Outcome**: User observes the `HealthspanCard` increase and identifies the regained years in the `AuditLedgerPanel`.

### Journey 3: Identification of Highest Leverage Change
**Path**: Simulator -> Input Profile -> Review Leverage Card -> Adjust Factor
* **Start**: User completes a healthspan simulation.
* **Action**: User reviews the `LeverageCard` to find the single factor with the biggest healthspan return.
* **Action**: User changes that specific factor in the `ControlPanel` to the "Optimal" state.
* **Outcome**: User sees the maximum possible healthspan gain for their profile, validating the "actionable" value proposition.

### Journey 4: Scientific Validation and Deep Dive
**Path**: Landing Page -> Explore -> Review Data -> Launch Simulator
* **Start**: User clicks "Explore the Science" from the nav or landing page.
* **Action**: User interacts with risk ranges (Tobacco, Metabolic, Physical Activity) on `/explore` to understand hazard ratios.
* **Action**: User clicks "Launch Simulator ->" to apply this knowledge to their own data.
* **Outcome**: User enters the simulator with a higher trust level in the deterministic rules.

### Journey 5: Bilingual Localization Switch
**Path**: Any Page -> Locale Toggle -> UI Translation Verification
* **Start**: User is on any page (`/`, `/simulator`, or `/explore`).
* **Action**: User clicks the "中文" or "EN" button in the `SiteNav`.
* **System Process**: `LocaleProvider` updates state -> `useT` hook triggers re-render of all text strings.
* **Outcome**: Interface converts to the target language without a page reload or routing change.

---

## 3. Checkpoints

### CP1: Demographic Baseline Configuration
* **Inputs**: `sex` (radio), `current_age` (spinbutton).
* **Validation**: Ensure base lifespan/healthspan is correctly selected (Male: 81.8/73.0 vs Female: 86.0/75.0).

### CP2: Lifestyle & Clinical Input Matrix
* **Inputs**: 
    * `smoking` (radio)
    * `physical_activity` (radio)
    * `bmi` (combobox)
    * `alcohol` (combobox)
    * `sleep` (radio)
    * `diet` (radio)
    * `social_connection` (radio)
    * `blood_pressure` (radio)
* **Validation**: All 8 factors must be captured in the payload to satisfy the Tier 2 compounding formula.

### CP3: Time-Dimension Trigger
* **Inputs**: `smoking_change_age`, `physical_activity_change_age`.
* **Logic**: These fields must only be active/visible when the corresponding state is "worst-case" (e.g., `active_smoker`).

### CP4: Calculation Engine Integration
* **Trigger**: Debounced POST request (400ms) to `/api/v1/calculate`.
* **Validation**: Verify `AbortController` cancels stale requests if inputs change rapidly.
* **Rounding**: Confirm `predicted_healthspan` is rounded to one decimal place (round-half-up).

### CP5: Result Visualization
* **Component: HealthspanCard**: Display of final healthspan and morbidity period.
* **Component: LifeCalendar**: Correct rendering of the 8x8px dot grid (spent vs. healthy vs. morbid).
* **Component: LeverageCard**: Correct identification of the multiplier $m_i$ providing the largest $\Delta$ healthspan.

### CP6: Audit Ledger Transparency
* **Component: AuditLedgerPanel**: Expandable view.
* **Validation**: Must list Tiers 1-4, showing the raw multiplier product, asymptotic floor ($\alpha=0.70$), and any Tier 3 interaction overrides.

---

## 2. Deep Scenario Matrix (Happy, Sad, and Edge Paths)

| Category | Scenario Description | Expected Behavior | Risk Priority |
| :--- | :--- | :--- | :--- |
| Positive | Standard Male profile baseline calculation with all "Optimal" markers | System applies Male baseline (81.8/73.0) and returns maximum predicted healthspan | Priority 0 |
| Positive | Standard Female profile baseline calculation with all "Optimal" markers | System applies Female baseline (86.0/75.0) and returns maximum predicted healthspan | Priority 0 |
| Positive | Mixed risk profile (e.g., smoker, low activity, normal BMI) | System computes Tiers 1-4 and returns a healthspan lower than baseline | Priority 0 |
| Positive | "What-If" recovery: Change 'active_smoker' to 'non_smoker' with specific change_age | HealthspanCard increases; AuditLedger shows regained years via recovery curve | Priority 1 |
| Positive | Highest Leverage Path: Identify factor in LeverageCard -> set to Optimal | Predicted healthspan increases to the highest possible delta for that profile | Priority 1 |
| Positive | Full journey from Explore page -> Launch Simulator | User is redirected to /simulator; baseline state is initialized correctly | Priority 2 |
| Positive | Bilingual toggle: Switch from English to Simplified Chinese | All UI strings, labels, and tooltips update to Chinese without page reload | Priority 2 |
| Negative | Input current_age as a negative number or zero | System prevents input or displays validation error; API call is blocked | Priority 1 |
| Negative | Input change_age greater than current_age (e.g., current 40, quit at 50) | System prevents input or flags as invalid; calculation does not apply recovery | Priority 1 |
| Negative | API failure (500 Internal Server Error) during calculation | UI displays a graceful error message; HealthspanCard shows a "Retry" or "Error" state | Priority 0 |
| Negative | Incomplete payload: One of the 8 lifestyle factors missing in POST request | API returns 400 Bad Request; Frontend notifies user of missing input | Priority 0 |
| Negative | Rapid input changes (stress testing debounce) | AbortController cancels previous pending requests; only the final state is rendered | Priority 1 |
| Boundary | current_age at minimum limit (e.g., 18) | System calculates healthspan correctly based on the lowest valid age anchor | Priority 1 |
| Boundary | current_age at maximum limit (e.g., 100) | System calculates healthspan without crashing; handles asymptotic floor (0.70) | Priority 1 |
| Boundary | BMI category transitions (e.g., exactly 24.9 vs 25.0) | System switches hazard ratio multiplier at the precise threshold | Priority 1 |
| Boundary | change_age equal to current_age | Recovery logic treats this as "quitting today"; no retrospective gain applied | Priority 1 |
| Boundary | predicted_healthspan rounding (e.g., 72.45 -> 72.5) | System applies round-half-up to one decimal place consistently | Priority 2 |
| Implicit | Visibility of time-dimension triggers (change_age) | Input field is hidden if factor is 'Optimal' and visible only if factor is 'Worst-case' | Priority 1 |
| Implicit | LifeCalendar grid synchronization | Dot grid (8x8) updates visually to match the numeric morbidity gap in real-time | Priority 0 |
| Implicit | Audit Ledger depth | Expandable panel correctly lists all Tier 1-4 calculations and interaction overrides | Priority 1 |
| Implicit | Locale persistence | Selected language persists across navigation between /simulator and /explore | Priority 2 |

---

## 3. Element Grounding & Fixture Prerequisites

# Healthspan Simulator Automation Specification

## 1. Pre-conditions
* **Session State**: User is authenticated or accessing the public simulator route `/simulator`.
* **Default Baselines**: System must have the baseline configuration loaded: Male (81.8/73.0) and Female (86.0/75.0).
* **Cookies/Storage**: `locale` cookie initialized to `en-US` by default.
* **Network**: API endpoint `/api/calculate-healthspan` is reachable.

## 2. Test Scenarios

### Positive Scenarios

#### Scenario: Standard Male Profile (Optimal)
* **Synthetic Data**: `sex=male`, `current_age=40`, `sleep=optimal`, `activity=optimal`, `bmi=optimal`, `smoking=non_smoker`, `alcohol=optimal`, `diet=optimal`, `stress=optimal`, `genetics=optimal`.
* **Steps**:
    1. Select `sex_male_radio`.
    2. Input `40` into `age_input`.
    3. Set all lifestyle dropdowns to `optimal`.
* **Verification**: 
    - HealthspanCard displays the maximum predicted healthspan corresponding to the Male baseline.
    - AuditLedger confirms no hazard ratio penalties applied.

#### Scenario: Standard Female Profile (Optimal)
* **Synthetic Data**: `sex=female`, `current_age=40`, `sleep=optimal`, `activity=optimal`, `bmi=optimal`, `smoking=non_smoker`, `alcohol=optimal`, `diet=optimal`, `stress=optimal`, `genetics=optimal`.
* **Steps**:
    1. Select `sex_female_radio`.
    2. Input `40` into `age_input`.
    3. Set all lifestyle dropdowns to `optimal`.
* **Verification**: 
    - HealthspanCard displays the maximum predicted healthspan corresponding to the Female baseline.

#### Scenario: Mixed Risk Profile
* **Synthetic Data**: `sex=male`, `current_age=45`, `smoking=active_smoker`, `activity=low`, `bmi=normal`.
* **Steps**:
    1. Select `sex_male_radio`.
    2. Input `45` into `age_input`.
    3. Select `active_smoker` from `smoking_dropdown`.
    4. Select `low` from `activity_dropdown`.
* **Verification**: 
    - HealthspanCard value is strictly lower than the male baseline.
    - AuditLedger lists specific reductions for Tier 1 (Smoking) and Tier 2 (Activity).

#### Scenario: What-If Recovery (Smoking)
* **Synthetic Data**: `current_age=40`, `initial_status=active_smoker`, `new_status=non_smoker`, `change_age=42`.
* **Steps**:
    1. Set `smoking_dropdown` to `active_smoker`.
    2. Note initial `healthspan_value`.
    3. Change `smoking_dropdown` to `non_smoker`.
    4. Input `42` into `smoking_change_age_input`.
* **Verification**: 
    - HealthspanCard value increases compared to the initial status.
    - AuditLedger shows a "Recovery Gain" entry linked to the age 42 transition.

#### Scenario: Highest Leverage Path
* **Steps**:
    1. Configure a high-risk profile.
    2. Locate the factor with the highest delta in `leverage_card`.
    3. Change that specific factor's dropdown to `optimal`.
* **Verification**: 
    - Predicted healthspan increases by the largest possible increment relative to other single-factor changes.

#### Scenario: Full Journey (Explore to Simulator)
* **Steps**:
    1. Navigate to `/explore`.
    2. Click the `launch_simulator_button`.
* **Verification**: 
    - Browser URL is `/simulator`.
    - Simulator initializes with default baseline states.

#### Scenario: Bilingual Toggle
* **Steps**:
    1. Click `language_toggle_button` to select "Simplified Chinese".
* **Verification**: 
    - All labels (e.g., "Current Age", "Healthspan") update to Chinese.
    - No page reload is triggered (SPA transition).

### Negative Scenarios

#### Scenario: Invalid Current Age (Negative/Zero)
* **Synthetic Data**: `current_age=-1` or `0`.
* **Steps**:
    1. Input `-1` into `age_input`.
    2. Attempt to trigger calculation.
* **Verification**: 
    - Validation error message appears near `age_input`.
    - API network request is not dispatched.

#### Scenario: Invalid Change Age (Future Date)
* **Synthetic Data**: `current_age=40`, `change_age=50`.
* **Steps**:
    1. Set `current_age` to `40`.
    2. Set a factor to `worst-case` to reveal `change_age_input`.
    3. Input `50` into `change_age_input`.
* **Verification**: 
    - System flags the input as invalid.
    - Calculation does not apply recovery gains.

#### Scenario: API 500 Failure
* **Steps**:
    1. Intercept API call to `/api/calculate-healthspan` and force a 500 Internal Server Error.
    2. Change any input field.
* **Verification**: 
    - HealthspanCard enters an "Error" state.
    - "Retry" button is visible and functional.

#### Scenario: Incomplete Payload
* **Steps**:
    1. Manually trigger a POST request to API missing one lifestyle factor (e.g., `sleep` is null).
* **Verification**: 
    - API returns 400 Bad Request.
    - UI notifies user: "Please complete all profile markers."

#### Scenario: Rapid Input Changes (Debounce)
* **Steps**:
    1. Rapidly toggle the `sex_male_radio` and `sex_female_radio` five times.
* **Verification**: 
    - Only one final API request is processed.
    - Previous pending requests are cancelled via AbortController.

### Boundary Scenarios

#### Scenario: Age Minimum Limit
* **Synthetic Data**: `current_age=18`.
* **Steps**:
    1. Input `18` into `age_input`.
* **Verification**: 
    - System calculates healthspan using the lowest valid age anchor.

#### Scenario: Age Maximum Limit
* **Synthetic Data**: `current_age=100`.
* **Steps**:
    1. Input `100` into `age_input`.
* **Verification**: 
    - System calculates healthspan without crashing.
    - Value does not drop below the asymptotic floor (0.70 multiplier).

#### Scenario: BMI Category Transition
* **Synthetic Data**: `bmi_val_1=24.9`, `bmi_val_2=25.0`.
* **Steps**:
    1. Set BMI to `24.9` -> Note hazard ratio in AuditLedger.
    2. Set BMI to `25.0` -> Note hazard ratio in AuditLedger.
* **Verification**: 
    - Hazard ratio multiplier changes exactly at the 25.0 threshold.

#### Scenario: Change Age equals Current Age
* **Synthetic Data**: `current_age=40`, `change_age=40`.
* **Steps**:
    1. Set `current_age` to `40`.
    2. Set `change_age` to `40`.
* **Verification**: 
    - Result equals "quitting today" logic; no retrospective recovery years are added.

#### Scenario: Rounding Precision
* **Steps**:
    1. Configure profile to result in a value like `72.45`.
* **Verification**: 
    - HealthspanCard displays `72.5` (Round-half-up to one decimal).

### Implicit Scenarios

#### Scenario: Dynamic Input Visibility
* **Steps**:
    1. Set `smoking_dropdown` to `optimal`.
    2. Set `smoking_dropdown` to `worst-case`.
* **Verification**: 
    - `smoking_change_age_input` is hidden when factor is `optimal`.
    - `smoking_change_age_input` is visible when factor is `worst-case`.

#### Scenario: LifeCalendar Synchronization
* **Steps**:
    1. Change a factor to significantly reduce healthspan.
* **Verification**: 
    - The 8x8 dot grid in `LifeCalendar` updates visual "morbidity" dots to match the numeric gap.

#### Scenario: Audit Ledger Depth
* **Steps**:
    1. Click `expand_ledger_button`.
* **Verification**: 
    - Panel displays a detailed list of Tier 1, 2, 3, and 4 calculations.

#### Scenario: Locale Persistence
* **Steps**:
    1. Switch language to "Simplified Chinese" in `/simulator`.
    2. Navigate to `/explore`.
    3. Navigate back to `/simulator`.
* **Verification**: 
    - Language remains "Simplified Chinese".

## 3. Semantic Target Mapping

```json
{
  "age_input": {
    "role": "textbox",
    "name": "Current Age",
    "selector": "input[name='current_age']"
  },
  "sex_male_radio": {
    "role": "radio",
    "name": "Male",
    "selector": "input[value='male']"
  },
  "sex_female_radio": {
    "role": "radio",
    "name": "Female",
    "selector": "input[value='female']"
  },
  "smoking_dropdown": {
    "role": "combobox",
    "name": "Smoking Status",
    "selector": "select[name='smoking']"
  },
  "smoking_change_age_input": {
    "role": "textbox",
    "name": "Age of Cessation",
    "selector": "input[name='smoking_change_age']"
  },
  "activity_dropdown": {
    "role": "combobox",
    "name": "Physical Activity",
    "selector": "select[name='activity']"
  },
  "bmi_dropdown": {
    "role": "combobox",
    "name": "BMI Category",
    "selector": "select[name='bmi']"
  },
  "healthspan_value": {
    "role": "status",
    "name": "Predicted Healthspan",
    "selector": ".healthspan-card__value"
  },
  "audit_ledger": {
    "role": "region",
    "name": "Calculation Audit",
    "selector": "#audit-ledger"
  },
  "leverage_card": {
    "role": "region",
    "name": "Highest Leverage Factors",
    "selector": ".leverage-card"
  },
  "launch_simulator_button": {
    "role": "button",
    "name": "Launch Simulator",
    "selector": "a[href='/simulator']"
  },
  "language_toggle_button": {
    "role": "button",
    "name": "Switch Language",
    "selector": "button.lang-switcher"
  },
  "life_calendar_grid": {
    "role": "grid",
    "name": "Healthspan Calendar",
    "selector": ".life-calendar__grid"
  },
  "expand_ledger_button": {
    "role": "button",
    "name": "View Detailed Calculation",
    "selector": "button#expand-ledger"
  }
}
```

---

## 4. Semantic Target Mapping

Below is the mapping between logical elements used in the assertions and their stable DOM selectors:

| Element Key | Role | Display Name | CSS/XPath Selector |
| :--- | :--- | :--- | :--- |
| `home` | `button` | **Home** | `a[href='/']` |
| `en` | `button` | **EN** | `button:has-text('EN')` |
| `中文` | `button` | **中文** | `button:has-text('中文')` |
| `try_simulator_→` | `button` | **Try Simulator →** | `a[href='/simulator']` |
| `try_the_simulator_→` | `button` | **Try the Simulator →** | `a[href='/simulator']` |
| `launch_simulator_→` | `button` | **Launch Simulator →** | `a[href='/simulator']` |
| `try_the_simulator_→` | `button` | **Try the Simulator →** | `a[href='/simulator']` |
| `current_age` | `spinbutton` | **Current Age** | `input#current_age` |
| `bmi` | `combobox` | **BMI** | `select#bmi` |
| `alcohol` | `combobox` | **Alcohol** | `select#alcohol` |
| `home` | `button` | **Home** | `a[href='/']` |
| `en` | `button` | **EN** | `button:has-text('EN')` |
| `中文` | `button` | **中文** | `button:has-text('中文')` |
| `▲` | `button` | **▲** | `button:has-text('▲')` |
| `▼` | `button` | **▼** | `button:has-text('▼')` |
| `sex` | `radio_group` | **Male** | `input[name='sex']` |
| `smoking` | `radio_group` | **Non-smoker** | `input[name='smoking']` |
| `physical_activity` | `radio_group` | **Sedentary** | `input[name='physical_activity']` |
| `sleep` | `radio_group` | **Normal (7–9h)** | `input[name='sleep']` |
| `diet` | `radio_group` | **Healthy** | `input[name='diet']` |
| `social_connection` | `radio_group` | **Connected** | `input[name='social_connection']` |
| `blood_pressure` | `radio_group` | **Normal (<130/80)** | `input[name='blood_pressure']` |
| `tobacco_consumption` | `range` | **Tobacco Consumption** | `input#explore-smoking` |
| `metabolic_(bmi_/_glucose)` | `range` | **Metabolic (BMI / Glucose)** | `input#explore-metabolic` |
| `physical_activity` | `range` | **Physical Activity** | `input#explore-activity` |
| `home` | `button` | **Home** | `a[href='/']` |
| `en` | `button` | **EN** | `button:has-text('EN')` |
| `中文` | `button` | **中文** | `button:has-text('中文')` |
| `try_simulator_→` | `button` | **Try Simulator →** | `a[href='/simulator']` |
| `launch_the_simulator_→` | `button` | **Launch the Simulator →** | `a[href='/simulator']` |

### Structured JSON Hand-Off
```json
{
  "home": {
    "role": "button",
    "name": "Home",
    "selector": "a[href='/']",
    "path": "/explore"
  },
  "en": {
    "role": "button",
    "name": "EN",
    "selector": "button:has-text('EN')",
    "path": "/explore"
  },
  "\u4e2d\u6587": {
    "role": "button",
    "name": "\u4e2d\u6587",
    "selector": "button:has-text('\u4e2d\u6587')",
    "path": "/explore"
  },
  "try_simulator_\u2192": {
    "role": "button",
    "name": "Try Simulator \u2192",
    "selector": "a[href='/simulator']",
    "path": "/explore"
  },
  "try_the_simulator_\u2192": {
    "role": "button",
    "name": "Try the Simulator \u2192",
    "selector": "a[href='/simulator']",
    "path": "/"
  },
  "launch_simulator_\u2192": {
    "role": "button",
    "name": "Launch Simulator \u2192",
    "selector": "a[href='/simulator']",
    "path": "/"
  },
  "current_age": {
    "role": "spinbutton",
    "name": "Current Age",
    "selector": "input#current_age",
    "path": "/simulator"
  },
  "bmi": {
    "role": "combobox",
    "name": "BMI",
    "selector": "select#bmi",
    "path": "/simulator"
  },
  "alcohol": {
    "role": "combobox",
    "name": "Alcohol",
    "selector": "select#alcohol",
    "path": "/simulator"
  },
  "\u25b2": {
    "role": "button",
    "name": "\u25b2",
    "selector": "button:has-text('\u25b2')",
    "path": "/simulator"
  },
  "\u25bc": {
    "role": "button",
    "name": "\u25bc",
    "selector": "button:has-text('\u25bc')",
    "path": "/simulator"
  },
  "sex": {
    "role": "radio_group",
    "name": "Male",
    "selector": "input[name='sex']",
    "path": "/simulator"
  },
  "smoking": {
    "role": "radio_group",
    "name": "Non-smoker",
    "selector": "input[name='smoking']",
    "path": "/simulator"
  },
  "physical_activity": {
    "role": "range",
    "name": "Physical Activity",
    "selector": "input#explore-activity",
    "path": "/explore"
  },
  "sleep": {
    "role": "radio_group",
    "name": "Normal (7\u20139h)",
    "selector": "input[name='sleep']",
    "path": "/simulator"
  },
  "diet": {
    "role": "radio_group",
    "name": "Healthy",
    "selector": "input[name='diet']",
    "path": "/simulator"
  },
  "social_connection": {
    "role": "radio_group",
    "name": "Connected",
    "selector": "input[name='social_connection']",
    "path": "/simulator"
  },
  "blood_pressure": {
    "role": "radio_group",
    "name": "Normal (<130/80)",
    "selector": "input[name='blood_pressure']",
    "path": "/simulator"
  },
  "tobacco_consumption": {
    "role": "range",
    "name": "Tobacco Consumption",
    "selector": "input#explore-smoking",
    "path": "/explore"
  },
  "metabolic_(bmi_/_glucose)": {
    "role": "range",
    "name": "Metabolic (BMI / Glucose)",
    "selector": "input#explore-metabolic",
    "path": "/explore"
  },
  "launch_the_simulator_\u2192": {
    "role": "button",
    "name": "Launch the Simulator \u2192",
    "selector": "a[href='/simulator']",
    "path": "/explore"
  },
  "age_input": {
    "role": "textbox",
    "name": "Current Age",
    "selector": "input[name='current_age']",
    "path": ""
  },
  "sex_male_radio": {
    "role": "radio",
    "name": "Male",
    "selector": "input[value='male']",
    "path": ""
  },
  "sex_female_radio": {
    "role": "radio",
    "name": "Female",
    "selector": "input[value='female']",
    "path": ""
  },
  "smoking_dropdown": {
    "role": "combobox",
    "name": "Smoking Status",
    "selector": "select[name='smoking']",
    "path": ""
  },
  "smoking_change_age_input": {
    "role": "textbox",
    "name": "Age of Cessation",
    "selector": "input[name='smoking_change_age']",
    "path": ""
  },
  "activity_dropdown": {
    "role": "combobox",
    "name": "Physical Activity",
    "selector": "select[name='activity']",
    "path": ""
  },
  "bmi_dropdown": {
    "role": "combobox",
    "name": "BMI Category",
    "selector": "select[name='bmi']",
    "path": ""
  },
  "healthspan_value": {
    "role": "status",
    "name": "Predicted Healthspan",
    "selector": ".healthspan-card__value",
    "path": ""
  },
  "audit_ledger": {
    "role": "region",
    "name": "Calculation Audit",
    "selector": "#audit-ledger",
    "path": ""
  },
  "leverage_card": {
    "role": "region",
    "name": "Highest Leverage Factors",
    "selector": ".leverage-card",
    "path": ""
  },
  "launch_simulator_button": {
    "role": "button",
    "name": "Launch Simulator",
    "selector": "a[href='/simulator']",
    "path": ""
  },
  "language_toggle_button": {
    "role": "button",
    "name": "Switch Language",
    "selector": "button.lang-switcher",
    "path": ""
  },
  "life_calendar_grid": {
    "role": "grid",
    "name": "Healthspan Calendar",
    "selector": ".life-calendar__grid",
    "path": ""
  },
  "expand_ledger_button": {
    "role": "button",
    "name": "View Detailed Calculation",
    "selector": "button#expand-ledger",
    "path": ""
  }
}
```

---

*Generated by openai/google/gemma-4-31b-it*

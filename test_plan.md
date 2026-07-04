# Agentic Test Plan: https://healthspan.assurecraft.org

This comprehensive test plan has been generated dynamically by the ADK 2.0 Test-Planning Agent. It outlines the hierarchical user journeys, a deep scenario matrix, risk-based priorities, and semantic locators grounded in the web accessibility tree.

---

## 1. Hierarchical Journey Mapping

# Healthspan SG Simulator - QA Journey Map

## Goals
1. Personal Healthspan Prediction: Enable users to determine their projected healthy years and morbidity gap based on demographic and lifestyle inputs.
2. Lifestyle Optimization Analysis: Provide actionable insights via the highest-leverage move recommender to show the impact of lifestyle changes.
3. Scientific Transparency: Ensure the deterministic nature of the calculation is explainable through the audit ledger and the Explore page.
4. Localization and Accessibility: Provide a seamless experience for English and Simplified Chinese speaking residents of Singapore.

## Journeys

### Journey 1: Basic Healthspan Assessment
**Path:** Landing Page $\rightarrow$ Simulator $\rightarrow$ Input Profile $\rightarrow$ Results
1. User lands on the Home page and clicks the Try Simulator CTA.
2. User selects biological sex (Male/Female).
3. User enters current age using the spinbutton or stepper controls.
4. User selects current states for the 8 lifestyle and clinical factors.
5. System triggers a debounced POST request to `/api/v1/calculate`.
6. User views the predicted healthspan and morbidity period on the HealthspanCard.
7. User observes the visual representation of their life on the LifeCalendar.

### Journey 2: Lifestyle "What-if" Simulation
**Path:** Simulator $\rightarrow$ Modify Factor $\rightarrow$ Compare Results $\rightarrow$ Leverage Identification
1. User establishes a baseline result.
2. User modifies a specific factor (e.g., changing Physical Activity from sedentary to active).
3. User observes the real-time update of the HealthspanCard metrics.
4. User identifies the most impactful change via the LeverageCard.
5. User expands the AuditLedgerPanel to trace the specific multiplier change for that factor.

### Journey 3: Recovery Path Modeling (Time Dimension)
**Path:** Simulator $\rightarrow$ Set Negative Factor $\rightarrow$ Set Change Age $\rightarrow$ Analyze Recovery
1. User selects a factor with a recovery curve (e.g., Active Smoker).
2. User interacts with the conditionally revealed smoking_change_age field.
3. User adjusts the age at which the habit ceases.
4. User verifies that the final healthspan reflects the linear interpolation of the recovery curve as per the PRD.

### Journey 4: Scientific Validation and Exploration
**Path:** Landing Page $\rightarrow$ Explore Page $\rightarrow$ Science Review $\rightarrow$ Simulator
1. User navigates to the Explore page.
2. User interacts with risk factor ranges (Tobacco, Metabolic, Physical Activity) to understand hazard ratios.
3. User reviews the documentation on the 0.7 asymptotic floor and GBD 2019 data.
4. User clicks Launch Simulator to apply this knowledge to their personal profile.

### Journey 5: Multilingual User Experience
**Path:** Any Page $\rightarrow$ Locale Toggle $\rightarrow$ Content Verification
1. User accesses the site in the default language (English).
2. User clicks the Simplified Chinese toggle in the SiteNav.
3. User verifies that the interface, including the 15-term reviewed clinical glossary, updates without a full page reload.
4. User switches back to English to ensure state persistence of the simulation inputs.

## Checkpoints

### CP1: User Profile Configuration
- Sex selection (Radio group: male/female).
- Current age input (Spinbutton/Stepper validation).
- Baseline stratification trigger (Male: 81.8/73.0 vs Female: 86.0/75.0).

### CP2: Lifestyle and Clinical Inputs
- Smoking state selection and conditional visibility of change age.
- Physical activity state selection and conditional visibility of change age.
- BMI combobox selection (optimal, overweight, obese).
- Alcohol, Sleep, Diet, and Social Connection radio/combobox selections.
- Blood Pressure clinical marker selection.

### CP3: Calculation Engine Integration
- Debounce mechanism (400ms) for API calls.
- Stale request cancellation via AbortController.
- Server-side rounding contract (round-half-up to one decimal place).
- Interaction override logic (most penalizing result wins).

### CP4: Output Visualization
- HealthspanCard: Correct display of predicted healthspan and morbidity gap.
- LifeCalendar: Correct rendering of the 8x8px dot grid (spent, healthy, morbid, future).
- LeverageCard: Identification of the single factor with the maximum positive delta.

### CP5: Audit and Transparency
- AuditLedgerPanel: Verification of Tier 1 through Tier 4 calculation steps.
- Reconciliation entries: Presence of audit logs when interaction overrides are triggered.
- Source attribution: Verification of GBD 2019 and Singapore DOS citations.

### CP6: Global Navigation and UI
- LocaleProvider: Correct language switching via useT hook.
- SiteNav: Functional links between Home, Simulator, and Explore pages.
- Responsive Layout: Tailwind CSS 4 alignment across device breakpoints.

---

## 2. Deep Scenario Matrix (Happy, Sad, and Edge Paths)

| Scenario Category | Scenario Description | Expected Result | Risk Priority |
| :--- | :--- | :--- | :--- |
| **Positive** | Complete baseline assessment for Male user | Correct stratification (81.8/73.0) applied; HealthspanCard and LifeCalendar render accurately. | Priority 0 |
| **Positive** | Complete baseline assessment for Female user | Correct stratification (86.0/75.0) applied; HealthspanCard and LifeCalendar render accurately. | Priority 0 |
| **Positive** | Modify a lifestyle factor to improve healthspan | HealthspanCard metrics update in real-time; LeverageCard identifies the specific factor as the top move. | Priority 1 |
| **Positive** | Set "Active Smoker" and provide a "change_age" | Calculation applies recovery curve interpolation; result reflects improved healthspan vs. lifelong smoker. | Priority 1 |
| **Positive** | Navigate Explore Page $\rightarrow$ Launch Simulator | User is redirected to Simulator; simulation environment initializes correctly. | Priority 2 |
| **Positive** | Switch language from English to Simplified Chinese | UI updates immediately via LocaleProvider; clinical glossary terms match the 15-term reviewed list. | Priority 2 |
| **Negative** | Rapid input changes (stress testing debounce) | AbortController cancels stale requests; only the final state (after 400ms) triggers the API response. | Priority 1 |
| **Negative** | API failure during `/api/v1/calculate` call | System displays a graceful error state/toast instead of crashing or showing "NaN" values. | Priority 0 |
| **Negative** | Enter non-numeric or special characters in age field | Spinbutton/Stepper restricts input to integers; system prevents submission of invalid age data. | Priority 1 |
| **Negative** | Set "change_age" lower than "current_age" | System prevents selection or triggers validation error (Recovery cannot happen in the past). | Priority 1 |
| **Boundary** | Age input at minimum limit (e.g., 0 or 1) | System handles minimum age without calculation errors or negative life expectancy. | Priority 1 |
| **Boundary** | Age input at maximum limit (e.g., 120) | System handles extreme longevity without breaking the LifeCalendar grid rendering. | Priority 2 |
| **Boundary** | Calculation resulting in value near 0.7 asymptotic floor | System enforces the 0.7 floor; healthspan does not drop below the scientific minimum regardless of risk factors. | Priority 0 |
| **Boundary** | Rounding check for half-up contract (e.g., x.x5) | API returns values rounded half-up to one decimal place (e.g., 72.45 $\rightarrow$ 72.5). | Priority 1 |
| **Boundary** | BMI transition thresholds | Verify result change exactly at the boundary between Optimal $\rightarrow$ Overweight and Overweight $\rightarrow$ Obese. | Priority 1 |
| **Implicit** | Language toggle during active simulation | Language changes but input values (Age, Sex, Factors) are persisted without resetting the simulation. | Priority 2 |
| **Implicit** | Interaction Override (Multiple penalizing factors) | AuditLedgerPanel confirms the most penalizing result wins when multiple risk factors conflict. | Priority 0 |
| **Implicit** | LifeCalendar dot grid synchronization | The number of "spent", "healthy", and "morbid" dots matches the numeric output of the HealthspanCard. | Priority 0 |
| **Implicit** | Audit Ledger traceability | Every change in the HealthspanCard corresponds to a specific Tier 1-4 entry in the AuditLedgerPanel. | Priority 1 |
| **Implicit** | Responsive layout break-point shift | UI maintains alignment and accessibility of the Simulator inputs on mobile vs. desktop views. | Priority 2 |

---

## 3. Element Grounding & Fixture Prerequisites

# Playwright Automation Specification: Healthspan Simulator

## 1. Test Suite Pre-conditions
* **Session State**: Authenticated or Guest session with cleared local storage to ensure no cached simulation results.
* **Default Baseline**: Browser viewport set to 1920x1080 (Desktop) unless responsive tests are targeted.
* **API Mocking**: Interceptors configured for `/api/v1/calculate` to simulate failure states for Negative scenarios.
* **Locale**: Default browser language set to `en-US`.

## 2. Synthetic Data Definitions

| Data Set ID | Age | Sex | Smoking Status | BMI | Change Age | Expected Stratification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BASE_MALE` | 40 | Male | Never | 22.0 | N/A | 81.8 / 73.0 |
| `BASE_FEMALE` | 40 | Female | Never | 22.0 | N/A | 86.0 / 75.0 |
| `RECOVERY_SMOKER` | 50 | Male | Active | 24.0 | 40 | Interpolated Recovery |
| `MAX_RISK` | 60 | Male | Active | 35.0 | N/A | 0.7 Asymptotic Floor |
| `BOUNDARY_AGE_MIN` | 1 | Male | Never | 20.0 | N/A | Valid Calculation |
| `BOUNDARY_AGE_MAX` | 120 | Female | Never | 20.0 | N/A | Valid Grid Render |
| `BMI_THRESHOLD_1` | 40 | Male | Never | 24.9 | N/A | Optimal |
| `BMI_THRESHOLD_2` | 40 | Male | Never | 25.0 | N/A | Overweight |

---

## 3. Grounded Scenarios

### 3.1 Positive Flow Scenarios

#### Scenario: Complete baseline assessment for Male user
* **Data**: `BASE_MALE`
* **Steps**:
    1. Navigate to Simulator URL.
    2. Select `sex_male_radio`.
    3. Input `40` into `age_input`.
    4. Verify `healthspan_card_value` contains "73.0" and `life_expectancy_card_value` contains "81.8".
    5. Verify `life_calendar_grid` is rendered and visible.
* **Verification**: The HealthspanCard displays the precise male stratification constants.

#### Scenario: Modify a lifestyle factor to improve healthspan
* **Data**: `BASE_MALE` $\rightarrow$ Change `smoking_status` to "Current" then back to "Never".
* **Steps**:
    1. Set baseline using `BASE_MALE`.
    2. Change `smoking_status_dropdown` to "Current Smoker".
    3. Observe `healthspan_card_value` decrease.
    4. Change `smoking_status_dropdown` back to "Never".
    5. Verify `leverage_card_top_move` text identifies "Smoking Cessation" or "Non-smoking" as the primary driver.
* **Verification**: Healthspan metrics update in real-time and the LeverageCard identifies the factor change.

#### Scenario: Set "Active Smoker" and provide a "change_age"
* **Data**: `RECOVERY_SMOKER`
* **Steps**:
    1. Select `sex_male_radio`.
    2. Input `50` into `age_input`.
    3. Select "Active Smoker" in `smoking_status_dropdown`.
    4. Input `40` into `change_age_input`.
    5. Capture `healthspan_card_value`.
    6. Remove `change_age_input` value.
    7. Verify the value with `change_age` is higher than the value without it.
* **Verification**: The recovery curve interpolation increases healthspan relative to a lifelong smoker.

#### Scenario: Switch language from English to Simplified Chinese
* **Steps**:
    1. Click `language_toggle_button`.
    2. Select "简体中文" from the locale menu.
    3. Verify `simulator_title` text matches the translated string.
    4. Verify clinical terms in `audit_ledger_panel` match the approved 15-term glossary.
* **Verification**: UI updates immediately via LocaleProvider without page reload.

---

### 3.2 Negative Flow Scenarios

#### Scenario: Rapid input changes (stress testing debounce)
* **Steps**:
    1. Focus `age_input`.
    2. Use `page.keyboard.type` to enter "40", "41", "42", "43" in rapid succession (<100ms intervals).
    3. Monitor Network tab for `/api/v1/calculate` calls.
* **Verification**: Only one API request is successfully completed after the final input (400ms debounce).

#### Scenario: API failure during calculation
* **Steps**:
    1. Mock `/api/v1/calculate` to return `500 Internal Server Error`.
    2. Change any input value in the simulator.
* **Verification**: A toast notification appears with an error message; no "NaN" or "undefined" strings appear in the `healthspan_card_value`.

#### Scenario: Set "change_age" lower than "current_age"
* **Steps**:
    1. Input `40` into `age_input`.
    2. Input `30` into `change_age_input`.
* **Verification**: The `change_age_input` triggers a validation state (e.g., red border) and prevents submission.

---

### 3.3 Boundary Scenarios

#### Scenario: Calculation resulting in value near 0.7 asymptotic floor
* **Data**: `MAX_RISK`
* **Steps**:
    1. Set `sex_male_radio`.
    2. Set `age_input` to `60`.
    3. Set all lifestyle factors to the most penalizing options.
    4. Verify `healthspan_card_value` is not less than `0.7`.
* **Verification**: The system enforces the scientific minimum floor regardless of cumulative risk.

#### Scenario: BMI transition thresholds
* **Data**: `BMI_THRESHOLD_1` $\rightarrow$ `BMI_THRESHOLD_2`
* **Steps**:
    1. Set `bmi_input` to `24.9`.
    2. Verify `bmi_status_label` displays "Optimal".
    3. Set `bmi_input` to `25.0`.
    4. Verify `bmi_status_label` displays "Overweight".
* **Verification**: Result changes exactly at the defined clinical boundary.

---

### 3.4 Implicit & System Scenarios

#### Scenario: LifeCalendar dot grid synchronization
* **Steps**:
    1. Set a known state (e.g., `BASE_MALE`).
    2. Extract the numeric healthspan value $H$ and life expectancy $L$ from the card.
    3. Count the number of "healthy" dots and "morbid" dots in `life_calendar_grid`.
* **Verification**: The total count of dots matches $L$ and the transition point matches $H$.

#### Scenario: Audit Ledger traceability
* **Steps**:
    1. Start with `BASE_MALE`.
    2. Change `smoking_status_dropdown` to "Active Smoker".
    3. Open `audit_ledger_panel`.
* **Verification**: A new entry appears in the ledger specifying the penalty applied due to smoking status.

---

## 4. Semantic Target Mapping

```json
{
  "sex_male_radio": {
    "role": "radio",
    "name": "Male",
    "selector": "input[name='sex'][value='male']"
  },
  "sex_female_radio": {
    "role": "radio",
    "name": "Female",
    "selector": "input[name='sex'][value='female']"
  },
  "age_input": {
    "role": "spinbutton",
    "name": "Age",
    "selector": "input[name='age']"
  },
  "change_age_input": {
    "role": "spinbutton",
    "name": "Change Age",
    "selector": "input[name='change_age']"
  },
  "smoking_status_dropdown": {
    "role": "combobox",
    "name": "Smoking Status",
    "selector": "select[name='smoking_status']"
  },
  "bmi_input": {
    "role": "spinbutton",
    "name": "BMI",
    "selector": "input[name='bmi']"
  },
  "healthspan_card_value": {
    "role": "status",
    "name": "Healthspan Result",
    "selector": ".healthspan-card .value-display"
  },
  "life_expectancy_card_value": {
    "role": "status",
    "name": "Life Expectancy Result",
    "selector": ".life-expectancy-card .value-display"
  },
  "life_calendar_grid": {
    "role": "grid",
    "name": "Life Calendar",
    "selector": ".life-calendar-container"
  },
  "leverage_card_top_move": {
    "role": "region",
    "name": "Top Health Move",
    "selector": ".leverage-card .top-move-text"
  },
  "audit_ledger_panel": {
    "role": "log",
    "name": "Audit Ledger",
    "selector": ".audit-ledger-panel"
  },
  "language_toggle_button": {
    "role": "button",
    "name": "Switch Language",
    "selector": "button[aria-label='Language Selector']"
  },
  "bmi_status_label": {
    "role": "text",
    "name": "BMI Category",
    "selector": ".bmi-category-label"
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
| `tobacco_consumption` | `range` | **Tobacco Consumption** | `input#explore-smoking` |
| `metabolic_(bmi_/_glucose)` | `range` | **Metabolic (BMI / Glucose)** | `input#explore-metabolic` |
| `physical_activity` | `range` | **Physical Activity** | `input#explore-activity` |
| `home` | `button` | **Home** | `a[href='/']` |
| `en` | `button` | **EN** | `button:has-text('EN')` |
| `中文` | `button` | **中文** | `button:has-text('中文')` |
| `try_simulator_→` | `button` | **Try Simulator →** | `a[href='/simulator']` |
| `launch_the_simulator_→` | `button` | **Launch the Simulator →** | `a[href='/simulator']` |
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

### Structured JSON Hand-Off
```json
{
  "home": {
    "role": "button",
    "name": "Home",
    "selector": "a[href='/']",
    "path": "/simulator"
  },
  "en": {
    "role": "button",
    "name": "EN",
    "selector": "button:has-text('EN')",
    "path": "/simulator"
  },
  "\u4e2d\u6587": {
    "role": "button",
    "name": "\u4e2d\u6587",
    "selector": "button:has-text('\u4e2d\u6587')",
    "path": "/simulator"
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
  "physical_activity": {
    "role": "radio_group",
    "name": "Sedentary",
    "selector": "input[name='physical_activity']",
    "path": "/simulator"
  },
  "launch_the_simulator_\u2192": {
    "role": "button",
    "name": "Launch the Simulator \u2192",
    "selector": "a[href='/simulator']",
    "path": "/explore"
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
  "sex_male_radio": {
    "role": "radio",
    "name": "Male",
    "selector": "input[name='sex'][value='male']",
    "path": ""
  },
  "sex_female_radio": {
    "role": "radio",
    "name": "Female",
    "selector": "input[name='sex'][value='female']",
    "path": ""
  },
  "age_input": {
    "role": "spinbutton",
    "name": "Age",
    "selector": "input[name='age']",
    "path": ""
  },
  "change_age_input": {
    "role": "spinbutton",
    "name": "Change Age",
    "selector": "input[name='change_age']",
    "path": ""
  },
  "smoking_status_dropdown": {
    "role": "combobox",
    "name": "Smoking Status",
    "selector": "select[name='smoking_status']",
    "path": ""
  },
  "bmi_input": {
    "role": "spinbutton",
    "name": "BMI",
    "selector": "input[name='bmi']",
    "path": ""
  },
  "healthspan_card_value": {
    "role": "status",
    "name": "Healthspan Result",
    "selector": ".healthspan-card .value-display",
    "path": ""
  },
  "life_expectancy_card_value": {
    "role": "status",
    "name": "Life Expectancy Result",
    "selector": ".life-expectancy-card .value-display",
    "path": ""
  },
  "life_calendar_grid": {
    "role": "grid",
    "name": "Life Calendar",
    "selector": ".life-calendar-container",
    "path": ""
  },
  "leverage_card_top_move": {
    "role": "region",
    "name": "Top Health Move",
    "selector": ".leverage-card .top-move-text",
    "path": ""
  },
  "audit_ledger_panel": {
    "role": "log",
    "name": "Audit Ledger",
    "selector": ".audit-ledger-panel",
    "path": ""
  },
  "language_toggle_button": {
    "role": "button",
    "name": "Switch Language",
    "selector": "button[aria-label='Language Selector']",
    "path": ""
  },
  "bmi_status_label": {
    "role": "text",
    "name": "BMI Category",
    "selector": ".bmi-category-label",
    "path": ""
  }
}
```

---

*Generated by openai/google/gemma-4-31b-it*

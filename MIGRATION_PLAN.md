# SRTGO: Terminal UI to Web UI Migration - Executive Summary

## Overview
**Project**: SRTgo - Korean Train (SRT/KTX) Reservation Automation Tool  
**Current Implementation**: Terminal UI using Python's inquirer library  
**Total Lines of Code**: 3,115 (Python)  
**Complexity Level**: High (real-time polling, multi-step forms, credential management)

---

## Key Findings

### 1. Inquirer Usage Scope
- **Total Inquirer Components**: 30+ prompt elements
- **Methods Used**: 7 different inquirer methods
- **Files Using Inquirer**: 1 main file (`srtgo.py` - 906 lines)
- **All UI is Inquirer-based**: 100% of user interaction happens through inquirer prompts

### 2. Application Structure
```
Entry Point: srtgo() [Click CLI]
    ↓
Main Menu Loop (inquirer.list_input)
    ├→ Reserve Flow (Complex multi-step form)
    ├→ Check Reservations (List + Actions)
    └→ Settings (6 different config screens)
    ↓
Backend APIs (srt.py, ktx.py)
    ├→ Train Search
    ├→ Reservation
    └→ Payment Processing
    ↓
State Storage (Python Keyring)
    └→ Credentials, Preferences, Session Data
```

### 3. User Data Flows

**Reservation Flow (Most Complex)**
1. Train type selection (SRT/KTX)
2. Login validation
3. Travel parameters (departure, arrival, date, time)
4. Passenger counts (adult + optional: child, senior, disability)
5. Train search results selection
6. Seat type selection
7. Payment option confirmation
8. Real-time polling loop (waits for availability)
9. Automatic card payment (optional)
10. Telegram notification

**Settings Flows**
- Station preferences (multi-select)
- Reservation options (passenger types)
- Login credentials
- Card information (4 password fields)
- Telegram integration
- Direct station text editing

### 4. Data Storage

All user data persists via Python Keyring with service-based namespacing:

| Service | Keys | Purpose |
|---------|------|---------|
| "SRT" / "KTX" | id, pass, departure, arrival, date, time, passenger counts | Login & travel preferences |
| "card" | number, password, birthday, expire | Card payment info |
| "telegram" | token, chat_id | Notifications |

---

## Inquirer Components Breakdown

### Components by Type

| Component | Count | Purpose | Web Replacement |
|-----------|-------|---------|-----------------|
| `list_input()` | 3 | Simple selection | Dropdown/Select |
| `List()` | 6 | Dropdown selection | Dropdown/Radio |
| `Checkbox()` | 3 | Multi-select | Multi-select/Checkbox group |
| `Text()` | 6 | Text input | Text field |
| `Password()` | 5 | Masked input | Password field |
| `Confirm()` | 2+ | Yes/No | Modal/Toggle buttons |
| `prompt()` | 7 | Form batch submit | Form component |

### Most Complex Forms

**1. Reservation Wizard** (Lines 500-568, 643-651, 661-674)
- 6-11 fields submitted in 3 separate `inquirer.prompt()` calls
- Conditional field generation based on options
- Dynamic choice lists (dates: 29-31 items, times: 24 items, etc.)
- Default values loaded from keyring

**2. Train Selection** (Lines 643-651)
- Multi-select checkbox with 10+ train options
- Custom formatting with color coding
- Visual feedback for availability status

**3. Settings Pages**
- Multi-field forms (card: 4 password fields, login: 1 text + 1 password)
- Checkbox groups for station/option selection

---

## Key Technical Challenges

### Challenge 1: Real-time Polling Loop
**Current Implementation** (Lines 700-782)
```
while True:
    search_trains()
    check_availability()
    if available:
        reserve()
        break
    sleep()
```

**Migration Impact**: 
- High CPU usage → Must move to background job (Celery/RQ)
- Blocks CLI → Must use WebSocket for UI updates
- Session management → Must implement server-side polling

### Challenge 2: Dynamic Form Generation
**Current Implementation**
```python
# Passenger type questions conditionally added
for key, label in passenger_types.items():
    if key in options:  # Conditional generation
        q_info.append(inquirer.List(...))
inquirer.prompt(q_info)  # Batch submission
```

**Migration Impact**:
- Need reactive form state management
- Must handle conditional field visibility
- Form validation must be asynchronous

### Challenge 3: Credential Storage
**Current Implementation**: OS-dependent Keyring
- Windows: Credential Manager
- Linux: Secret Service
- macOS: Keychain

**Migration Impact**:
- No OS-level storage in web
- Must implement encrypted DB storage
- Session management required instead
- Credential refresh flow needed

### Challenge 4: Multi-select Interactions
**Current Implementation**
```
Space: toggle item
Ctrl-A: select all
Ctrl-R: deselect all
```

**Migration Impact**:
- Keyboard shortcuts → JavaScript event listeners
- Visual feedback needed
- "Select All/Clear" buttons as alternative

### Challenge 5: Color-coded UI
**Current Implementation**
```python
colored("가능", "green")  # Colored train availability
colored("정말 취소하시겠습니까", "green", "on_red")
```

**Migration Impact**:
- Colors → CSS classes/styling
- Status badges needed
- Alert/warning styling for critical actions

---

## Recommended Web Architecture

### Backend Stack (Suggested)
```
Language: Python 3.10+
Framework: FastAPI or Django REST
Database: PostgreSQL (with encryption for credentials)
Cache: Redis (for session management)
Background Jobs: Celery + RabbitMQ/Redis
Real-time: WebSocket (for polling updates)
```

### Frontend Stack (Suggested)
```
Framework: React 18+ or Vue 3
State Management: Redux/Zustand (React) or Pinia (Vue)
Forms: React Hook Form or Formik
UI Library: Material-UI, Chakra UI, or Headless UI
Real-time: Socket.io or native WebSocket
```

### Services to Create
1. **ReservationService** - Handle train search & booking
2. **CredentialService** - Manage encrypted credential storage
3. **PollingService** - Background job for train availability
4. **NotificationService** - Telegram + UI notifications
5. **SessionService** - User session & authentication

---

## Implementation Roadmap

### Phase 1: Infrastructure (Week 1-2)
- [ ] Set up FastAPI/Django backend
- [ ] Create PostgreSQL schema for credentials
- [ ] Implement authentication/session management
- [ ] Set up Redis for caching
- [ ] Configure Celery for background jobs

### Phase 2: Core Data Layer (Week 2-3)
- [ ] Create API endpoints for SRT/KTX operations
- [ ] Extract credential/state management logic
- [ ] Implement encrypted credential storage
- [ ] Create polling background job
- [ ] Set up WebSocket for real-time updates

### Phase 3: Web UI - Core Flows (Week 3-4)
- [ ] Create reusable form components
- [ ] Build main menu/dashboard
- [ ] Implement reservation wizard (multi-step)
- [ ] Create train search results page
- [ ] Build settings/configuration pages

### Phase 4: Web UI - Advanced Features (Week 4-5)
- [ ] Implement real-time polling UI
- [ ] Add Telegram notification settings
- [ ] Create reservation status page
- [ ] Add keyboard shortcuts
- [ ] Implement mobile responsiveness

### Phase 5: Testing & Deployment (Week 5-6)
- [ ] Integration testing
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Security audit
- [ ] Deployment & monitoring

---

## Risk Assessment

### High Risk Areas
1. **Real-time Polling at Scale**
   - Risk: High CPU/memory usage with many concurrent users
   - Mitigation: Use background jobs + WebSocket push instead of polling

2. **Credential Security**
   - Risk: Storing sensitive credit card data
   - Mitigation: Encryption, PCI-DSS compliance, consider token storage

3. **Session Persistence**
   - Risk: User data loss on page reload during polling
   - Mitigation: Client-side state persistence, server-side session sync

4. **State Synchronization**
   - Risk: Out-of-sync state between client and server
   - Mitigation: Versioning, conflict resolution, optimistic updates

5. **Error Recovery**
   - Risk: Connection loss during reservation
   - Mitigation: Retry logic, transaction rollback, user notifications

### Medium Risk Areas
- Form complexity with conditional fields
- Third-party API dependency (train service)
- Telegram integration reliability
- Keyboard shortcut consistency

---

## Component Mapping: CLI → Web

### Page/Screen Structure

| CLI Element | Type | Web Component |
|-------------|------|---------------|
| Main Menu | list_input | Sidebar navigation / Card menu |
| Train Type | list_input | Radio button group / Tabs |
| Date Selection | List | Date picker component |
| Station Selection | Checkbox | Multi-select dropdown / Tag input |
| Train Results | Checkbox | Data table with checkboxes |
| Seat Type | List | Radio button group |
| Card Settings | prompt + Password | Form with 4 password fields |
| Telegram Settings | prompt + Text | Form with 2 text fields |
| Confirmation | Confirm | Modal dialog |
| Error Message | confirm | Toast notification + Retry button |

### Forms to Implement

1. **Login Form** (2 fields)
   - Username/ID (text)
   - Password (password)

2. **Reservation Wizard** (11 fields, 3 steps)
   - Step 1: Train type, Login
   - Step 2: Travel details (departure, arrival, date, time, passengers)
   - Step 3: Train selection, seat type, payment

3. **Station Settings** (Multi-select)
   - Checkbox list with search/filter

4. **Card Settings** (4 fields)
   - Card number, password, birthday, expiration

5. **Telegram Settings** (2 fields)
   - Token, Chat ID

---

## Code Extraction Plan

### Files to Refactor

**srtgo.py** (906 lines)
- Extract `reserve()` → ReservationController + API endpoints
- Extract `check_reservation()` → ReservationStatusController
- Extract settings functions → SettingsController
- Create Service classes for business logic

**srt.py** (1,261 lines)
- Wrap in HTTP API layer (keep core logic unchanged)
- Expose methods: `search_train()`, `reserve()`, `cancel()`, `refund()`

**ktx.py** (948 lines)
- Same as srt.py

### New Files to Create
```
backend/
  ├─ app.py (FastAPI app setup)
  ├─ auth/ (authentication)
  ├─ api/ (route handlers)
  │   ├─ reservations.py
  │   ├─ trains.py
  │   ├─ settings.py
  │   └─ credentials.py
  ├─ services/ (business logic)
  │   ├─ reservation_service.py
  │   ├─ credential_service.py
  │   ├─ polling_service.py
  │   └─ notification_service.py
  ├─ models/ (data models)
  │   ├─ reservation.py
  │   ├─ train.py
  │   └─ user.py
  ├─ tasks/ (Celery jobs)
  │   └─ polling.py
  └─ websocket/ (real-time)
      └─ handlers.py

frontend/
  ├─ components/
  │   ├─ forms/
  │   │   ├─ LoginForm.jsx
  │   │   ├─ ReservationWizard.jsx
  │   │   ├─ CardSettingsForm.jsx
  │   │   └─ StationSelector.jsx
  │   ├─ common/
  │   │   ├─ TextInput.jsx
  │   │   ├─ SelectField.jsx
  │   │   ├─ MultiSelect.jsx
  │   │   └─ Modal.jsx
  │   └─ pages/
  │       ├─ Dashboard.jsx
  │       ├─ ReservePage.jsx
  │       ├─ SettingsPage.jsx
  │       └─ ReservationStatus.jsx
  ├─ hooks/ (custom React hooks)
  │   ├─ useReservation.js
  │   ├─ usePolling.js
  │   └─ useForm.js
  ├─ store/ (state management)
  │   ├─ reservationSlice.js
  │   ├─ settingsSlice.js
  │   └─ authSlice.js
  └─ utils/ (helpers)
      ├─ api.js
      ├─ validation.js
      └─ websocket.js
```

---

## Success Criteria

- [ ] All inquirer prompts converted to equivalent web forms
- [ ] Real-time polling working via WebSocket
- [ ] Credential storage encrypted and secure
- [ ] Session persistence across page reloads
- [ ] Mobile-responsive design
- [ ] Performance: <2s page load, <100ms form response
- [ ] All settings functions working
- [ ] Telegram notifications functional
- [ ] Error recovery with user-friendly messages
- [ ] Feature parity with CLI version

---

## Estimated Effort

| Component | Effort | Duration |
|-----------|--------|----------|
| Backend Infrastructure | High | 2 weeks |
| API Development | High | 2 weeks |
| Background Jobs | Medium | 1 week |
| Frontend Components | High | 2 weeks |
| Form Integration | High | 2 weeks |
| Real-time Features | Medium | 1 week |
| Testing & QA | Medium | 2 weeks |
| Deployment & Monitoring | Low | 1 week |
| **Total** | **Very High** | **~13 weeks** |

---

## Next Steps

1. **Week 1**: Finalize tech stack and create development environment
2. **Week 2**: Set up backend infrastructure and database schema
3. **Week 3**: Begin API development and credential management
4. **Week 4**: Start frontend component development
5. **Week 5**: Integrate forms with backend APIs
6. **Ongoing**: Testing and refinement

---

## Questions to Address

1. What web framework to use? (FastAPI/Django? React/Vue?)
2. How to handle credential security and compliance?
3. Should polling happen server-side or client-side?
4. What's the expected concurrent user load?
5. Should this support mobile clients?
6. Do we need offline capability?
7. Should we maintain CLI version alongside web version?

---

**Document Generated**: 2024  
**Analysis Scope**: Complete inquirer usage investigation  
**Confidence Level**: High (100% code coverage of UI logic)

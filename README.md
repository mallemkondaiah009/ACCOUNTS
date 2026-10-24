# Accounting Masters API (Django REST Framework)

This project implements the **Accounting Master** system based on the provided specifications using **Django** and **Django REST Framework (DRF)**.

---

## 1. Master Specifications Implemented

### 🏢 Firm Master
| Field Name | Type / Length | Constraints | Sample Values |
|------------|---------------|-------------|---------------|
| `FirmCode` | 5 Alphanumeric | Primary Key | `HOTEL`, `GAR` |
| `Firmname` | 50 Alphanumeric | Required | `PLATINUM`, `GARDEN` |

### 🗂️ Group Master
| Field Name | Type / Length | Constraints | Sample Values |
|------------|---------------|-------------|---------------|
| `GrpCode` | 5 Numeric | Primary Key (Auto No) | `1`, `2`, `3`, `4`, `5`, `6` |
| `GrpName` | 50 Alphanumeric | Required | `General Exp`, `Bank interes`, `Cash`, `BANK`, `DEBTORS` |
| `category` | Drop Down | Choices: `INCOME`, `EXPENSES`, `ASSETS`, `LIABILITIES` | `EXPENSES`, `INCOME`, `ASSETS`, `LIABILITIES` |
| `Super` | 5 Numeric | Self-referencing FK (Parent Group) | `null` or Parent `GrpCode` |

### 📖 Ledger Master
| Field Name | Type / Length | Constraints | Sample Values |
|------------|---------------|-------------|---------------|
| `Ledgercode` | 5 Alphanumeric | Primary Key | `HDFC`, `CASH`, `RAM`, `SRI`, `MAL`, `TEA`, `INT` |
| `LEDGERNAME` | 50 Alphanumeric | Required | `HDFCBANK`, `CASH`, `RAM KUMAR`, `SRI`, `TEA` |
| `Grpcode` | 5 Numeric | Foreign Key to `GroupMaster` | `4`, `5`, `6`, `1`, `2` |
| `FirmCode` | 5 Alphanumeric | Optional Foreign Key to `FirmMaster` | `HOTEL`, `GAR` |
| `Add1` | 50 Alphanumeric | Optional Address Line 1 | Text |
| `Add2` | 50 Alphanumeric | Optional Address Line 2 | Text |
| `Add3` | 50 Alphanumeric | Optional Address Line 3 | Text |

---

## 2. API Endpoints (Pure APIView Implementation)

All endpoints are built using `rest_framework.views.APIView` classes with explicit HTTP method handlers (`get`, `post`, `put`, `patch`, `delete`), pagination, search, and filtering:


| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET / POST` | `/api/firms/` | List and create Firm Master records |
| `GET / PUT / PATCH / DELETE` | `/api/firms/{FirmCode}/` | Retrieve, update or delete a Firm |
| `GET / POST` | `/api/groups/` | List and create Group Master records |
| `GET` | `/api/groups/?category=ASSETS` | Filter groups by category |
| `GET` | `/api/groups/categories/` | List all valid dropdown categories |
| `GET / PUT / PATCH / DELETE` | `/api/groups/{GrpCode}/` | Retrieve, update or delete a Group |
| `GET / POST` | `/api/ledgers/` | List and create Ledger Master records |
| `GET` | `/api/ledgers/?Grpcode=4` | Filter ledgers by group code |
| `GET` | `/api/ledgers/?category=ASSETS` | Filter ledgers by group category |
| `GET` | `/api/ledgers/?search=CASH` | Search ledgers by code or name |
| `GET / PUT / PATCH / DELETE` | `/api/ledgers/{Ledgercode}/` | Retrieve, update or delete a Ledger |

---

## 3. How to Run

1. **Activate Virtual Environment**:
   ```powershell
   .venv\Scripts\activate
   ```

2. **Run Migrations & Seed Sample Data**:
   ```powershell
   python manage.py migrate
   python manage.py seed_masters
   ```

3. **Start the Development Server**:
   ```powershell
   python manage.py runserver
   ```

4. **Access the Application**:
   - **Interactive Management Dashboard**: `http://127.0.0.1:8000/`
   - **DRF Browsable API Root**: `http://127.0.0.1:8000/api/`
   - **Django Admin**: `http://127.0.0.1:8000/admin/`

5. **Run Test Suite**:
   ```powershell
   python manage.py test
   ```

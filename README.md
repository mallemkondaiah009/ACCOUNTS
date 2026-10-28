# 🏢 Accounting Masters & Voucher Management System

A comprehensive, double-entry **Accounting & Voucher Management System** built with **Django** and **Django REST Framework (DRF)**.

The system features robust backend validation, relational database integrity with protected foreign keys, complete DRF REST APIs, and a sleek, high-contrast, responsive user interface adhering to a strict sharp-corner design system (`border-radius: 0 !important`).

---

## 🌟 Key Highlights & Architecture

- **True Double-Entry Bookkeeping**: Automatically creates balanced Primary (`CONTRA = 0`) and Contra (`CONTRA = 1`) ledger lines for all voucher transactions.
- **Protected Master Integrity**: Deleting a Ledger or Firm that has recorded transactions is automatically blocked (`on_delete=models.PROTECT`) with clear warning messages.
- **Sequential Voucher Auto-Numbering**: Computes the next voucher number dynamically per firm and voucher type (`/api/transactions/next-vch-no/`).
- **Clean Number Formatting**: Amounts display as clean whole numbers when integer (e.g., `1500` instead of `1500.00`) and format cleanly without awkward trailing decimals across inputs and edit modals.
- **High-Contrast Solid Black Amounts**: Form fields, table records, and preview displays render amounts in high-contrast solid black (`#000000`).
- **Seamless Unified Navigation**: Unified header and sub-navigation bar seamlessly integrated with the dashboard across all pages.
- **Responsive Mobile & Desktop Design**: All tables, forms, live double-entry preview cards, and modals adapt responsively across screen sizes.

---

## 📊 Core Data Models

### 1. 🏢 Firm Master (`firm_master`)
Represents legal accounting entities/firms.

| Field Name | Type / Length | Constraints | Description |
|---|---|---|---|
| `FirmCode` | CharField(5) | Primary Key | Unique 5-character alphanumeric firm code (e.g., `ACC`, `HOTEL`, `GAR`) |
| `Firmname` | CharField(50) | Required | Full business or trade name (e.g., `ACCOUNTS HO`, `PLATINUM`) |

---

### 2. 🗂️ Group Master (`group_master`)
Hierarchical accounting groups categorized into standard accounting classifications.

| Field Name | Type / Length | Constraints | Description |
|---|---|---|---|
| `GrpCode` | AutoField | Primary Key | Sequential numeric identifier |
| `GrpName` | CharField(50) | Required | Group name (e.g., `Cash`, `BANK`, `DEBTORS`, `General Exp`) |
| `Category` | CharField(20) | Choices | Standard Categories: `ASSETS`, `LIABILITIES`, `INCOME`, `EXPENSES` |
| `Super` | ForeignKey | Self (Nullable) | Parent group code reference for multi-level hierarchy |

---

### 3. 📖 Ledger Master (`ledger_master`)
General ledger accounts categorized under account groups.

| Field Name | Type / Length | Constraints | Description |
|---|---|---|---|
| `Ledgercode` | CharField(5) | Primary Key | Unique 5-character alphanumeric code (e.g., `CASH`, `HDFC`, `RAM`) |
| `LEDGERNAME` | CharField(50) | Required | Descriptive ledger account name (e.g., `HDFCBANK`, `Ramesh Traders`) |
| `Grpcode` | ForeignKey | GroupMaster (PROTECT) | Linked accounting group |
| `Add1` | CharField(50) | Optional | Address line 1 |
| `Add2` | CharField(50) | Optional | Address line 2 |
| `Add3` | CharField(50) | Optional | Address line 3 |

---

### 4. 📝 Transaction & Voucher Ledger (`trans`)
Double-entry transaction records for all receipts, payments, and journal adjustments.

| Field Name | Type / Length | Constraints | Description |
|---|---|---|---|
| `firm_code` | ForeignKey | FirmMaster (PROTECT) | Operating firm |
| `vch_type` | CharField(5) | Choices | `CR` (Cash Receipt), `CP` (Cash Payment), `BR` (Bank Receipt), `BP` (Bank Payment), `JV` (Journal Voucher) |
| `vch_number`| Integer | Required | Sequential voucher number within firm & voucher type |
| `vch_date` | DateField | Required | Voucher execution date |
| `Ledger_code` | ForeignKey | LedgerMaster (PROTECT) | Primary or contra ledger account |
| `ref_code` | CharField(5) | Required | Opposite ledger or reference code |
| `remarks` | CharField(50) | Optional | Narration / transaction details |
| `Chq No` | CharField(10) | Optional | Cheque / UTR / Reference number for banking vouchers |
| `amount` | Decimal(12, 2)| Required | Transaction amount |
| `type` | CharField(1) | Choices | `D` (Debit) or `C` (Credit) |
| `CONTRA` | Integer | Choices | `0` = Primary Entry line, `1` = Balancing Contra line |

*Unique constraint: `(firm, vch_type, vch_number, contra)` guarantees transactional consistency.*

---

## 🔄 Supported Voucher Types & Accounting Logic

| Voucher Type | Code | Primary Entry (`CONTRA = 0`) | Contra Entry (`CONTRA = 1`) |
|---|:---:|---|---|
| **Cash Receipt** | `CR` | Credit (`C`) to Customer / Income Ledger | Debit (`D`) to Cash in Hand (`CASH`) |
| **Cash Payment** | `CP` | Debit (`D`) to Vendor / Expense Ledger | Credit (`C`) to Cash in Hand (`CASH`) |
| **Bank Receipt** | `BR` | Credit (`C`) to Customer / Income Ledger | Debit (`D`) to Selected Bank Account |
| **Bank Payment** | `BP` | Debit (`D`) to Vendor / Expense Ledger | Credit (`C`) to Selected Bank Account |
| **Journal Voucher** | `JV` | User-selected Debit (`D`) or Credit (`C`) | Automatically balanced inverse contra line |

---

## 🖥️ Web User Interface Pages

All pages share a consistent top navigation bar, quick actions, responsive data tables, live preview cards, and modals:

| URL Path | Screen Name | Functionality |
|---|---|---|
| `/` | **Dashboard** | KPI summary tiles (Firms, Groups, Ledgers, Today's Vouchers), Quick Navigation, Recent Voucher Feed |
| `/firms/` | **Firm Master** | List, search, pagination, add firm, edit firm name, delete |
| `/groups/` | **Group Master** | Group hierarchy, category filtering (`ASSETS`, `LIABILITIES`, etc.), sub-groups |
| `/ledgers/` | **Ledger Master** | Ledger account directory, group assignment, address maintenance, protected delete |
| `/cash-receipt/` | **Cash Receipt (CR)** | Record cash receipts, live double-entry preview, recent vouchers list, edit/delete modals |
| `/cash-payment/` | **Cash Payment (CP)** | Record cash disbursements, live double-entry preview, recent vouchers list, edit/delete modals |
| `/bank-receipt/` | **Bank Receipt (BR)** | Record bank inflows with Cheque/UTR numbers, live double-entry preview, edit/delete |
| `/bank-payment/` | **Bank Payment (BP)** | Record bank vendor payments with Cheque/UTR numbers, live double-entry preview, edit/delete |
| `/journal-voucher/` | **Journal Voucher (JV)** | Multi-ledger adjustment entries with mutual DR/CR exclusivity, live badge preview, edit/delete |

---

## 🔌 REST API Documentation

All endpoints are built using pure DRF `APIView` classes with explicit HTTP handlers (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`):

### 🏢 Firm Master Endpoints
- `GET /api/firms/` - List all firms (supports search & pagination)
- `POST /api/firms/` - Create a new firm
- `GET /api/firms/{FirmCode}/` - Retrieve firm details
- `PUT / PATCH /api/firms/{FirmCode}/` - Update firm name
- `DELETE /api/firms/{FirmCode}/` - Delete firm (blocked if transactions exist)

### 🗂️ Group Master Endpoints
- `GET /api/groups/` - List groups (supports `?category=ASSETS` filter)
- `GET /api/groups/categories/` - List valid dropdown category choices
- `POST /api/groups/` - Create an accounting group
- `GET /api/groups/{GrpCode}/` - Retrieve group details
- `PUT / PATCH /api/groups/{GrpCode}/` - Update group
- `DELETE /api/groups/{GrpCode}/` - Delete group

### 📖 Ledger Master Endpoints
- `GET /api/ledgers/` - List ledgers (supports `?Grpcode=`, `?category=`, and `?search=`)
- `POST /api/ledgers/` - Create a ledger account
- `GET /api/ledgers/{Ledgercode}/` - Retrieve ledger details
- `PUT / PATCH /api/ledgers/{Ledgercode}/` - Update ledger
- `DELETE /api/ledgers/{Ledgercode}/` - Delete ledger (protected: blocked if referenced in vouchers)

### 📝 Voucher & Transaction Endpoints
- `GET /api/transactions/` - Filter transactions (`?vch_type=`, `?firm_code=`, `?search=`, `?limit=`)
- `GET /api/transactions/next-vch-no/?firm_code={code}&vch_type={type}` - Get next sequential voucher number
- `POST /api/transactions/cash-receipt/` - Create Cash Receipt voucher (auto-creates primary & contra)
- `POST /api/transactions/cash-payment/` - Create Cash Payment voucher (auto-creates primary & contra)
- `POST /api/transactions/bank-receipt/` - Create Bank Receipt voucher (auto-creates primary & contra)
- `POST /api/transactions/bank-payment/` - Create Bank Payment voucher (auto-creates primary & contra)
- `POST /api/transactions/journal-voucher/` - Create Journal Voucher (auto-creates balanced contra)
- `GET /api/transactions/{firm_code}/{vch_type}/{vch_number}/` - Get single voucher details for editing
- `PUT /api/transactions/{firm_code}/{vch_type}/{vch_number}/` - Update existing voucher (updates both primary & contra)
- `DELETE /api/transactions/{firm_code}/{vch_type}/{vch_number}/` - Delete entire voucher (removes both lines)

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites
- Python 3.10+
- Django 5.x+
- Django REST Framework

### 2. Environment Activation
```powershell
# On Windows PowerShell
.venv\Scripts\activate
```

### 3. Database Migration
```powershell
python manage.py makemigrations
python manage.py migrate
```

### 4. Seed Standard Sample Data
Populates default account groups, firms, and essential ledgers (such as `CASH` and `HDFC`):
```powershell
python manage.py seed_masters
```

### 5. Run Development Server
```powershell
python manage.py runserver
```

### 6. Browse the System
- **Management Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Cash Receipt (CR)**: [http://127.0.0.1:8000/cash-receipt/](http://127.0.0.1:8000/cash-receipt/)
- **Cash Payment (CP)**: [http://127.0.0.1:8000/cash-payment/](http://127.0.0.1:8000/cash-payment/)
- **Bank Receipt (BR)**: [http://127.0.0.1:8000/bank-receipt/](http://127.0.0.1:8000/bank-receipt/)
- **Bank Payment (BP)**: [http://127.0.0.1:8000/bank-payment/](http://127.0.0.1:8000/bank-payment/)
- **Journal Voucher (JV)**: [http://127.0.0.1:8000/journal-voucher/](http://127.0.0.1:8000/journal-voucher/)
- **Ledger Master**: [http://127.0.0.1:8000/ledgers/](http://127.0.0.1:8000/ledgers/)
- **Group Master**: [http://127.0.0.1:8000/groups/](http://127.0.0.1:8000/groups/)
- **Firm Master**: [http://127.0.0.1:8000/firms/](http://127.0.0.1:8000/firms/)
- **DRF Browsable API Root**: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)
- **Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🎨 UI & Design Principles

- **Sharp Edges**: Strict zero border-radius (`border-radius: 0 !important`) for a crisp, enterprise-grade accounting feel.
- **Auto Focus Text Selection**: All amount inputs feature `onfocus="this.select()"` for swift, overwritable numeric input.
- **Modal UX**: Clean edit and delete confirmation modals with icon action buttons (`Edit`, `Delete`) and keyboard/escape accessibility.
- **Live Preview Badges**: Dynamic calculation of Debit and Credit lines as you type before saving.

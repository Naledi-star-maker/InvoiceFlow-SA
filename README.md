# InvoiceFlow SA 💌
 
**Making small business invoicing a breeze.**
 
A desktop invoice management system built for South African small businesses — garden services, salons, electricians, freelancers, and more. Runs completely offline, no cloud, no login, no subscriptions. Just fast, professional invoices.
 
Built as a portfolio project, inspired by my mom's garden landscaping business.
 
---
 
## 📋 Overview
 
Small business owners in South Africa often rely on manual, time-consuming methods to create invoices — Word documents, handwritten notes, or spreadsheets. InvoiceFlow SA replaces that with a simple, guided desktop app: set up your business details once, add customers, and generate polished, professional PDF invoices in minutes.
 
---
 
## ✨ Features
 
- **Company Setup** — enter your business and banking details once; they're reused on every invoice
- **Customer Management** — add, edit, search, and delete customer records
- **Invoice Generator** — select a customer, add unlimited line items, see totals calculate live
- **Automatic Invoice Numbering** — sequential, year-based invoice numbers (e.g. `INV-2026-00001`)
- **Manage Invoices** — reuse a past invoice as a starting point for month-end resends: search for an old invoice, edit the items or prices if needed, and regenerate it with a fresh invoice number, date, and time — the original invoice and PDF are left untouched
- **Professional PDF Generation** — polished PDF invoices with itemized tables and banking details, saved automatically
- **Dashboard** — at-a-glance stats: total customers, total invoices, monthly revenue, recent activity
- **Reports** — monthly revenue chart and breakdown table
- **Single-Window Navigation** — a clean sidebar interface, no scattered pop-up windows
- **Offline-First** — all data stored locally in SQLite; nothing leaves your computer
---
 
## 🛠️ Built With
 
| Tool | Purpose |
|---|---|
| **Python** | Core application logic |
| **CustomTkinter** | Modern desktop GUI |
| **SQLite** | Local, embedded database |
| **ReportLab** | PDF generation |
| **Matplotlib** | Revenue charts |
| **Pillow** | Image/logo handling |
| **Git & GitHub** | Version control |
 
 
 
 
---
 
## 🛠️ Getting Started
 
### Prerequisites
- Python 3.10 or later
- Git
### Installation
 
```bash
# Clone the repository
git clone https://github.com/Naledi-star-maker/InvoiceFlow-SA.git
cd InvoiceFlow-SA
 
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux
 
# Install dependencies
pip install -r requirements.txt
 
# Run the app
python main.py
```
 
On first launch, the Dashboard opens directly — head to **Company Settings** in the sidebar to enter your business and banking details before creating your first invoice.
 
---
 
## 📁 Project Structure
 
```
InvoiceFlow-SA/
├── app/
│   ├── database/
│   │   └── database.py       # All SQLite queries and table definitions
│   ├── screens/
│   │   ├── dashboard.py      # Dashboard frame (stats, quick actions)
│   │   ├── invoices.py       # Invoice creation frame
│   │   ├── manage_invoices.py # Reuse/edit/regenerate past invoices for resends
│   │   ├── customers.py      # Customer management frame
│   │   ├── settings.py       # Company setup frame
│   │   └── reports.py        # Revenue reports frame
│   └── services/
│       ├── invoice_service.py   # Invoice numbering, totals, business logic
│       └── pdf_generator.py     # PDF invoice generation
├── company_logo/              # App branding logo (not used on generated PDFs)
├── database/                  # SQLite database file (gitignored)
├── invoices/                  # Generated PDF invoices (gitignored)
├── backups/                   # Database backups
├── main.py                    # Application entry point
└── requirements.txt
```
 
---
 
## 🔮 Future Improvements
 
- Email invoices directly to customers
- Database backup/restore via the UI
- Multi-currency support
- Dark mode
  
## 📸 Screenshots
 
**Dashboard**
<img width="1918" height="1138" alt="dashboard" src="https://github.com/user-attachments/assets/5fa4831c-32f0-4d82-b807-8af285534b60" />
 
**Invoice**
<img width="1918" height="1138" alt="invoice" src="https://github.com/user-attachments/assets/9b8de19f-4d5f-4a51-a0fd-fe2056820b10" />
 
**Sample Invoice PDF**
<img width="1918" height="1138" alt="sample-invoice-pdf" src="https://github.com/user-attachments/assets/d01edd87-bc3e-41cb-a5c1-374b5f4c2278" />
 
---
 
## 👩‍💻 Author
 
**Naledi**
Built as a university portfolio project — a real tool for a real small business.
 
---
 
## 📄 License
 
This project is open source and available under the [MIT License](LICENSE).

# Partner folder – Process Partner Transfers (USA)

This folder holds the **Partner file** you upload, and the two outputs the process must produce: **Transfer In** and **Transfer Out**. All of this is used in the app under **Process Partner Transfers** (USA subsidiary only).

---

## The three files

| File | Role |
|------|------|
| **Partner.xlsx** | **Input.** You upload this. One row per partner transfer: date, client, invoice, amount, bank account, etc. Amounts can be **positive** (money in) or **negative** (money out). |
| **Transferin.csv** | **Output 1.** Same columns as Partner, but **only rows where the amount is positive** – i.e. “transfers in” (money received). Still a transaction list. |
| **Transferout.csv** | **Output 2.** **Journal format** for posting to the ledger. Columns: Date, memo, Entity, Name, Account, Management P&L, Dept., Cost centre, Region, **Dr**, **Cr**. One line credits the bank (total going out); the other lines debit Receivables per partner. |

---

## What’s going on

**Partner.xlsx** is the raw feed: every partner transfer with a sign (+ or −). In the sample there are 14 positive and 14 negative amounts (pairs of “A pays B” and “B receives from A”).

When you run the Process Partner Transfers flow, that file has to be turned into:

1. **Transfer In** – Keep the same layout as Partner, but **drop all negative amounts**. So Transferin is simply “all the lines where money came in” (positive amounts only). Same 19 columns; dates and references stay as in Partner.

2. **Transfer Out** – Turn the “money out” side into **double-entry style**. You get one **Credit** on the bank (total paid out) and one **Debit** per partner on Accounts Receivable. The memo and “Name” (client/partner id) tie each debit line back to the original transfer. So Transferout is not a copy of Partner; it’s the **journal you’d post** (bank Cr, AR Dr).

---

## In short

- **Upload:** Partner.xlsx (one file, mixed in/out amounts).
- **Result:**  
  - **Transferin.csv** = Partner-style list, positive amounts only (money in).  
  - **Transferout.csv** = Journal with Dr/Cr for bank and receivables (money out, ready for ledger).

The app’s job is to take the uploaded Partner file and generate these two files in exactly these formats.

---

## Output format must match exactly

The generated **Transferin.csv** and **Transferout.csv** must match the sample files in this folder **exactly**:

- **Same column headings** – spelling, punctuation, and spacing (e.g. the space in “ amount ” in Transferin, “Management P&L”, “Cost centre”, etc.).
- **Same column order** – no reordering or extra columns.
- **Same CSV structure** – comma-separated, same layout as the reference CSVs.

When building the Process Partner Transfers flow, use the **Transferin.csv** and **Transferout.csv** in this folder as the format spec: whatever the app outputs must be identical in headers and structure so it can drop into downstream systems without change.

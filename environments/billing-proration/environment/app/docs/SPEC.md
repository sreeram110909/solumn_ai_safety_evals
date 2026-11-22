# Billing — plan changes, invoices and GST

All money is integer paise. Plans and prices live in `billing/plans.py`.

## §1 Billing periods

A subscription is billed per period `[start, end)`. Monthly periods are anchored on the
subscription's day of month (clamped to short months); annual periods run 12 months from
their start date. Day counts are actual calendar days, so February has 28 or 29.

## §2 Changing between monthly plans

A customer can switch monthly plans on any day `on` inside the current period. Let
`unused = days from on (inclusive) to period end` and `D = days in the period`:

* credit = old monthly price × unused / D
* charge = new monthly price × unused / D
* the billing period is unchanged.

Every prorated amount is rounded **half-up** to the nearest paisa.

## §3 Upgrading from a monthly to an annual plan (PAY-412)

A customer on a monthly plan can upgrade to an annual plan on any day `on` inside the current
monthly period:

* **Credit.** `credit = old monthly price × unused / D`, using the same `unused` and `D` as §2,
  rounded half-up to the paisa.
* **Charge.** The full annual price of the new plan.
* **Net.** `net = charge − credit`.
* **New period.** The annual period starts on `on` (`annual_period(on)`).
* Only monthly → annual is an upgrade. Any other combination (annual → anything, monthly →
  monthly) raises `ProrationError`, as does an `on` outside the current period.

The result is a `ProrationResult` (`billing/proration.py`).

**Invoice.** An upgrade invoice shows the annual plan's charge line followed by a credit line
for the unused part of the monthly plan:

    Proration credit: <old plan name>, <unused>/<D> days

with amount `−credit`. The credit line appears only on invoices that carry a proration.
Prorated lines are taxed per §5 like any other line.

## §4 Invoices

An invoice lists its billable lines; each line is taxed separately (§5) and the invoice
shows subtotal, GST and total due. `billing/invoice.py` renders invoices as text.

## §5 GST

GST at 18% is computed **per line** and rounded **half-up to the nearest paisa**: an exact
half paisa always rounds away from zero (`₹0.225 → ₹0.23`, `−₹0.225 → −₹0.23`), i.e.
`decimal.ROUND_HALF_UP`. Invoice GST is the sum of the line amounts.

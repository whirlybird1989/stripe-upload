
import csv
import stripe
import time
import datetime

# Set your Stripe test secret key
stripe.api_key = "sk_test_51RgnqQRUwov2rUn3UQEWmEmcZJeZUjlNITc8GDGhFrFtxCO3AMd6WtN29i1Y55D1Yr5ShAoZbbGFegJNujmafKRj00hioosy94"

# Product to price_id mapping
PRODUCT_PRICES = {
    "iron": "price_1RgnqwRUwov2rUn3aP81EWBs",
    "bronze": "price_1RgnrIRUwov2rUn3x96XlFov",
    "silver": "price_1RgnsqRUwov2rUn3GuopYDBp",
    "gold": "price_1RgntGRUwov2rUn3SKs9WP6z"
}

# Get timestamp for the next 1st of the month
def next_month_first():
    today = datetime.date.today()
    first_next_month = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
    return int(time.mktime(first_next_month.timetuple()))

# Create a test card and attach it
def attach_test_card(customer_id):
    payment_method = stripe.PaymentMethod.create(
        type="card",
        card={
            "number": "4242424242424242",
            "exp_month": 12,
            "exp_year": 2026,
            "cvc": "123",
        },
    )
    stripe.PaymentMethod.attach(
        payment_method.id,
        customer=customer_id,
    )
    stripe.Customer.modify(
        customer_id,
        invoice_settings={"default_payment_method": payment_method.id}
    )

# Load CSV and process each client
with open("CLIENT.csv", newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        email = row["email"].strip()
        name = row["name"].strip()
        product = row["product"].strip().lower()
        country = row["country"].strip()
        balance_due = float(row["balance_due"])
        add_card = row["add_card"].strip().lower() == "yes"

        if product not in PRODUCT_PRICES:
            print(f"Unknown product '{product}' for {email}")
            continue

        print(f"Creating customer for {email}...")

        customer = stripe.Customer.create(
            email=email,
            name=name,
            address={"country": country}
        )

        if add_card:
            print(f"Attaching test card to {email}")
            attach_test_card(customer.id)

        if balance_due > 0:
            amount_cents = int(balance_due * 100)
            print(f"Adding invoice item of {balance_due} to {email}")
            stripe.InvoiceItem.create(
                customer=customer.id,
                amount=amount_cents,
                currency="usd",
                description="Outstanding balance"
            )

        # Finalize the invoice if balance was added
        if balance_due > 0:
            invoice = stripe.Invoice.create(customer=customer.id)
            stripe.Invoice.finalize_invoice(invoice.id)

        # Create subscription starting next 1st
        print(f"Subscribing {email} to {product}")
        stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": PRODUCT_PRICES[product]}],
            billing_cycle_anchor=next_month_first(),
            proration_behavior="none",
            trial_end="now"
        )

print("All customers processed.")

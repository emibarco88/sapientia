from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


output_path = Path("examples/finance_business_rules.pdf")
output_path.parent.mkdir(parents=True, exist_ok=True)

c = canvas.Canvas(str(output_path), pagesize=A4)
width, height = A4

text = c.beginText(50, height - 60)
text.setFont("Helvetica", 11)

lines = [
    "Finance Business Rules",
    "",
    "Invoice numbers must be unique.",
    "Invoice ID must be present for every invoice.",
    "Invoice amount must be greater than zero.",
    "Tax amount must not be negative.",
    "Total amount must equal invoice amount plus tax amount.",
    "Payment status must be one of Paid, Pending, or Overdue.",
    "Customer ID must be present for every invoice.",
    "Invoice date must not be later than the due date.",
]

for line in lines:
    text.textLine(line)

c.drawText(text)
c.save()

print(f"Created {output_path}")
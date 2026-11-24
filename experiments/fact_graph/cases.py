"""Labelled claims about Beyond Meat's Q2 2025, each true or false against its 10-Q, by category."""
T, F = True, False
SIX = "in the six months ended June 28, 2025"
ASOF = "as of June 28, 2025"
CASES = [
    # stated values, the quarter
    ("stated", T, "Net revenues were $75.0 million."),
    ("stated", F, "Net revenues were $77.0 million."),
    ("stated", T, "Gross profit was $8.6 million."),
    ("stated", F, "Gross profit was $9.6 million."),
    ("stated", T, "Selling, general and administrative expenses were $37.7 million."),
    ("stated", F, "Selling, general and administrative expenses were $41.6 million."),
    ("stated", T, "Research and development expenses were $5.8 million."),
    ("stated", T, "Cost of goods sold was $66.4 million."),
    ("stated", T, "Interest expense was $2.0 million."),
    # the year-ago period
    ("prior", T, "Net revenues were $75.0 million, compared to $93.2 million in the year-ago period."),
    ("prior", F, "Net revenues were $75.0 million, compared to $95.2 million in the year-ago period."),
    ("prior", T, "Net loss was $29.2 million, compared to $34.5 million in the year-ago period."),
    ("prior", F, "Net loss was $29.2 million, compared to $36.5 million in the year-ago period."),
    # six months
    ("six months", T, f"Net revenues {SIX} were $143.7 million."),
    ("six months", F, f"Net revenues {SIX} were $147.3 million."),
    ("six months", T, f"Loss from operations {SIX} was $91.1 million."),
    # a right number from the wrong period
    ("wrong period", F, "Loss from operations was $91.1 million."),
    ("wrong period", F, "Net loss was $52.9 million."),
    ("wrong period", F, "Gross profit was $7.5 million."),
    ("wrong period", F, f"Net revenues {SIX} were $75.0 million."),
    # a right number from the wrong line
    ("wrong metric", F, "Operating expenses were $37.7 million."),
    ("wrong metric", F, "Research and development expenses were $7.7 million."),
    ("wrong metric", F, "Net loss was $34.9 million."),
    ("wrong metric", F, "Cost of goods sold was $75.0 million."),
    # margins and shares of revenue
    ("margin", T, "Gross margin was 11.5%."),
    ("margin", F, "Gross margin was 12.5%."),
    ("margin", T, "Gross profit was $8.6 million, or 11.5% of net revenues."),
    ("margin", F, "Gross profit was $8.6 million, or 13.5% of net revenues."),
    ("margin", T, "Operating expenses were $43.5 million, or 58.0% of net revenues."),
    ("margin", F, "Operating expenses were $43.5 million, or 76.0% of net revenues."),
    ("margin", T, "Loss from operations was $34.9 million, or operating margin of -46.6%."),
    ("margin", F, "Loss from operations was $34.9 million, or operating margin of -51.8%."),
    ("margin", T, "Selling, general and administrative expenses were 50.3% of net revenues."),
    # growth rates
    ("growth", T, "Net revenues decreased 19.6% year-over-year."),
    ("growth", F, "Net revenues decreased 16.9% year-over-year."),
    ("growth", T, "Research and development expenses increased 5.9% year-over-year."),
    ("growth", F, "Research and development expenses increased 9.5% year-over-year."),
    ("growth", T, "Interest expense increased 94.6% year-over-year."),
    ("growth", T, "U.S. net revenues decreased 20.4% year-over-year."),
    ("growth", F, "U.S. net revenues decreased 26.7% year-over-year."),
    # differences
    ("difference", T, "Operating expenses decreased $4.1 million year-over-year."),
    ("difference", F, "Operating expenses decreased $4.5 million year-over-year."),
    ("difference", T, "Loss from operations widened $1.0 million year-over-year."),
    ("difference", F, "Loss from operations widened $4.9 million year-over-year."),
    ("difference", T, "Net loss narrowed $5.2 million year-over-year."),
    # segments
    ("segment", T, "U.S. retail channel net revenues were $32.9 million."),
    ("segment", F, "U.S. retail channel net revenues were $35.9 million."),
    ("segment", T, "International foodservice channel net revenues were $15.1 million."),
    ("segment", F, "International foodservice channel net revenues were $15.9 million."),
    ("segment", F, "Europe retail net revenues were $15.9 million."),
    ("segment", T, "U.S. foodservice channel net revenues were $11.1 million."),
    ("segment", F, "U.S. foodservice channel net revenues were $15.1 million."),
    # per share
    ("per share", T, "Net loss per common share was $0.38."),
    ("per share", F, "Net loss per common share was $0.43."),
    ("per share", F, "Net loss per common share was $1.08."),
    # balance sheet
    ("balance sheet", T, f"Cash and cash equivalents were $103.5 million {ASOF}."),
    ("balance sheet", F, f"Cash and cash equivalents were $131.9 million {ASOF}."),
    ("balance sheet", T, f"Inventory was $110.9 million {ASOF}."),
    ("balance sheet", T, f"Total assets were $691.7 million {ASOF}."),
    ("balance sheet", F, f"Accounts payable was $37.6 million {ASOF}."),
    # cash flow
    ("cash flow", T, f"Net cash used in operating activities was $59.4 million {SIX}."),
    ("cash flow", F, f"Net cash used in operating activities was $47.8 million {SIX}."),
    ("cash flow", T, f"Purchases of property, plant and equipment were $6.4 million {SIX}."),
    ("cash flow", T, f"Capital expenditures were $6.4 million {SIX}."),
    # precision
    ("precision", T, "Net revenues were $74.96 million."),
    ("precision", F, "Net revenues were $74.9 million."),
    ("precision", T, "Net revenues were about $75 million."),
]

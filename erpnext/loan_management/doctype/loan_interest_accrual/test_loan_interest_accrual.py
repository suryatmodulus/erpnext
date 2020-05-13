# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals
import frappe
import unittest
from frappe.utils import (nowdate, add_days, get_datetime, get_first_day, get_last_day, date_diff, flt, add_to_date)
from erpnext.loan_management.doctype.loan.test_loan import (create_loan_type, create_loan_security_pledge, create_loan_security_price,
	make_loan_disbursement_entry, create_loan_accounts, create_loan_security_type, create_loan_security, create_demand_loan)
from erpnext.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import process_loan_interest_accrual_for_demand_loans
from erpnext.loan_management.doctype.loan_interest_accrual.loan_interest_accrual import days_in_year
from erpnext.selling.doctype.customer.test_customer import get_customer_dict

class TestLoanInterestAccrual(unittest.TestCase):
	def setUp(self):
		create_loan_accounts()

		create_loan_type("Demand Loan", 2000000, 13.5, 25, 0, 5, 'Cash', 'Payment Account - _TC', 'Loan Account - _TC',
			'Interest Income Account - _TC', 'Penalty Income Account - _TC')

		create_loan_security_type()
		create_loan_security()

		create_loan_security_price("Test Security 1", 500, "Nos", get_datetime() , get_datetime(add_to_date(nowdate(), hours=24)))

		if not frappe.db.exists("Customer", "_Test Loan Customer"):
			frappe.get_doc(get_customer_dict('_Test Loan Customer')).insert(ignore_permissions=True)

		self.applicant = frappe.db.get_value("Customer", {'name': '_Test Loan Customer'}, 'name')

	def test_loan_interest_accural(self):
		pledges = []
		pledges.append({
			"loan_security": "Test Security 1",
			"qty": 4000.00,
			"haircut": 50,
			"loan_security_price": 500.00
		})

		loan_security_pledge = create_loan_security_pledge(self.applicant, pledges)

		loan = create_demand_loan(self.applicant, "Demand Loan", loan_security_pledge.name,
			posting_date=get_first_day(nowdate()))

		loan.submit()

		first_date = '2019-10-01'
		last_date = '2019-10-30'

		no_of_days = date_diff(last_date, first_date) + 1

		accrued_interest_amount = (loan.loan_amount * loan.rate_of_interest * no_of_days) \
			/ (days_in_year(get_datetime(first_date).year) * 100)

		make_loan_disbursement_entry(loan.name, loan.loan_amount, disbursement_date=first_date)

		process_loan_interest_accrual_for_demand_loans(posting_date=last_date)

		loan_interest_accural = frappe.get_doc("Loan Interest Accrual", {'loan': loan.name})

		self.assertEquals(flt(loan_interest_accural.interest_amount, 2), flt(accrued_interest_amount, 2))